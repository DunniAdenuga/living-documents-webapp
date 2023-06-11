import re
import unittest
from typing import List, Set
import logging
import datetime

import igraph
import nltk
import numpy
from nltk.stem.snowball import SnowballStemmer
from pulp import GUROBI, LpBinary, LpMaximize, LpProblem, LpVariable, lpSum
from pycorenlp import StanfordCoreNLP
from sklearn.feature_extraction.text import TfidfVectorizer
from text_generation.models.sentence import Sentence

logger = logging.getLogger(__name__)


def _tokenize_and_stem(text: str):
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    stemmer = SnowballStemmer('english')
    tokens = [
        word for sent in nltk.sent_tokenize(text)
        for word in nltk.word_tokenize(sent)
    ]

    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    filtered_tokens = []
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems


class ExtractiveSummarizer:
    """This class takes a bunch of articles and creates an extractive summarization."""

    def __init__(self, stopwords: Set[str] = []):
        """
        Creates a new object

        Parameters
        ----------
        stopwords
            This is an optional parameter, the default is no stopwords. If there are no
            stopwords it loads the ones from nltk, if there are stopwords it uses those
            instead
        """
        if stopwords == []:
            self.stopwords = set(nltk.corpus.stopwords.words('english'))
        else:
            self.stopwords = stopwords

    def summarize(self,
                  text: str,
                  query: List[str],
                  document,
                  section = None,
                  max_words: int = 200) -> List[str]:
        """
        Takes *all* of the corpus in one string for text and returns a
        summarization as list of strings

        Parameters
        ----------
        text:
            The entire corpus in a single string! TODO this likely needs to
            change to documents and we can do something to track provenance
            here.
        query:
            A list of search terms that was used to generate the corpus

        Returns
        -------
        List(str)
            A list of sentences that summarize the corpus
        """

        # If it's section, make query just the section header

        # setup the model that we will construct and send to gurobi
        logger.warn('{}: Setup the model'.format(datetime.datetime.now()))
        model = LpProblem("mip1", LpMaximize)
        sim_threshold = 0.6

        # break the text into sentences for processing
        logger.warn('{}: Tokenize sentences'.format(datetime.datetime.now()))
        sentences = nltk.tokenize.sent_tokenize(text)
        '''
        Full sentence cosine similarity comparison
        '''
        logger.warn('{}: Tfidf Vectorization and cosine similarity'.format(
            datetime.datetime.now()))
        bag_of_words_matrix = TfidfVectorizer(
            tokenizer=_tokenize_and_stem).fit_transform(sentences)
        cosine_similarity_matrix = (
            bag_of_words_matrix * bag_of_words_matrix.T).A
        sources, targets = cosine_similarity_matrix.nonzero()
        similarity_igraph = igraph.Graph(
            list(zip(sources, targets)), directed=True)
        txtRankScores = igraph.Graph.pagerank(similarity_igraph)
        '''
        Entity-based ranking
        '''
        # need this for section
        # TODO honestly not sure why this is here, it is repeating above code,
        # only with the query added...this might be more appropriately used as
        # the vocabulary parameter for vectorization???
        logger.warn('{}: Entity-based ranking'.format(datetime.datetime.now()))
        sentences_query = list(sentences)
        sentences_query.append(' '.join(query))
        bag_of_words_matrix = TfidfVectorizer(
            tokenizer=_tokenize_and_stem).fit_transform(sentences_query)
        query_cosine_similarity_matrix = (
            bag_of_words_matrix * bag_of_words_matrix.T).A
        query_index = len(sentences_query) - 1
        sentence_importance_scores = [
            (query_cosine_similarity_matrix[query_index, k] + 0.00001)
            for k in range(len(sentences))
        ]
        lpvariable_sentence_list = []

        # start constructing the lp model for gurobi
        logger.warn('{}: Construct gurobi model'.format(
            datetime.datetime.now()))
        for i in range(len(sentences)):
            lpvar = LpVariable("var_" + str(i), cat=LpBinary)
            lpvariable_sentence_list.append(lpvar)

        # the objective function finds the important sentences
        list_obj_function = [
            sentence_importance_scores[i] * txtRankScores[i] *
            lpvariable_sentence_list[i]
            for i in range(len(lpvariable_sentence_list))
        ]

        model += lpSum(list_obj_function)

        visited = []

        for i in range(len(sentences)):
            s_indices = numpy.where(
                cosine_similarity_matrix[i, :] >= sim_threshold)[0].tolist()
            for j in s_indices:
                if i == j:
                    continue
                if (i, j) not in visited:
                    visited.append((i, j))
                    model += lpvariable_sentence_list[i] + lpvariable_sentence_list[j] <= 1.0, \
                             f'constraint_facts_redundancy_{i}_{lpvariable_sentence_list[i].name}_{lpvariable_sentence_list[j].name}'

        total_words = 0
        sentence_lengths = []
        for i in range(len(txtRankScores)):
            words = nltk.tokenize.word_tokenize(sentences[i])
            count = 0
            for word in words:
                if str.isalnum(word):
                    count += 1

            # lengths of sentences
            sentence_lengths.append(count)
            # total words assigned to class
            total_words += count

        model += lpSum([
            lpvariable_sentence_list[i] * sentence_lengths[i]
            for i in range(len(lpvariable_sentence_list))
        ]) <= max_words

        logger.warn('{}: Solve gurobi model'.format(datetime.datetime.now()))
        model.solve(GUROBI(timeLimit=50.0, msg=False))

        logger.warn('{}: Process gurobi model results'.format(
            datetime.datetime.now()))
        final_var_list = []
        for variable in model.variables():
            if variable.varValue == 1.0:
                final_var_list.append(variable.name)

        def sentences_from_variables(final_variables):
            final_Sents = []
            for elem in final_variables:
                m = elem.split("_")
                first_sent = int(m[1])
                final_Sents.append(first_sent)
            return final_Sents

        def sentenceCapitalize(sent):
            return sent[0].capitalize() + sent[1:]

        final_summ_sents = []
        final_sel_var_list = sentences_from_variables(final_var_list)

        # TODO merging this with the old text needs to be done, right now it just overwrites everything
        logger.warn('{}: Adding sentences to document'.format(
            datetime.datetime.now()))
        i = 0  # position in dictionary
        for a in final_sel_var_list:
            sentence = sentences[int(a)]
            sentence = sentence.strip()
            sentence = sentence.replace('\n', ' ')
            sentence = sentenceCapitalize(sentence)

            final_summ_sents.append(sentence.replace(" .", "."))
            if section:
                new_sent = Sentence(section=section, document=document, text=sentence, position=i)
            else:
                new_sent = Sentence(document=document, text=sentence, position=i)
            new_sent.save()
            new_sent.build_triples()
            i = i + 1

        logger.warn('{}: Finished generating summary'.format(
            datetime.datetime.now()))
        # TODO this isn't really needed anymore
        return final_summ_sents  # , [int(a) for a in final_sel_var_list]


class TestFrequencySummarizer(unittest.TestCase):
    def setUp(self):
        self.summarizer = ExtractiveSummarizer()
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
        d = Document(title="Crowdsourcing")

    def test_stemmed_vectorizer(self):
        tfidf_matrix = self.summarizer.tfidf_vectorizer.fit_transform(
            self.documents)
        # print(tfidf_matrix.shape)
        # print(self.summarizer.tfidf_vectorizer.get_feature_names())

    def test_summarize(self):
        self.summarizer.summarize(
            self.documents[0] + 'n' + self.documents[1],
            ['crowdsourcing', 'workers'],
            max_words=400)


if __name__ == '__main__':
    unittest.main()
