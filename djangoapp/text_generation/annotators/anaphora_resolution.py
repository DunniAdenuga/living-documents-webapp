from pycorenlp import StanfordCoreNLP
import unittest
from typing import Dict
import pprint
'''
This doesn't do well if origin_text =
                  'Mary had a little lamb. Its fleece was white as snow.'\
                  'Everywhere that Mary went, it was sure to go.'\
                  'He followed her to school one day, which was against the rule.' \
                  'It made the children laugh and play to see a lamb at school.' \
                  'And so the teacher sent him out, but still he lingered near.' \
                  'And waited patiently til Mary did appear.'
Runs into errors with the keys in update_text:
KeyError: string indices cannot be integers
'''


class Resolver:
    nlp_server = StanfordCoreNLP('http://localhost:9000')

    def __init__(self, origin_text):
        """
        :param origin_text: the original text that we want to work with
        """
        self.text = origin_text
        self.nlp_dict = self.nlp_server.annotate(
            self.text,
            properties={
                'annotators': 'coref',
                'outputFormat': 'json'
            })

    def update_text(self) -> str:
        """
        This is called explicitly.

        :return: self.text which will be completely updated in the following functions
        """
        for key in self.nlp_dict['corefs']:
            # *** not using .keys() here because .keys() requires an integer, and the keys are strings
            coref = self.nlp_dict['corefs'][key]
            replacement_token = coref[0]
            tokens_to_replace = coref[1:]
            # Here we grab the coref dictionary using the key we get from iterating
            for token_to_replace in tokens_to_replace:
                self.text = self._replace_token(token_to_replace,
                                                replacement_token)
        return self.text

    def _replace_token(self, token_to_replace: Dict,
                       replacement_token: Dict) -> str:
        """This is an internal function that calls _replace_slice using input from update_text.

         :param token_to_replace: this is a dictionary with information about the token
         :param replacement_token: this is a dictionary with information about the token we are replacing with
         :return: the updated text
         """
        sentence_dict = self.nlp_dict['sentences'][token_to_replace['sentNum']
                                                   - 1]
        token_info = sentence_dict['tokens'][token_to_replace['startIndex']
                                             - 1]
        # this should change the text
        self.text = self._replace_slice(self.text, replacement_token['text'],
                                        token_info['characterOffsetBegin'],
                                        token_info['characterOffsetEnd'])
        return self.text

    def _replace_slice(self, text: str, replacement_text: str,
                       start_index_to_replace: int,
                       end_index_to_replace: int) -> str:
        """
        This is internal. Takes in the text and keeps it the same up to the start_index, then puts in the replacement text,
        then puts in the remaining text starting from the end_index of the replaced text.

        :param text: the current text we are working with, sent as self.text from _replace_token
        :param replacement_text: the 'text' value found in the token's dictionary
        :param start_index_to_replace: start index value found in the token's dictionary
        :param end_index_to_replace: end index value found in the token's dictionary
        :return:
        """
        return f'{text[:start_index_to_replace]}{replacement_text}{text[end_index_to_replace:]}'


#  T E S T S
class TestResolver(unittest.TestCase):
    def setUp(self):
        origin_text = 'Mary had a little lamb. Its fleece was white as snow. ' \
                      'Everywhere that Mary went, it was sure to go.'
        self.resolver = Resolver(origin_text)

    def test_update_text(self):
        result = self.resolver.update_text()
        self.assertEqual(
            result,
            "Mary had a little lamb. a little lamb fleece was white as snow. "
            "Everywhere that Mary went, a little lamb was sure to go.")

    def test_replace_token(self):
        replacement_token = self.resolver.nlp_dict['corefs']['6'][0]
        # "Its"
        token_to_replace = self.resolver.nlp_dict['corefs']['6'][1]
        self.resolver.text = self.resolver._replace_token(
            token_to_replace, replacement_token)
        # print(self.resolver.text)
        self.assertEqual(
            self.resolver.text,
            "Mary had a little lamb. a little lamb fleece was white as snow. "
            "Everywhere that Mary went, it was sure to go.")

    def test_replace_slice(self):
        replacement = 'A little lamb'

        sentence = 'Its fleece was white as snow.'
        to_replace = 'Its'
        start_index = sentence.find(to_replace)
        end_index = start_index + len(to_replace)
        result = self.resolver._replace_slice(sentence, replacement,
                                              start_index, end_index)

        self.assertEqual(f'{replacement} fleece was white as snow.', result)

        sentence = 'Some thought its fleece was white as snow.'
        to_replace = 'its'
        start_index = sentence.find(to_replace)
        end_index = start_index + len(to_replace)
        result = self.resolver._replace_slice(sentence, replacement,
                                              start_index, end_index)

        self.assertEqual(
            f'Some thought {replacement} fleece was white as snow.', result)

        sentence = 'Some thought fleece was white as snow its'
        to_replace = 'its'
        start_index = sentence.find(to_replace)
        end_index = start_index + len(to_replace)
        result = self.resolver._replace_slice(sentence, replacement,
                                              start_index, end_index)

        self.assertEqual(
            f'Some thought fleece was white as snow {replacement}', result)
