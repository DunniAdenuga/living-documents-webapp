import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

import unittest
from typing import List

import requests
from bs4 import BeautifulSoup
from newspaper import Article

from text_generation.extractors.article_extractor import ArticleExtractor


class WikipediaExtractor(ArticleExtractor):
    """This class takes a query, executes it on wikipedia search, and then
    returns clean articles. It inherits from the ArticleExtractor.
    """

    def __init__(self):
        super().__init__()

    def get_articles(self, search_terms: List[str]) -> List[Article]:
        """
        This is the main method that you use in this class, it takes a list
        of search terms and returns the text of the top wikipedia search results

        Parameters
        ----------
        search_terms
            A list of search strings, usually single words.

        Returns
        -------
        List[Article]
            The top search results extracted and cleaned
        """
        urls = self.execute_wikipedia_query(search_terms)
        self.extract_articles(urls)

        return self.articles

    def execute_wikipedia_query(self, search_terms: List[str]) -> List[str]:
        """Executes a wikipedia search that uses a list of search_terms, it
        returns a list of cleaned links

        Parameters
        ----------
        search_terms
            A list of search strings, usually single words.

        Returns
        -------
        List[strs]
            The top search result urls
        """
        # links to return
        urls = []

        query = '+'.join(search_terms)
        url = f'https://en.wikipedia.org/w/index.php?search={query}&title=Special:Search&fulltext=1'

        # grab from web
        query_results = requests.get(url)
        query_soup = BeautifulSoup(query_results.text, 'lxml')

        # scrape all of the links
        for link in query_soup.find_all('a'):
            link_url = link.get('href')
            if link_url and link_url.startswith('/wiki'):
                if link_url.find('Help:') < 0:
                    urls.append(f'https://en.wikipedia.org{link_url}')

        return urls[:10]


class TestWikipediaExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = WikipediaExtractor()

    def test_execute_wikipedia_query(self):
        search_terms = [
            'Crowdsourcing',
        ]
        urls = self.extractor.execute_wikipedia_query(search_terms)
        self.assertEqual(len(urls), 10)

    def test_extract_articles(self):
        search_terms = [
            'Crowdsourcing',
        ]
        urls = self.extractor.execute_wikipedia_query(search_terms)
        self.extractor.extract_articles(urls)
        self.assertGreater(len(self.extractor.articles), 0)


if __name__ == '__main__':
    unittest.main()
