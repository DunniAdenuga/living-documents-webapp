import os
import sys
import datetime
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

import logging
from typing import List

import requests
from bs4 import BeautifulSoup
from newspaper import Article

from text_generation.extractors.article_extractor import ArticleExtractor

logger = logging.getLogger(__name__)


class GoogleExtractor(ArticleExtractor):
    """This class takes a query, executes it on Google, and then returns clean
    articles. It inherits from the ArticleExtractor.
    """

    def __init__(self):
        # define our custom blacklist
        self.blacklist = [
            'google', 'facebook', 'amazon', 'twitter', 'youtube', 'pinterest',
            'scholar'
        ]
        super().__init__()

    def get_articles(self, search_terms: List[str], remove_terms: List[str]) -> (List[Article], List[str]):
        """
        This is the main method that you use in this class, it takes a list
        of search terms and returns the text of the top google search results
        and a list of expanded query terms.

        Parameters
        ----------
        search_terms
            A list of search strings, usually single words.

        remove_terms
            A list of terms that must be excluded from search

        Returns
        -------
        List[Article]
            The top search results extracted and cleaned
        List[str]
            The expanded query terms
        """
        urls = self.execute_google_query(search_terms, remove_terms)
        logger.warning('{}: Back from executing google query'.format(datetime.datetime.now()))
        self.extract_articles(urls)
        logger.warning('{}: Back from extracting articles'.format(datetime.datetime.now()))

        # query_expansion
        expanded_terms = self.query_expansion(search_terms)

        return self.articles, expanded_terms

    def execute_google_query(self, search_terms: List[str], remove_terms: List[str]) -> List[str]:
        """Executes a google query that uses a list of search_terms, it returns a list
        of cleaned links

        Parameters
        ----------
        search_terms
            A list of search strings, usually single words.

        remove_terms
            A list of terms that must be excluded from search

        Returns
        -------
        List[strs]
            The top search result urls
        """
        # links to return
        urls = []

        # setup query
        # The query will include all user defined keywords (both positive/added and negative/deleted)
        query = '+'.join(['"' + word + '"' for word in search_terms])

        # add quotes around remove term to ensure removal
        for rem_term in remove_terms:
            query += '-"' + rem_term + '"'

        url = f'http://www.google.com/search?q={query}'
        logger.warning(f'Executing query: {url}')

        # grab from web
        query_results = requests.get(url)
        query_soup = BeautifulSoup(query_results.text, 'lxml')

        # scrape all of the links
        for link in query_soup.find_all('a'):
            link_url = link.get('href')
            if link_url.startswith('/url'):
                if not any(blacklist_element in link_url.lower()
                           for blacklist_element in self.blacklist):
                    # strip off the /url?q= part of string
                    clean_url = link_url[7:]
                    # strip of junk at end...which starts with '&'
                    idx = clean_url.find('&')
                    if idx > -1:
                        clean_url = clean_url[:clean_url.find('&')]
                    urls.append(clean_url)

        return urls

    def execute_google_query_url(self, google_query):
        """
        Same thing as above but with already prepared query
        :param google_query:
        :return: urls from google search
        """
        # links to return
        urls = []

        # grab from web
        query_results = requests.get(google_query)
        query_soup = BeautifulSoup(query_results.text, 'lxml')

        # scrape all of the links
        for link in query_soup.find_all('a'):
            link_url = link.get('href')
            if link_url.startswith('/url'):
                if not any(blacklist_element in link_url.lower()
                           for blacklist_element in self.blacklist):
                    # strip off the /url?q= part of string
                    clean_url = link_url[7:]
                    # strip of junk at end...which starts with '&'
                    idx = clean_url.find('&')
                    if idx > -1:
                        clean_url = clean_url[:clean_url.find('&')]
                    urls.append(clean_url)

        return urls
