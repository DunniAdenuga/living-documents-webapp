import logging
import unittest
import string
import tiktoken

from typing import List
from tenacity import (retry, stop_after_attempt, wait_random_exponential)

import nltk
nltk.download('punkt')
nltk.download('stopwords')
# nltk.download('corpus')

import openai as ai

from .gpt3_info.secrets import OPENAI_KEY
from text_generation.models.sentence import Sentence
from text_generation.models.keyword import Keyword

logger = logging.getLogger(__name__)

def sent_remove_punc(sentence):
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


def getMaxTokensNumber(textPrompt):
    # encoding = tiktoken.get_encoding("cl100k_base")
    encoding = tiktoken.encoding_for_model("text-davinci-003")
    numTokens = len(encoding.encode(textPrompt))
    # numTokens = len(nltk.word_tokenize(textPrompt))

    return 4096 - numTokens

# copied from https://platform.openai.com/docs/guides/rate-limits/error-mitigation
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(7))
def completion_with_backoff(**kwargs):
    return ai.Completion.create(**kwargs)

class GPT3Summarizer:
    """
    This class takes a bunch of articles and creates an abstractive summarization using OPEN AI's GPT3 model.
    """
    def __init__(self, words):
        """
        :param words: Approximate number of words in summary
        """
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
        if "your access" not in str.lower(text) and "temporarily blocked" not in str.lower(text):
            final_sent_ids = []  # keep track of sentence ids to be returned
            model_name = "text-davinci-003"

            # Model has a maximum token count of 4097
            # if len(text.split()) < 3400:
            # logger.warning("OPENAI_KEY")
            # logger.warning(OPENAI_KEY)
            ai.api_key = OPENAI_KEY
            # logger.warning("AI API KEY")
            # logger.warning(ai.api_key)

            logger.warning("In summarize method")

            _promptSummary = ""
            # _promptSummary = f"summarize this text: {text}"
            _promptSummary = text + "\n\nTl;dr"
            # logger.warning(_promptSummary)
            # logger.warning("after prompt summary")

            _promptKeyword = ""
            _promptKeyword = "Extract 6 keywords from this text:\n\n" + text
            # logger.warning(_promptKeyword)
            # logger.warning("after prompt keyword")

            if getMaxTokensNumber(_promptSummary) > 20 and getMaxTokensNumber(_promptKeyword) > 10:
                _maxTokens = self.words * 6
                if section is not None:
                    _maxTokens = self.words * 2

                test = getMaxTokensNumber(_promptSummary)
                logger.warning("amount of tokens left - sum")
                logger.warning(test)
                _maxTokensSum = min(_maxTokens, test)
                logger.warning("amount of tokens chosen - sum")
                logger.warning(_maxTokensSum)
                #
                logger.warning("About to call OpenAI completion - summary")
                text_sum = completion_with_backoff(model=model_name, prompt=_promptSummary, temperature=0,
                                                   max_tokens=_maxTokensSum, top_p=1.0, frequency_penalty=0.8,
                                                   presence_penalty=1)

                logger.warning("text_sum")
                logger.warning(text_sum)

                test2 = getMaxTokensNumber(_promptKeyword)
                logger.warning("amount of tokens left - keyword")
                logger.warning(test2)
                _maxTokensKey = min(50, test2)
                logger.warning("amount of tokens chosen - keyword")
                logger.warning(_maxTokensKey)

                logger.warning("About to call OpenAI completion - keywords")
                text_keywords = completion_with_backoff(model=model_name, prompt=_promptKeyword, temperature=0,
                                                        max_tokens=_maxTokensKey, top_p=1.0, frequency_penalty=0.8,
                                                        presence_penalty=1)

                logger.warning("text_keywords")
                logger.warning(text_keywords)

                if model_name == "text-davinci-002":
                    text_keywords_words = text_keywords["choices"][0].text.split("\n\n")
                    list_of_keywords = text_keywords_words[len(text_keywords_words) - 1].split(",")
                else:
                    text_keywords_words = text_keywords["choices"][0]["text"].split(":")
                    list_of_keywords = text_keywords_words[len(text_keywords_words) - 1].strip("\n").split(", ")

                allKeywordsInDocument = Keyword.objects.filter(document=document)

                if text_keywords["choices"][0].text.strip() != "":
                    for keyword in list_of_keywords:
                        if (str.lower(keyword.strip()) != str.lower(document.title)) and (len(keyword.split(" ")) <= 3):
                            if not allKeywordsInDocument.filter(text=keyword.strip()).exists():
                                Keyword.objects.get_or_create(text=keyword.strip(), document=document)

                # tokenize the sentences to insert into the data model
                temp_sum_sents = text_sum["choices"][0].text.split("\n\n")
                if len(temp_sum_sents) > 1:
                    final_sum_sents = nltk.tokenize.sent_tokenize(temp_sum_sents[len(temp_sum_sents) - 1].strip(": "))
                else:
                    final_sum_sents = nltk.tokenize.sent_tokenize(temp_sum_sents[0].strip(": "))
                # print(final_sum_sents)
                logger.warning("final_sum_sents")
                logger.warning(final_sum_sents)

                logger.warning(final_sum_sents)
                actual_final_sum_sents = []
                for sent in final_sum_sents:
                    if sent not in actual_final_sum_sents:
                        actual_final_sum_sents.append(sent)

                for sent in actual_final_sum_sents:
                    if section is not None:
                        new_sent = Sentence(text=sent, position=-1, section=section, article=article)
                    else:
                        new_sent = Sentence(document=document, text=sent, position=-1, article=article, section=None)
                    new_sent.save()
                    final_sent_ids.append(new_sent.id)

                return final_sent_ids
