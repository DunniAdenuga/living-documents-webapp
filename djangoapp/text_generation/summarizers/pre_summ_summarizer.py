import logging
import datetime
import unittest
from typing import List

import nltk

from text_generation.models.sentence import Sentence

from summa import summarizer
import glob
import os
import random
import signal
import time
import sys
import nltk
import torch
import string
from pytorch_transformers import BertTokenizer

from .pre_summ.models import data_loader
from .pre_summ.models.model_builder import AbsSummarizer
from .pre_summ.models.model_builder import ExtSummarizer
from .pre_summ.models.trainer_ext import build_trainer
from .pre_summ.models.predictor import build_predictor
from .pre_summ.others.logging import logger, init_logger
sys.path.append(os.path.abspath(os.path.join('text_generation/summarizers/pre_summ')))


logger = logging.getLogger(__name__)

model_flags = ['hidden_size', 'ff_size', 'heads', 'emb_size', 'enc_layers', 'enc_hidden_size', 'enc_ff_size',
               'dec_layers', 'dec_hidden_size', 'dec_ff_size', 'encoder', 'ff_actv', 'use_interval']


class Args:
    def __init__(self):
        self.task = 'abs'
        self.encoder = 'bert'
        self.mode = 'test_text'
        self.model_path = 'text_generation/summarizers/pre_summ/temp_tensorboard_log/'
        self.temp_dir = 'text_generation/summarizers/pre_summ/temp_Bert_cache'

        self.batch_size = 140
        self.test_batch_size = 200
        self.max_ndocs_in_batch = 6

        self.max_pos = 512
        self.use_interval = True
        self.large = False
        self.load_from_extractive = ''

        self.sep_optim = False
        self.lr_bert = 2e-3
        self.lr_dec = 2e-3
        self.use_bert_emb = False

        self.share_emb = False
        self.finetune_bert = True
        self.dec_dropout = 0.2
        self.dec_layers = 6
        self.dec_hidden_size = 768
        self.dec_heads = 8
        self.dec_ff_size = 2048
        self.enc_hidden_size = 512
        self.enc_ff_size = 512
        self.enc_dropout = 0.2
        self.enc_layers = 6

        # params for EXT
        self.ext_dropout = 0.2
        self.ext_layers = 2
        self.ext_hidden_size = 768
        self.ext_heads = 8
        self.ext_ff_size = 2048

        self.label_smoothing = 0.1
        self.generator_shard_size = 32
        self.alpha =0.6
        self.beam_size = 5
        self.min_length = 15
        self.max_length = 150
        self.max_tgt_len = 140

        self.param_init = 0
        self.param_init_glorot = True
        self.optim = 'adam'
        self.lr = 1.0
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.warmup_steps = 8000
        self.warmup_steps_bert = 8000
        self.warmup_steps_dec = 8000
        self.max_grad_norm = 0.0

        self.save_checkpoint_steps = 5
        self.accum_count = 1
        self.report_every = 1
        self.train_steps = 1000
        self.recall_eval = False

        self.visible_gpus = '-1'
        self.gpu_ranks = '0'
        self.log_file = 'text_generation/summarizers/pre_summ/logs/cnndm.log'
        self.seed = 666

        self.test_all = False
        self.test_from = ''
        self.test_start_from = -1

        self.train_from = ''
        self.block_trigram = True


class PreSummSummarizer:
    def __init__(self):
        self.args = Args()
        self.args.gpu_ranks = [int(i) for i in range(len(self.args.visible_gpus.split(',')))]
        self.args.world_size = len(self.args.gpu_ranks)
        os.environ["CUDA_VISIBLE_DEVICES"] = self.args.visible_gpus

        # init_logger(args.log_file)
        device = "cpu" if self.args.visible_gpus == '-1' else "cuda"
        device_id = 0 if device == "cuda" else -1

    def test_text_abs(self, text_input):
        min_paragraph = 2
        max_paragraph = 4
        min_para_leng = 10

        if len(text_input.split('\n\n')) >= min_paragraph:
            new_input = ""
            new_paragraph = ""
            for paragraph in text_input.split('\n\n'):
                new_paragraph += paragraph.replace('\n', ' ')
                if len(new_paragraph) >= min_para_leng:
                    new_input += new_paragraph
                    new_paragraph = ""
                    if max_paragraph > 1:
                        max_paragraph -= 1
                        new_input += '\n'
            if len(new_paragraph) > 0:
                new_input += new_paragraph
            # text_input = new_input
        else:
            new_input = ""
            new_paragraph = ""
            for paragraph in text_input.split('\n'):
                new_paragraph += paragraph
                if len(new_paragraph) >= min_para_leng:
                    new_input += new_paragraph
                    new_paragraph = ""
                    if max_paragraph > 1:
                        max_paragraph -= 1
                        new_input += '\n'
            if len(new_paragraph) > 0:
                new_input += new_paragraph
        text_input = new_input

        self.args.test_from = 'text_generation/summarizers/pre_summ/pre-trained_models/bertsumextabs_cnndm_final_model.pt'
        logger.info('Loading checkpoint from %s' % self.args.test_from)
        device = "cpu" if self.args.visible_gpus == '-1' else "cuda"

        checkpoint = torch.load(self.args.test_from, map_location=lambda storage, loc: storage)
        opt = vars(checkpoint['opt'])
        for k in opt.keys():
            if (k in model_flags):
                setattr(self.args, k, opt[k])
        # print(args)

        model = AbsSummarizer(self.args, device, checkpoint)
        model.eval()

        test_iter = data_loader.load_text(self.args, text_input, device)

        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True, cache_dir=self.args.temp_dir)
        symbols = {'BOS': tokenizer.vocab['[unused0]'], 'EOS': tokenizer.vocab['[unused1]'],
                   'PAD': tokenizer.vocab['[PAD]'], 'EOQ': tokenizer.vocab['[unused2]']}
        predictor = build_predictor(self.args, tokenizer, symbols, model, logger)
        final_summ = predictor.translate(test_iter, -1)
        # print(final_summ)
        return final_summ

    def test_text_ext(self, text_input):
        min_paragraph = 2
        max_paragraph = 5
        min_para_leng = 10
        min_sent_leng = 5

        if len(text_input.split('\n\n')) >= min_paragraph:
            new_input = ""
            new_paragraph = ""
            for paragraph in text_input.split('\n\n'):
                # new_paragraph += paragraph.replace('\n', ' ')
                para_sent_list = nltk.tokenize.sent_tokenize(paragraph)
                for i in range(len(para_sent_list)):
                    if len(para_sent_list[i]) > min_sent_leng:
                        new_paragraph += para_sent_list[i]
                    if i < len(para_sent_list)-1:
                        new_paragraph += " [CLS] [SEP] "
                if len(new_paragraph) >= min_para_leng:
                    new_input += new_paragraph
                    new_paragraph = ""
                    if max_paragraph > 1:
                        max_paragraph -= 1
                        new_input += '\n'
            if len(new_paragraph) > 0:
                new_input += new_paragraph
            text_input = new_input
        else:
            new_input = ""
            new_paragraph = ""
            for paragraph in text_input.split('\n'):
                para_sent_list = nltk.tokenize.sent_tokenize(paragraph)
                for i in range(len(para_sent_list)):
                    if len(para_sent_list[i]) > min_sent_leng:
                        new_paragraph += para_sent_list[i]
                    if i < len(para_sent_list)-1:
                        new_paragraph += " [CLS] [SEP] "                        
                # new_paragraph += paragraph
                if len(new_paragraph) >= min_para_leng:
                    new_input += new_paragraph
                    new_paragraph = ""
                    if max_paragraph > 1:
                        max_paragraph -= 1
                        new_input += '\n'
            if len(new_paragraph) > 0:
                new_input += new_paragraph
            text_input = new_input

        self.args.test_from = 'text_generation/summarizers/pre_summ/pre-trained_models/bertext_cnndm_transformer.pt'
        logger.info('Loading checkpoint from %s' % self.args.test_from)
        checkpoint = torch.load(self.args.test_from, map_location=lambda storage, loc: storage)
        opt = vars(checkpoint['opt'])
        for k in opt.keys():
            if (k in model_flags):
                setattr(self.args, k, opt[k])
        # print(args)
        device = "cpu" if self.args.visible_gpus == '-1' else "cuda"
        device_id = 0 if device == "cuda" else -1

        model = ExtSummarizer(self.args, device, checkpoint)
        model.eval()

        test_iter = data_loader.load_text(self.args, text_input, device)

        trainer = build_trainer(self.args, device_id, model, None)
        final_summ = ""
        try:
            final_summ = trainer.test(test_iter, -1)
        except:
            pass
        # print(final_summ)
        return final_summ

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

    def summarize(self, document, article, text: str,  section=None) -> List[int]:
        """
        Does the actual work of the summarization
        :param document: This is of type document in the models.py
        :param text: the text to summarize
        :param article: the url that the text came from
        :param section: the section (if there is one) to add the sentence to
        :return: list of the ids of the sentences that were added
        """

        # # summarization using abstractive method
        text_sum = self.test_text_abs(text)

        # # summarization using extractive method
        # text_sum = self.test_text_ext(text)
        # print(text)
        # print("***********************************")
        text_sum = self.sent_remove_punc(text_sum)
        print(text_sum)

        # tokenize the sentences to insert into the data model
        final_sum_sents = nltk.tokenize.sent_tokenize(text_sum)

        final_sent_ids = []  # keep track of sentence ids
        for sent in final_sum_sents:
            if section is not None:
                new_sent = Sentence(text=sent.capitalize(), position=-1, section=section, article=article)
                # section.sentence_set.add(new_sent)
                # section.save()
            else:
                new_sent = Sentence(document=document, text=sent.capitalize(), position=-1, article=article)
            new_sent.save()
            final_sent_ids.append(new_sent.id)

        return final_sent_ids
