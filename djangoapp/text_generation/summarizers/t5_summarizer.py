import logging
import unittest
from typing import List

import nltk
import string
from transformers import AutoModelWithLMHead, AutoTokenizer
from transformers import pipeline

from text_generation.models.sentence import Sentence

logger = logging.getLogger(__name__)


class T5Summarizer:
    """This class takes a bunch of articles and creates an abstractive summarization using BART model."""

    def __init__(self, words=125):
        """
            Creates a new object

            Parameters
            ----------
            words
                This is an parameter that define length of the summary by aproximate number of words
        """
        self.words = words

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
        model = AutoModelWithLMHead.from_pretrained("t5-base", cache_dir="./text_generation/summarizers/transformer_cache/")
        tokenizer = AutoTokenizer.from_pretrained("t5-base", cache_dir="./text_generation/summarizers/transformer_cache/")
        # text_input = nltk.tokenize.sent_tokenize(text)

        text_words = nltk.tokenize.word_tokenize(text)
        text_sum = []
        # T5 uses a max_length of 512 so we cut the article to 512 tokens.
        for i in range(0, len(text_words), 512):
            text_input = ' '.join(text_words[i:i+1024])
            inputs = tokenizer.encode("summarize: " + text_input, return_tensors="pt", max_length=512, truncation=True)
            outputs = model.generate(inputs, max_length=self.words, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
            text_output = [tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=False) for g in outputs]
            text_sum.append(text_output[0])
        # print(text_sum)

        final_sum_sents = []
        for i in range(len(text_sum)):
            new_sent = self.sent_remove_punc(text_sum[i])
            final_sum_sents += nltk.tokenize.sent_tokenize(new_sent)
        print(final_sum_sents)

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
