import logging
import unittest
from typing import List

import nltk
from summa import summarizer

from text_generation.models.sentence import Sentence

logger = logging.getLogger(__name__)


class TextrankSummarizer:
    """This class takes a bunch of articles and creates an extractive summarization based on textrank algorithm."""

    def __init__(self, ratio=0, words=0):
        """
            Creates a new object

            Parameters
            ----------
            ratio
                This is an parameter that define length of the summary as a proportion of the text
            words
                This is an parameter that define length of the summary by aproximate number of words
        """
        self.ratio = ratio
        self.words = words

    def summarize(self, document, article, text: str,  section=None) -> List[int]:
        """
        Does the actual work of the summarization
        :param document: This is of type document in the models.py
        :param text: the text to summarize
        :param article: the url that the text came from
        :param section: the section (if there is one) to add the sentence to
        :return: list of the ids of the sentences that were added
        """

        # summarization without paragraph split
        if self.ratio > 0:
            text_sum = summarizer.summarize(text, ratio=self.ratio)
        elif self.words > 0:
            text_sum = summarizer.summarize(text, words=self.words)
        else:
            text_sum = summarizer.summarize(text)

        # tokenize the sentences to insert into the data model
        final_sum_sents = nltk.tokenize.sent_tokenize(text_sum)
        print(final_sum_sents)

        final_sent_ids = []  # keep track of sentence ids
        for sent in final_sum_sents:
            if section is not None:
                new_sent = Sentence(text=sent, position=-1, section=section, article=article)
                # section.sentence_set.add(new_sent)
                # section.save()
            else:
                new_sent = Sentence(document=document, text=sent, position=-1, article=article)
            new_sent.save()
            final_sent_ids.append(new_sent.id)

        return final_sent_ids
