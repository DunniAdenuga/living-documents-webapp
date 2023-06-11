import io
import logging
import datetime
import operator
from queue import Queue
from threading import Thread
from typing import List

import PyPDF2
import requests
from PyPDF2.errors import PdfReadError
from newspaper import Article, ArticleException
from sklearn.feature_extraction.text import TfidfVectorizer

from living_documents_server import settings

logger = logging.getLogger(__name__)


class ArticleWorker(Thread):
    """
    The worker that actually does the work of grabbing the article at a url
    and extracting the text from the html

    """

    def __init__(self, queue: Queue, article_container):
        """
        Creates the article worker that grabs an article from a url. The urls are
        stored in the queue and the worker runs until there aren't any urls to
        get from the queue

        Parameters
        ----------
        queue:
            This is the queue that you will add urls today
        article_container:
            This is the collection were the articles are stored when the
            _extract_article method is called for each url. We can't put
            the type hint before the class is defined
        """
        Thread.__init__(self)
        self.queue = queue
        self.article_container = article_container
        # TODO check that object implements articles and extract_article

    def run(self):
        """
        This is called by the worker daemon stuff, you don't need to call this
        manually
        """
        while True:
            url = self.queue.get()
            try:
                article = self.article_container._extract_article(url)
                self.article_container.articles.append(article)
            finally:
                self.queue.task_done()


class ArticleExtractor:
    """
    Multithreaded article extractor, must inherit from this...don't use this
    class directly
    """

    # different implementations will have their own blacklisted url terms
    blacklist = []

    def __init__(self):
        # create the collection
        self.articles = []

    def query_expansion(self, search_terms: List[str]) -> List[str]:
        """ This function is used to get more terms based on the tf-idf ranking of previous search results.
        """
        logger.warning('{}: At the beginning of query expansion'.format(datetime.datetime.now()))
        corpus = [article.text for article in self.articles]
        #   Some words in the stop_words list might be useful and should not be removed (e.g.: 'system', 'detail')
        #   Reference: http://scikit-learn.org/stable/modules/feature_extraction.html#stop-words
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(corpus)
        index_word_dict = {i[1]: i[0] for i in vectorizer.vocabulary_.items()}
        tfidf_scores = dict()
        for row in tfidf_matrix:
            for i in range(len(row.indices)):
                tfidf_scores[index_word_dict[row.indices[i]]] = row.data[i]

        # sort tf-idf values in descending order
        logger.warning('{}: At the middle of query expansion'.format(datetime.datetime.now()))
        sorted_tf_idf_scores = sorted(tfidf_scores.items(), key=operator.itemgetter(1), reverse=True)
        # # extract n words (different from search_terms) with largest tf-idf values
        # sorted_tf_idf_scores = [word for word in sorted_tf_idf_scores if word not in search_terms]
        search_terms_exp = [sorted_tf_idf_scores[i][0] for i in range(settings.ARTICLE_EXTRACTOR_QUERY_EXPANSION_SIZE)]
        search_terms_exp = [word for word in search_terms_exp if word not in search_terms]
        logger.warning('{}: At the end of query expansion'.format(datetime.datetime.now()))
        return search_terms_exp

    def extract_articles(self, urls: List[str]):
        """
        Uses the newspaper library to grab and scrub the html and stuff out the
        of pagesfor the links, puts it in articles variable when it is finished

        Parameters
        ----------
        urls:
            The list of urls in string form that you want to collect and extract
        """
        logger.warning('{}: At the beginning of extracting articles'.format(datetime.datetime.now()))
        queue = Queue()
        # create 20 worker threads
        for x in range(20):
            worker = ArticleWorker(queue, self)
            worker.daemon = True
            worker.start()

        # queue up the article tasks
        for url in urls:
            queue.put(url)

        # wait for them to finish
        queue.join()
        logger.warning('{}: At the middle of extracting articles'.format(datetime.datetime.now()))
        # filter out the failed articles
        successful_articles = list(filter(lambda x: x is not None, self.articles))
        # filter out unique articles, because sometimes urls go to the same place
        texts = []
        unique_articles = []
        for article in successful_articles:
            if article.text not in texts:
                unique_articles.append(article)
                texts.append(article.text)
        logger.warning('{}: At the end of extracting articles'.format(datetime.datetime.now()))
        self.articles = unique_articles

    # TODO - this will probably have a few different extractors (pdf, html, ?)
    def _extract_article(self, url: str) -> Article:
        """This should really only be called by the ArticleWorker, it is the actual
        work that each thread is doing.

        Parameters
        ----------
        url:
            The url it is grabbing

        Returns
        -------
        Article
            The extracted article
        """
        # if the article is a pdf run the pdf parser
        if url.endswith('.pdf'):
            try:
                # download the pdf file
                response = requests.get(url, stream=True)
                # fake an article model for external stuff, but don't use the functionality
                article = Article(url)
                article.text = ''
                with io.BytesIO(response.content) as pdf_file:
                    pdf = PyPDF2.PdfReader(pdf_file)
                    for page in pdf.pages:
                        article.text += page.extract_text()

                if article.text != '':
                    return article
                else:
                    return None
            except PdfReadError:
                pass
            # Dunni did this in the original for when the pdf was scanned, I don't think we need to worry about this atm
            #   # If the above returns as False, we run the OCR library textract to #convert
            #   # scanned/image based PDF files into text
            #   else:
            #   text = textract.process("temp_file.pdf", method='tesseract', language='eng')

        # if the article is a regular web page do this
        else:
            try:
                article = Article(url)
                article.download()
                article.parse()
                # TODO: not sure if we need this, but it does some nlp stuff - article.nlp()
                return article
            except ArticleException:
                pass

        return None
