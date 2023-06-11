import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
import unittest

import nltk
from pycorenlp import StanfordCoreNLP

from text_generation.utilities import tf_idf_reduce_noun_adjectives
from text_generation.models.sentence import Sentence



class FrequencySummarizer:
    """This class takes a bunch of articles and creates a simple, frequency-based extractive summarization."""

    def __init__(self, min_cut: float = 0.1, max_cut: float = 0.9):
        self._min_cut = min_cut
        self._max_cut = max_cut
        self.nlp_server = StanfordCoreNLP(
            'http://lws-hanrahan.ist.psu.edu:8080')

    def summarize(self, document, article, text: str, n: int = 20, section=None):
        """
        Takes *all* of the corpus in one string for text and returns a
        summarization as list of strings

        Parameters
        ----------
        text:
            The entire corpus in a single string!
        n:
            The number of sentences to return
        document:
            document that is associated
        article:
        section:

        Returns
        -------
        List(str)
            A list of sentences that summarize the corpus
        """
        self._freq = tf_idf_reduce_noun_adjectives(
            text,
            self.nlp_server,
            min_cut=self._min_cut,
            max_cut=self._max_cut)

        ranking = {}
        sentences = nltk.tokenize.sent_tokenize(text)
        for i, sentence in enumerate(sentences):
            for word in nltk.tokenize.word_tokenize(sentence):
                if word in self._freq.keys():
                    if word in ranking.keys():
                        ranking[i] += self._freq[word]
                    else:
                        ranking.setdefault(i, self._freq[word])

        final_sent_ids = []
        top_sentence_indexes = sorted(
            ranking, key=ranking.get, reverse=True)[:n]
        for i in top_sentence_indexes:
            if section:
                new_sent = Sentence(text=sentences[i], position=-1, section=section, article=article)
            else:
                new_sent = Sentence(document=document, text=sentences[i], position=-1, article=article)
            new_sent.save()
            final_sent_ids.append(new_sent.id)
        return final_sent_ids


class TestFrequencySummarizer(unittest.TestCase):
    def setUp(self):
        self.summarizer = FrequencySummarizer(min_cut=0.1, max_cut=0.9)
        self.text_to_summarize = '''Crowdsourcing is a sourcing model in which individuals or organizations obtain goods and services, including ideas and finances, from a large, relatively open and often rapidly-evolving group of internet users; it divides work between participants to achieve a cumulative result. The word crowdsourcing itself is a portmanteau of crowd and outsourcing, and was coined in 2005. As a mode of sourcing, crowdsourcing existed prior to the digital age (i.e. "offline").

Major differences between crowdsourcing and outsourcing include features such as: crowdsourcing comes from a less-specific, more public group (i.e. whereas outsourcing is commissioned from a specific, named group) and; includes a mix of bottom-up and top-down processes. Advantages of using crowdsourcing may include improved costs, speed, quality, flexibility, scalability, or diversity.

Some forms of crowdsourcing, such as in "idea competitions" or "innovation contests" provide ways for organizations to learn beyond the "base of minds" provided by their employees (e.g. LEGO Ideas). Tedious "microtasks" performed in parallel by large, paid crowds (e.g. Amazon Mechanical Turk) are another form of crowdsourcing. It has also been used by not-for-profit organisations and to create common goods (e.g. Wikipedia). The effect of user communication and the platform presentation should be taken into account when evaluating the performance of ideas in crowdsourcing contexts. '''

    def test_summarize(self):
        summarization = self.summarizer.summarize(self.text_to_summarize, 3)
        self.assertTrue(summarization)


if __name__ == '__main__':
    unittest.main()
