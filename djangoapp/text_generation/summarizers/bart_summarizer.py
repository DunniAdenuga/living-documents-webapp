import logging
import unittest
from typing import List

import nltk
import string
from transformers import BartTokenizer, BartForConditionalGeneration, BartConfig
from transformers import pipeline

from text_generation.models.sentence import Sentence

logger = logging.getLogger(__name__)


class BartSummarizer:
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

        model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn', cache_dir="./text_generation/summarizers/transformer_cache/")
        tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn', cache_dir="./text_generation/summarizers/transformer_cache/")
        # text_input = nltk.tokenize.sent_tokenize(text)

        text_words = nltk.tokenize.word_tokenize(text)
        text_input = []
        for i in range(0, len(text_words), 1024):
            text_input.append(' '.join(text_words[i:i+1024]))

        inputs = tokenizer(text_input, max_length=1024, return_tensors='pt', truncation=True, padding=True)
        # Generate Summary
        summary_ids = model.generate(inputs['input_ids'], num_beams=5, max_length=self.words, early_stopping=True)
        text_sum = [tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=False) for g in summary_ids]

        # tokenize the sentences to insert into the data model
        # final_sum_sents = [nltk.tokenize.sent_tokenize(text_sum[i]) for i in range(len(text_sum))]
        final_sum_sents = []
        for i in range(len(text_sum)):
            new_sent = self.sent_remove_punc(text_sum[i])
            final_sum_sents += nltk.tokenize.sent_tokenize(text_sum[i])
        print(final_sum_sents)

        # summarizer = pipeline("summarization")
        # final_sum_sents = summarizer(text, max_length=125, min_length=30, do_sample=False)['summary_text']


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
