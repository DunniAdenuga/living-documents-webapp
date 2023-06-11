""" run decoding of rnn-ext + abs + RL (+ rerank)"""
# https://github.com/ChenRocks/fast_abs_rl

import argparse
import json
import os
import re
import torch
import unittest
import nltk
import string
import logging
import datetime

from typing import List
from os.path import join
from datetime import timedelta
from time import time
from collections import Counter, defaultdict
from itertools import product
from functools import reduce
import operator as op
import pickle as pkl
from itertools import starmap
from cytoolz import identity, concat, curry
from torch.utils.data import DataLoader, Dataset
from torch import multiprocessing as mp
from .fast_abs_rl.data.batcher import tokenize
from .fast_abs_rl.model.copy_summ import CopySumm
from .fast_abs_rl.model.extract import PtrExtractSumm
from .fast_abs_rl.model.rl import ActorCritic
from .fast_abs_rl.data.batcher import conver2id, pad_batch_tensorize
from text_generation.models.sentence import Sentence
from living_documents_server import settings

logger = logging.getLogger(__name__)

# constant value used for pre-processing word to index
PAD = settings.FAST_ABS_RL_SUMMARIZER_PAD
UNK = settings.FAST_ABS_RL_SUMMARIZER_UNK
START = settings.FAST_ABS_RL_SUMMARIZER_START
END = settings.FAST_ABS_RL_SUMMARIZER_END

def load_best_ckpt(model_dir, reverse=False):
    """ reverse=False->loss, reverse=True->reward/score"""
    ckpts = os.listdir(join(model_dir, 'ckpt'))
    ckpt_matcher = re.compile('^ckpt-.*-[0-9]*')
    ckpts = sorted([c for c in ckpts if ckpt_matcher.match(c)],
                   key=lambda c: float(c.split('-')[1]), reverse=reverse)
    # print('loading summarizer model checkpoint {}...'.format(ckpts[0]))
    ckpt = torch.load(
        join(model_dir, 'ckpt/{}'.format(ckpts[0])), map_location='cpu'
    )['state_dict']
    return ckpt

class Abstractor(object):
    def __init__(self, abs_dir, max_len=30, cuda=True):
        abs_meta = json.load(open(join(abs_dir, 'meta.json')))
        assert abs_meta['net'] == 'base_abstractor'
        abs_args = abs_meta['net_args']
        abs_ckpt = load_best_ckpt(abs_dir)
        word2id = pkl.load(open(join(abs_dir, 'vocab.pkl'), 'rb'))
        abstractor = CopySumm(**abs_args)
        abstractor.load_state_dict(abs_ckpt)
        self._device = torch.device('cuda' if cuda else 'cpu')
        self._net = abstractor.to(self._device)
        self._word2id = word2id
        self._id2word = {i: w for w, i in word2id.items()}
        self._max_len = max_len

    def _prepro(self, raw_article_sents):
        ext_word2id = dict(self._word2id)
        ext_id2word = dict(self._id2word)
        for raw_words in raw_article_sents:
            for w in raw_words:
                if not w in ext_word2id:
                    ext_word2id[w] = len(ext_word2id)
                    ext_id2word[len(ext_id2word)] = w
        articles = conver2id(UNK, self._word2id, raw_article_sents)
        art_lens = [len(art) for art in articles]
        article = pad_batch_tensorize(articles, PAD, cuda=False
                                     ).to(self._device)
        extend_arts = conver2id(UNK, ext_word2id, raw_article_sents)
        extend_art = pad_batch_tensorize(extend_arts, PAD, cuda=False
                                        ).to(self._device)
        extend_vsize = len(ext_word2id)
        dec_args = (article, art_lens, extend_art, extend_vsize,
                    START, END, UNK, self._max_len)
        return dec_args, ext_id2word

    def __call__(self, raw_article_sents):
        self._net.eval()
        dec_args, id2word = self._prepro(raw_article_sents)
        decs, attns = self._net.batch_decode(*dec_args)
        def argmax(arr, keys):
            return arr[max(range(len(arr)), key=lambda i: keys[i].item())]
        dec_sents = []
        for i, raw_words in enumerate(raw_article_sents):
            dec = []
            for id_, attn in zip(decs, attns):
                if id_[i] == END:
                    break
                elif id_[i] == UNK:
                    dec.append(argmax(raw_words, attn[i]))
                else:
                    dec.append(id2word[id_[i].item()])
            dec_sents.append(dec)
        return dec_sents

class ArticleBatcher(object):
    def __init__(self, word2id, cuda=True):
        self._device = torch.device('cuda' if cuda else 'cpu')
        self._word2id = word2id
        self._device = torch.device('cuda' if cuda else 'cpu')

    def __call__(self, raw_article_sents):
        articles = conver2id(UNK, self._word2id, raw_article_sents)
        article = pad_batch_tensorize(articles, PAD, cuda=False
                                     ).to(self._device)
        return article

class RLExtractor(object):
    def __init__(self, ext_dir, cuda=True):
        ext_meta = json.load(open(join(ext_dir, 'meta.json')))
        assert ext_meta['net'] == 'rnn-ext_abs_rl'
        ext_args = ext_meta['net_args']['extractor']['net_args']
        word2id = pkl.load(open(join(ext_dir, 'agent_vocab.pkl'), 'rb'))
        extractor = PtrExtractSumm(**ext_args)
        agent = ActorCritic(extractor._sent_enc,
                            extractor._art_enc,
                            extractor._extractor,
                            ArticleBatcher(word2id, cuda))
        ext_ckpt = load_best_ckpt(ext_dir, reverse=True)
        agent.load_state_dict(ext_ckpt)
        self._device = torch.device('cuda' if cuda else 'cpu')
        self._net = agent.to(self._device)
        self._word2id = word2id
        self._id2word = {i: w for w, i in word2id.items()}

    def __call__(self, raw_article_sents):
        self._net.eval()
        indices = self._net(raw_article_sents)
        return indices

class DecodeDataset(Dataset):
    """ get the article sentences only (for decoding use)"""
    def __init__(self, document_list):
        self.document_list = document_list

    def __len__(self) -> int:
        return len(self.document_list)

    def __getitem__(self, i: int):
        return self.document_list[i]

class BeamAbstractor(Abstractor):
    def __call__(self, raw_article_sents, beam_size=5, diverse=1.0):
        self._net.eval()
        dec_args, id2word = self._prepro(raw_article_sents)
        dec_args = (*dec_args, beam_size, diverse)
        all_beams = self._net.batched_beamsearch(*dec_args)
        all_beams = list(starmap(_process_beam(id2word),
                                 zip(all_beams, raw_article_sents)))
        return all_beams

@curry
def _process_beam(id2word, beam, art_sent):
    def process_hyp(hyp):
        seq = []
        for i, attn in zip(hyp.sequence[1:], hyp.attns[:-1]):
            if i == UNK:
                copy_word = art_sent[max(range(len(art_sent)),
                                         key=lambda j: attn[j].item())]
                seq.append(copy_word)
            else:
                seq.append(id2word[i])
        hyp.sequence = seq
        del hyp.hists
        del hyp.attns
        return hyp
    return list(map(process_hyp, beam))

def decode(input_doc, model_dir, batch_size,
           beam_size, diverse, max_len, cuda):
    start = time()
    # setup model
    logger.warning('{}: Got to decode'.format(datetime.datetime.now()))
    with open(join(model_dir, 'meta.json')) as f:
        meta = json.loads(f.read())
    if meta['net_args']['abstractor'] is None:
        # NOTE: if no abstractor is provided then
        #       the whole model would be extractive summarization
        assert beam_size == 1
        abstractor = identity
    else:
        if beam_size == 1:
            abstractor = Abstractor(join(model_dir, 'abstractor'),
                                    max_len, cuda)
        else:
            abstractor = BeamAbstractor(join(model_dir, 'abstractor'),
                                        max_len, cuda)
    extractor = RLExtractor(model_dir, cuda=cuda)

    # setup loader
    def coll(batch):
        articles = list(filter(bool, batch))
        return articles
    dataset = DecodeDataset(input_doc)
    n_data = len(dataset)
    loader = DataLoader(
        dataset, batch_size=batch_size, shuffle=False, num_workers=4,
        collate_fn=coll
    )

    # Decoding
    i = 0
    output_summ = []
    with torch.no_grad():
        for i_debug, raw_article_batch in enumerate(loader):
            # print(i_debug)
            tokenized_article_batch = map(tokenize(None), raw_article_batch)
            ext_arts = []
            ext_inds = []
            for raw_art_sents in tokenized_article_batch:
                ext = extractor(raw_art_sents)[:-1]  # exclude EOE
                if not ext:
                    # use top-5 if nothing is extracted
                    # in some rare cases rnn-ext does not extract at all
                    ext = list(range(5))[:len(raw_art_sents)]
                else:
                    ext = [i.item() for i in ext]
                ext_inds += [(len(ext_arts), len(ext))]
                ext_arts += [raw_art_sents[i] for i in ext]
            if beam_size > 1:
                all_beams = abstractor(ext_arts, beam_size, diverse)
                dec_outs = rerank_mp(all_beams, ext_inds)
            else:
                dec_outs = abstractor(ext_arts)
            # print(dec_outs)
            assert i == batch_size*i_debug
            for j, n in ext_inds:
                decoded_sents = [' '.join(dec) for dec in dec_outs[j:j+n]]
                # with open(join(save_path, 'output/{}.dec'.format(i)),
                #           'w') as f:
                #     f.write(make_html_safe('\n'.join(decoded_sents)))
                # output_summ.append('\n'.join(decoded_sents))
                output_summ.append(decoded_sents)
                i += 1
                # print('{}/{} ({:.2f}%) decoded in {} seconds\r'
                # .format(i, n_data, i/n_data*100,timedelta(seconds=int(time()-start))))
    logger.warning('{} this is outputSumm\r'.format(output_summ))
    return output_summ


_PRUNE = defaultdict(
    lambda: 2,
    {1:5, 2:5, 3:5, 4:5, 5:5, 6:4, 7:3, 8:3}
)

def rerank(all_beams, ext_inds):
    beam_lists = (all_beams[i: i+n] for i, n in ext_inds if n > 0)
    return list(concat(map(rerank_one, beam_lists)))

def rerank_mp(all_beams, ext_inds):
    beam_lists = [all_beams[i: i+n] for i, n in ext_inds if n > 0]
    with mp.Pool(8) as pool:
        reranked = pool.map(rerank_one, beam_lists)
    return list(concat(reranked))

def rerank_one(beams):
    @curry
    def process_beam(beam, n):
        for b in beam[:n]:
            b.gram_cnt = Counter(_make_n_gram(b.sequence))
        return beam[:n]
    beams = map(process_beam(n=_PRUNE[len(beams)]), beams)
    best_hyps = max(product(*beams), key=_compute_score)
    dec_outs = [h.sequence for h in best_hyps]
    return dec_outs

def _make_n_gram(sequence, n=2):
    return (tuple(sequence[i:i+n]) for i in range(len(sequence)-(n-1)))

def _compute_score(hyps):
    all_cnt = reduce(op.iadd, (h.gram_cnt for h in hyps), Counter())
    repeat = sum(c-1 for g, c in all_cnt.items() if c > 1)
    lp = sum(h.logprob for h in hyps) / sum(len(h.sequence) for h in hyps)
    return (-repeat, lp)


def summarize_func(input_doc, beam_size):
    model_dir = settings.FAST_ABS_RL_SUMMARIZER_MODEL_DIR
    batch = settings.FAST_ABS_RL_SUMMARIZER_BATCH
    div = settings.FAST_ABS_RL_SUMMARIZER_DIV
    max_dec_word = settings.FAST_ABS_RL_SUMMARIZER_MAX_LEN
    cuda = settings.FAST_ABS_RL_SUMMARIZER_CUDA and torch.cuda.is_available()

    summ_results = decode(input_doc, model_dir, batch,
        beam_size, div, max_dec_word, cuda)
    logger.warning('{}: Decode finished'.format(datetime.datetime.now()))
    return summ_results

class FastSummarizer:
    """This class takes a bunch of articles and creates an extractive summarization based on textrank algorithm."""

    def __init__(self):
        """
            Creates a new object

            Parameters
            ----------
        """
        self.beam_size = 5 # use Abstractor class if equals 1, otherwise use BeamAbstractor

    def sent_remove_punc(self, sentence):
        sent_list = sentence.split(' ')
        new_sent = ""
        for i in range(len(sent_list)):
            if i == 0:
                new_sent += sent_list[i]
            elif sent_list[i] in string.punctuation:
                new_sent += sent_list[i]
            else:
                new_sent += ' ' + sent_list[i]
        return new_sent

    def summarize(self, document, text: str, article, section=None) -> List[int]:
        logger.warning('{}: In Fast Summarize'.format(datetime.datetime.now()))
        input_text = nltk.tokenize.sent_tokenize(text)
        logger.warning('{}: Tokenize done'.format(datetime.datetime.now()))
        input_text = [input_text]

        logger.warning('{}: About to run summarize func'.format(datetime.datetime.now()))
        final_summ = summarize_func(input_text, self.beam_size)
        logger.warning('{}: Summarize-Func done'.format(datetime.datetime.now()))
        final_sum_sents = []
        for i in range(len(final_summ)):
            for j in range(len(final_summ[i])):
                sent_temp = self.sent_remove_punc(final_summ[i][j])
                final_sum_sents.append(sent_temp)
        # print(final_sum_sents)

        final_sent_ids = []  # keep track of sentence ids
        for sent in final_sum_sents:
            if section is not None:
                new_sent = Sentence(text=sent.capitalize(), position=-1, section=section, article=article)
            else:
                new_sent = Sentence(document=document, text=sent.capitalize(), position=-2, article=article)
            new_sent.save()
            final_sent_ids.append(new_sent.id)

        return final_sent_ids


class TestFastSummarizer(unittest.TestCase):
    def setUp(self):
        self.document = None
        self.summarizer = FastSummarizer()
        self.documents = [
            '''Crowdsourcing is a sourcing model in which individuals or organizations obtain goods and services, including ideas and finances, from a large, relatively open and often rapidly-evolving group of internet users; it divides work between participants to achieve a cumulative result. The word crowdsourcing itself is a portmanteau of crowd and outsourcing, and was coined in 2005. As a mode of sourcing, crowdsourcing existed prior to the digital age (i.e. "offline").

Major differences between crowdsourcing and outsourcing include features such as: crowdsourcing comes from a less-specific, more public group (i.e. whereas outsourcing is commissioned from a specific, named group) and; includes a mix of bottom-up and top-down processes. Advantages of using crowdsourcing may include improved costs, speed, quality, flexibility, scalability, or diversity.

        Some forms of crowdsourcing, such as in "idea competitions" or "innovation contests" provide ways for organizations to learn beyond the "base of minds" provided by their employees (e.g. LEGO Ideas). Tedious "microtasks" performed in parallel by large, paid crowds (e.g. Amazon Mechanical Turk) are another form of crowdsourcing. It has also been used by not-for-profit organisations and to create common goods (e.g. Wikipedia). The effect of user communication and the platform presentation should be taken into account when evaluating the performance of ideas in crowdsourcing contexts. ''',
            '''
                          Crowdsourcing is the process of getting work or funding, usually online, from a crowd of people. The word is a combination of the words 'crowd' and 'outsourcing'. The idea is to take work and outsource it to a crowd of workers.

Famous Example: Wikipedia. Instead of Wikipedia creating an encyclopedia on their own, hiring writers and editors, they gave a crowd the ability to create the information on their own. The result? The most comprehensive encyclopedia this world has ever seen.

Crowdsourcing & Quality: The principle of crowdsourcing is that more heads are better than one. By canvassing a large crowd of people for ideas, skills, or participation, the quality of content and idea generation will be superior.

Different Types of Crowdsourcing
Crowdsource Design
If you’re looking for a logo design, you can tell a crowd of designers what you want, how much you will pay, and your deadline. All interested designers will create a finished design specifically for you. You’ll receive 50-300+ different finished logo designs, and you can keep whichever design you like the best. By doing design this way, crowdsourcing actually increases the quality & decreases the price, compared to online freelancing.

Crowdsourcing can also be used to get designs for furniture, fashion, advertisements, video, & product design. Just about anything that can be designed can be crowdsourced.

Crowdfunding
Crowdfunding involves asking a crowd of people to donate money to your project. For example, if you want to raise $10,000 to pay for studio time to record a new CD, crowdfunding can help you raise that money.. You find a crowdfunding platform, set the goal amount, deadline, and any rewards offered to donors. You must raise 100% of your goal before the deadline, or all the donations are returned to the donors. Deadlines are typically less than 60 days.

Crowdfunding is mostly used by artists, charities, & start-ups to raise money for projects such as filming a documentary, manufacturing an iPod watch, cancer research, or seed money. Read more about crowdfunding or browse crowdfunding sites.

Microtasks
Microtasking involves breaking work up into tiny tasks and sending the work to a crowd of people. If you have 1,000 photos on your website that need captions, you can ask 1,000 individual people to each add a caption to one photo. Break up the work and decide the payment for each completed task (typically .01¢ – .10¢ per task). With microtasking, you can expect to see results within minutes. Microtasking can involve tasks such as scanning images, proofreading, database correction and transcribing audio files.

Work is done faster, cheaper, and usually with less errors (when validation systems are in place). Additionally, microtasks can often be performed by people in less fortunate countries, including those with SMS capabilities but without computers. Read more about microtasks or browse microtasks sites.

Open Innovation
If you are unsure of where to begin with an idea for a business opportunity, whether it’s product design or perhaps a marketing firm, crowdsourcing can help through open innovation. Open innovation allows people from all aspects of business such as investors, designers, inventors, and marketers to collaborate into a functional profit making reality. This can be done either through a dedicated web platform to gain outside perspective, or used with only internal employees.

Open innovation brings together people from different parts of the world and different sectors of business to work together on a project. This is effectively a collection of different fields and levels of expertise that would not otherwise be available to any budding entrepreneur. It also elevates previously considered uninvolved parties, such as investors, to roll up their sleeves and impart their knowledge, essentially becoming more than just a cash cow.

Pros & Cons
Crowdsourcing’s biggest benefit is the ability to receive better quality results, since several people offer their best ideas, skills, & support. Crowdsourcing allows you to select the best result from a sea of ‘best entries,’ as opposed to receiving the best entry from a single provider. Results can be delivered much quicker than traditional methods, since crowdsourcing is a form of freelancing. You can get a finished video within a month, a finished design or idea within a week, and microtasks appear within minutes.

Clear instructions are essential in crowdsourcing. You could potentially be searching through thousands of possible ideas, which can be painstaking, or even complicated, if the instructions are not clearly understood. Some forms of crowdsourcing do involve spec work, which some people are against. Quality can be difficult to judge if proper expectations are not clearly stated.'''
        ]
        self.documents2 = ['Crowdsourcing is the process of using many disparate individuals (the "crowd") to perform services or to generate ideas or content. As a practice, it has been around longer than the actual term, which dates back only to 2006.', 'How Did Crowdsourcing Start?', 'The concept of crowdsourcing is built on an early 20th-century theory sometimes referred to as the "wisdom of crowds." The idea is that a large group of people can collectively provide surprising insight or value as a workforce.', "This is rooted in the example of British scientist Sir Francis Galton, who in 1907 asked more than 700 people at a county fair to guess the weight of an ox. No one individual guessed correctly, but the average of all the guesses provided a number almost identical to the ox's weight.", 'Who Uses Crowdsourcing?', 'Some businesses use crowdsourcing to accomplish specific tasks or generate ideas. While traditional outsourcing involves businesses choosing a specific contractor or freelancer for a job, crowdsourced work is spread across a large, often undefined group. Unlike a traditional business model, the people in these groups have no connection to each other or to the business aside from their crowdsourced input.', 'In addition to the completion of tasks, crowdsourcing can provide valuable data and insight into the actions of large groups of people. For example, knowing what information people look for in search engines or what videos they watch online can help businesses gauge public interest in their own content, products, and services.', 'In addition to businesses, small nonprofits or community organizations with limited budgets can use crowdsourcing to spread their messages or promote events.', 'Online Crowdsourcing', 'Since the practice of using many individual inputs to create a single common product came to be known as crowdsourcing, it has become popular on the internet. Online culture facilitates easy information sharing and efficient communication, both of which are key to crowdsourcing.', 'One common example of crowdsourcing is in software development. Many software programs, especially those that are available for free, are "open source." This means that the actual code is available for programmers to see and review, allowing them to make changes or additions to the software.', 'OpenOffice, which is a productivity suite compatible with Microsoft Office products, is one example of open-source software. Because it is developed through a form of crowdsourcing, it also is free to download and use.', 'Crowdsourcing Marketplaces', 'Many forms of crowdsourcing are a means of attracting free labor. By seeking input from the crowd, businesses or other organizations bypass the process of hiring someone to do the desired job. There are forms of crowdsourcing, though, that involve getting paid.', 'Crowdsourcing marketplaces on the web, also known as "micro-labor" sites, provide opportunities for groups of people to perform tasks or "micro-jobs" for small fees. Crowdsourcing websites put out open calls on behalf of clients who need microtasks performed. For example, Amazon’s Mechanical Turk offers virtual tasks that can be done online from home, and TaskRabbit connects people to complete virtual tasks in addition to running errands or doing odd jobs in person.', 'Microworkers on these sites are not necessarily providing the same form of wisdom as those in other forms of crowdsourcing, such as with open-source software. Crowdsourcing marketplaces are different because each micro-worker is simply following instructions from a crowdsourcer.', 'However, companies that use micro-labor often label these tasks as crowdsourcing jobs and do still receive some of the benefits of a large crowd. If they are putting out calls for many small tasks to be completed and getting responses from many micro-workers, the company still gets the benefit of multiple viewpoints over time from multiple sources.', 'Pros and Cons of Crowdsourcing', 'No matter whether it uses in-person groups, online connections, or micro-labor from marketplaces, crowdsourcing comes with pros and cons.', 'It is often cheaper than hiring a professional contractor or a traditional employee. For example, if a business wants to develop a new logo or slogan, it might put the concept in front of its customer base, challenging people to come up with ideas or designs that could be used. This method can be good for achieving positive results because the crowd might generate ideas that no one would have discovered through a more traditional approach—and the cost might be no more than rewarding those with the best ideas with discounts or other perks.', "However, the process offers limited control. Following the same example of the new logo or design, a traditional approach would allow the company to oversee the process from beginning to end. If there's even a slight miscommunication with the crowd in a crowdsourcing campaign, the project can go in the wrong direction quickly and might result in nothing more than a waste of time and an irate customer base."]

    def test_summarize(self):
        # input_doc = self.documents

        # input_doc = ""
        # for doc in self.documents:
        #     input_doc += doc

        # input_doc = self.documents[0] + self.documents[1]
        # input_doc = self.documents
        input_doc = self.documents2
        # for sentence in input_doc:
        #     print("Sentence:")
        #     print(sentence)

        self.summarizer.summarize(self.document, input_doc)
