import datetime
import logging
import random

from typing import List

from django.db import models
from newspaper import Article as RawArticle
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

from text_generation.extractors.article_extractor import ArticleExtractor
from text_generation.extractors.google_extractor import GoogleExtractor
from text_generation.models.article import Article
from text_generation.models.keyword import Keyword
from text_generation.models.section import Section
from text_generation.models.sentence import Sentence
from text_generation.models.suggested_link import SuggestedLink
from text_generation.models.document_history import DocumentHistory
from text_generation.summarizers.textrank_summarizer import TextrankSummarizer
from text_generation.summarizers.fast_abs_rl_summarizer import FastSummarizer
# from text_generation.summarizers.frequency_summarizer import FrequencySummarizer
from text_generation.summarizers.pre_summ_summarizer import PreSummSummarizer
from text_generation.summarizers.bart_summarizer import BartSummarizer
from text_generation.summarizers.t5_summarizer import T5Summarizer
from text_generation.summarizers.gpt3_summarizer import GPT3Summarizer
from text_generation.utilities import process_text

logger = logging.getLogger(__name__)


class Document(models.Model):
    """
    """
    title = models.TextField(blank=True)
    author = models.TextField(blank=True)

    def __str__(self):
        return f'{self.id}: {self.title}'

    def _set_body_sentences(self, body_text: str):
        """This is used mostly for testing, so that we can create a new document and not have to run the summarizers
        :param str body_text: the text that you want in the document
        :return None
        """
        sentences = sent_tokenize(body_text)

        i = 0  # position in dictionary
        for sentence in sentences:
            new_sent = Sentence(document=self, text=sentence, position=i)
            new_sent.save()
            new_sent.build_triples()
            i = i + 1

    # TODO should have a flag for regenerating section summaries as well
    def generate_summarization(self, get_articles=True, summarizer="gpt3") -> None:
        """This is mostly used for generating a new article right now, going to handle the updating of a summarization
        differently....probably need to do individual section generation or something.

        :param get_articles: set to True if you want to do a query expansion and get more articles, set to false if
        you want to grab new urls, it doesn't delete existing articles atm
        :param generate_sections: set to True if you want to generate the section summaries as well
        :param summarizer : text format of chosen summarizer
        :return: None
        """
        # delete all sentences in current document then generate new summary
        Sentence.objects.filter(document=self, section=None, is_user_defined=False).delete()
        Keyword.objects.filter(document=self).delete()
        SuggestedLink.objects.filter(document=self).delete()

        # an if statement about to get more urls or not
        if get_articles:
            # get suggested sections from here
            # and set keywords
            temp_articles1 = self._expand_terms_get_articles(search_terms=[self.title])
            # temp_articles = random.choices(temp_articles, k=5)
            # temp_articles = random.sample(temp_articles, 5)
            # or pick top 5 articles
            temp_articles = temp_articles1[:5]
            for article in temp_articles:
                self.articles.create(document=self, text=article.text, url=article.url, section=None)
            self.set_keywords_links(self.title)
        else:
            self._user_defined_articles()
            self.clean_keywords()
            self.set_keywords_links(self.title)

        articles_to_summarize = Article.objects.filter(document=self, section=None)
        logger.warning('{}: About to start Summarize'.format(datetime.datetime.now()))
        self._summarize_articles(articles=articles_to_summarize, summarizer_text=summarizer)
        self._remove_repeat_sentences()

        logger.warning('{}: Creating Full Graph'.format(datetime.datetime.now()))
        # generate the tf idf scores for the entire summarized document
        self.calculate_tf_idf_scores(useAllSentences=False)
        # build the triple graph for the entire document
        self.build_triple_graph(useAllSentences=False)

        logger.warning('{}: Creating Full Graph finished'.format(datetime.datetime.now()))
        logger.warning(
            '{}: Number of sentences: '.format(str(len(self.sentences.all())).format(datetime.datetime.now())))
        logger.warning('{}: Ordering Sentences using triple graph'.format(datetime.datetime.now()))
        # logger.warning("Sentences before ordering")
        # logger.warning(self.sentences.all())
        self.graph.sort_sentences()
        self.save()

    def generate_section_summarization(self, section: Section, get_articles=True, summarizer="gpt3") -> None:
        """
        This creates a new section and generates the text

        :param get_articles:
        :param section: The section that you want to generate text for
        :param summarizer:
        :return: None
        """
        # self.temp_articles = self._expand_terms_get_articles(search_terms=[self.title, section.heading])
        # for article in self.temp_articles:
        #     self.articles.create(text=article.text, url=article.source_url)
        # self._summarize_articles(self.temp_articles, section=section)
        # TODO this is not sorting the sentences at the moment
        # an if statment about to get more urls or not
        if get_articles:
            # get suggested sections from here
            # and set keywords
            temp_articles1 = self._expand_terms_get_articles(search_terms=[self.title, section.heading])
            # temp_articles = random.choices(temp_articles, k=3)
            # temp_articles = random.sample(temp_articles, 3)
            # or pick top 3 articles
            temp_articles = temp_articles1[:3]
            logger.warning("Get Articles is true. Articles about to be set listed below.")
            for article in temp_articles:
                logger.warning(article)
                section.articles.create(text=article.text, url=article.url)
        else:
            self._user_defined_articles(section=section)
        #     I want to keep keywords for introduction if summarizer is gpt3
        if summarizer != "gpt3":
            self.clean_keywords()
        self.set_keywords_links(self.title, section.heading)

        # articles_to_summarize = Article.objects.filter(document=self, section=section)
        articles_to_summarize = list(section.articles.all())
        logger.warning(articles_to_summarize)
        logger.warning(
            'About to summarize {} articles: '.format(str(len(section.articles.all()))))
        self._summarize_articles(articles=articles_to_summarize, section=section, summarizer_text=summarizer)

        logger.warning(
            'Number of sentences in section: {} '.format(str(len(section.sentences.all()))))
        self._remove_repeat_sentences()
        logger.warning(
            '{}: Number of sentences: '.format(str(len(section.sentences.all())).format(datetime.datetime.now())))

        # generate the tf idf scores for the entire summarized document
        section.calculate_tf_idf_scores()
        # build the triple graph for the only section
        section.build_triple_graph()

        logger.warning('{}: Creating Section Graph finished (after new section summary)'.format(
            datetime.datetime.now()))
        section.graph.sort_sentences()
        self.save()

    def _assemble_search_keywords(self, search_terms: List[str] = [], remove_terms: List[str] = []) -> (
            List[str], List[str]):
        """
        This gets the search terms and the remove terms from the keywords based on their various values
        :param search_terms: any custom search terms you want to seed it with
        :param remove_terms: any custom remove terms you want to seed it with
        :return: tuple of the search and remove terms
        """
        for keyword in Keyword.objects.filter(is_deleted=False, is_user_defined=True, document=self):
            search_terms.append(keyword.text)

        for keyword in Keyword.objects.filter(is_deleted=True, is_user_defined=True, document=self):
            remove_terms.append(keyword.text)

        return search_terms, remove_terms

    def _expand_terms_get_articles(self, search_terms: List[str] = [], remove_terms: List[str] = [], summarizer="gpt3") -> (
            List[RawArticle], List):
        """
        This expands the keywords via a google search and tf-idf stuff.
        :param search_terms: any custom search terms you want to seed it with
        :param remove_terms: any custom remove terms you want to seed it with
        :return: list of articles
        """
        # get articles and expanded terms
        logger.warning('{}: Extracting terms with a google query'.format(datetime.datetime.now()))
        extractor = GoogleExtractor()
        search_terms, remove_terms = self._assemble_search_keywords(search_terms=search_terms,
                                                                    remove_terms=remove_terms)

        logger.warning('{}: Getting related articles from google searches'.format(datetime.datetime.now()))
        articles, expanded_terms = extractor.get_articles(search_terms=search_terms, remove_terms=remove_terms)
        # delete not used keywords from previous search
        logger.warning('{}: Back from extractor. Gotten related articles from google searches'.format(datetime.datetime.now()))
        # self.clean_keywords()
        # add keywords to the model

        if summarizer != "gpt3":
            self.clean_keywords()
            for keyword in expanded_terms:
                Keyword.objects.get_or_create(text=keyword, document=self)

        return articles

    def set_keywords_links(self, title, section_heading=None, summarizer="gpt3"):
        # search_term = [title]
        if section_heading is None:
            search_term = title.split(" ")
        else:
            search_term = title.split(" ") + [section_heading]
        extractor = GoogleExtractor()

        logger.warning('{}: Getting related terms from google searches'.format(datetime.datetime.now()))
        articles_s, expanded_terms = extractor.get_articles(search_terms=search_term, remove_terms=[])
        logger.warning('{}: Back from getting related terms from google searches'.format(datetime.datetime.now()))
        # if summarizer == "gpt3":
        # Keyword.objects.get_or_create(text="keyword", document=self)

        if summarizer != "gpt3":
            for keyword in expanded_terms:
                Keyword.objects.get_or_create(text=keyword, document=self)
        allArticlesInDocument = Article.objects.filter(document=self)

        for section in self.sections.all():
            allArticlesInSection = Article.objects.filter(section=section)
            allArticlesInDocument = allArticlesInDocument.union(allArticlesInSection)

        allArticlesInDocumentList = list(allArticlesInDocument)

        for article in articles_s:
            # logger.warn("each article")
            # logger.warn(str(article))
            # if not allArticlesInDocumentList.filter(url=article.url).exists():
            if len([art for art in allArticlesInDocumentList if art.url == article.url]) <= 0:
                SuggestedLink.objects.get_or_create(url=article.url, document=self)

    def _summarize_articles(self,  articles: List[Article], section: Section = None, summarizer_text='gpt3',) -> None:
        """
        Retrieve articles and summarize each one
        :param section: optional argument if you want to summarize an individual section
        :return: None
        """
        number_of_words = 125
        # ratio = 0.2
        if summarizer_text == 'textrank':
            summarizer = TextrankSummarizer(words=number_of_words)
        elif summarizer_text == 'fast':
            summarizer = FastSummarizer()
        # elif summarizer_text == 'frequency':
        #     summarizer = FrequencySummarizer(min_cut=0.1, max_cut=0.9)
        elif summarizer_text == 'presum':
            summarizer = PreSummSummarizer()
        elif summarizer_text == 'bart':
            summarizer = BartSummarizer(words=125)
        elif summarizer_text == 't5':
            summarizer = T5Summarizer(words=125)
        elif summarizer_text == 'gpt3':
            summarizer = GPT3Summarizer(words=200)

        logger.warning('{}:Summarizer set. About to summarize each article'.format(datetime.datetime.now()))
        i = 1
        for article in articles:
            if len(article.text.split('.')) <= 5:
                logger.warning("less than 5 sentences, skip...")
                continue
            logger.warning('Printing i')
            logger.warning(i)
            summarizer.summarize(document=self, text=article.text, section=section, article=article)
            i = i + 1

    def clean_keywords(self, summarizer="gpt3"):
        """ Remove all the keywords that haven't been used/modified by user (is_user_defined=False)
        :return: None
        """
        if summarizer != "gpt3":
            Keyword.objects.filter(document=self, is_user_defined=False).delete()

    # TODO this is not currently used, although we might want to start using it
    def _sentence_similarity(self, sentence1, sentence2, ratio_threshold=1.0):
        """ Compare the similarity between two sentences, if the similarity ratio >= the threshold,
        this function will return True and it will return False otherwise.
        :param sentence1: string you want to compare
        :param sentence2: string you want to compare
        :param ratio_threshold: if above or equal to this ratio, function will return True
        :return: bool, whether these two sentences are the same/similar
        """
        from difflib import SequenceMatcher
        ratio = SequenceMatcher(None, sentence1, sentence2).ratio()
        if ratio >= ratio_threshold:
            return True
        return False

    def _remove_repeat_sentences(self) -> None:
        """ Remove repeated sentences from the document. Only call this before the tree has been built, not after
        :param summary: newly created summary -> list of string
        :return: updated summary (after removal of repeated sentences)
        """
        sentence_lookup = {str: Sentence}  # hash all sentences here, to remove repeated sentences

        for sentence in self.sentences.all():
            if sentence.text in sentence_lookup:
                sentence.delete()
            else:
                sentence_lookup[sentence.text] = True

    # TODO this is currently only calculating it for the 'intro' section and not the subsections
    def calculate_tf_idf_scores(self, useAllSentences=False):
        """Mostly an internal function that processes the text in the sentences and vectorizes the tokens, you
        shouldn't need to call this
        :return: None
        """
        texts = []
        allSents = self.getAllDocSecSentences()
        if useAllSentences:
            for sentence in allSents:
                process_text_result = process_text(sentence.text)
                list_of_stemmed_words = []
                # get list of stemmed words
                for res in process_text_result:
                    list_of_stemmed_words.append(res["stemmed_word"])
                texts.append(' '.join(list_of_stemmed_words))
        else:
            for sentence in self.sentences.filter(section=None):
                process_text_result = process_text(sentence.text)
                list_of_stemmed_words = []
                # get list of stemmed words
                for res in process_text_result:
                    list_of_stemmed_words.append(res["stemmed_word"])
                texts.append(' '.join(list_of_stemmed_words))

        tfidf_vec = TfidfVectorizer()
        transformed = tfidf_vec.fit_transform(texts)
        index_value = {i[1]: i[0] for i in tfidf_vec.vocabulary_.items()}
        temp_tf_idf_scores = []
        # set em
        for row in transformed:
            temp_tf_idf_scores.append({
                index_value[column]: value
                for (column, value) in zip(row.indices, row.data)
            })

        self.tf_idf_scores = {}
        for row in temp_tf_idf_scores:
            for token in row.keys():
                self.tf_idf_scores[token] = row[token]

    def getAllDocSecSentences(self):
        allSents = []
        for sent in self.sentences.all():
            allSents.append(sent)
        for section in self.sections.all():
            for sec_sent in section.sentences.all():
                allSents.append(sec_sent)
        return allSents

    # TODO this is currently only building it for the 'intro' section and not the subsections
    def build_triple_graph(self, useAllSentences=False) -> None:
        """
        Builds the triple graph for the sentences in the document
        :return: None
        """
        logger.warn("in build-triple graph")
        from text_generation.annotators.triple_graph import TripleGraph
        # logger.warn("self.sentences.all()")
        # logger.warn(self.sentences.all())
        # logger.warn("self.tf_idf_scores")
        # logger.warn(self.tf_idf_scores)
        # changed self.sentences.all()
        allSents = self.getAllDocSecSentences()
        if useAllSentences:
            logger.warning("about to use all sentences")
            self.graph = TripleGraph(allSents, self.tf_idf_scores)  # saw this in test
        else:
            logger.warning("about to use ONLY some sentences")
            self.graph = TripleGraph(self.sentences.filter(section=None), self.tf_idf_scores)
        #     use only section sentences
        logger.warning('{}: Triple Graph built'.format(datetime.datetime.now()))

    def change_word_text(self, old_word: str, new_word: str):
        """
        ***************************************************Change this method*******************************************
        Do targeted search
        get summary of length x
        get triples and merge
        :param old_word:
        :param new_word:
        :return:
        """
        logger.warning('In change_word_text')

        if len(self.sentences.all()) > 0:
            self.calculate_tf_idf_scores()
            self.build_triple_graph()

        extractor = GoogleExtractor()

        query = self.title + "+" + "\"" + new_word + "\"" + "-" + old_word
        query_url = f'http://www.google.com/search?q={query}'
        urls = extractor.execute_google_query_url(google_query=query_url)
        extractor.extract_articles(urls)
        articles = extractor.articles
        # terms = extractor.terms
        # get expanded terms later
        logger.warning('Targeted Search with new word completed')

        summarizer = TextrankSummarizer(words=150)
        # summary = []
        model_ = []
        for article in articles:
            model2 = summarizer.summarize(document=self, text=article.text)
            for elem in model2:
                model_.append(elem)

        logger.warning('Summarized results of targeted search')
        return model_

    def _user_defined_articles(self, section: Section = None):
        """
        This is used to get the urls that are predefined by users, it is only fetching ones that don't have any text
        :param section: is there a section that this is attached to
        :return: None
        """
        # get the urls that we need to fetch (e.g. they don't have any text)
        if section is None:
            incomplete_articles = Article.objects.filter(text='', document=self, section=None)
        else:
            incomplete_articles = Article.objects.filter(text='', section=section)
        urls = [article.url for article in incomplete_articles]

        article_extractor = ArticleExtractor()
        article_extractor.extract_articles(urls)

        # for article in article_extractor.articles:
        #     incomplete_articles
        for inc_article in incomplete_articles:
            arts = list(filter(lambda x: x.url == inc_article.url, article_extractor.articles))
            if arts:
                inc_article.text = arts[0].text
                inc_article.save()
