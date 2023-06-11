from typing import List, Dict, Any

import nltk
from pycorenlp import StanfordCoreNLP

nltk.download('stopwords')
stopwords = set(nltk.corpus.stopwords.words('english'))
my_stops = {'displaystyle', 'mathbf', 'function', 'mathcal', 'alpha', 'boldsymbol'}
stopwords |= my_stops

stemmer = nltk.stem.porter.PorterStemmer()


def process_text(text: str, filter_stopwords: bool = True) -> List[Dict[str, Any]]:
    """Returns a list of stemmed text, filtered of stopwords if flag is true

    :param bool filter_stopwords: Default to false
    :param str text: text to process
    :return List[str:, changed to List[{}]
    """
    processed_text = []
    for word in text.lower().split():
        processed_text_object = {"stemmed_word": "", "processed_word": "", "actual_word": ""}
        processed_word = ''.join(e for e in word if e.isalpha())
        if processed_word not in stopwords or not filter_stopwords:
            processed_text_object["stemmed_word"] = stemmer.stem(processed_word)
            # processed_text.append(stemmer.stem(processed_word))
            processed_text_object["processed_word"] = processed_word
            processed_text_object["actual_word"] = word

        processed_text.append(processed_text_object)
    return processed_text


def process_text_list(words: List[str]) -> List[Dict[str, Any]]:
    processed_text = []
    for word in words:
        processed_text_object = {"stemmed_word": "", "processed_word": "", "actual_word": ""}
        processed_word = ''.join(e for e in word if e.isalpha())
        if processed_word not in stopwords:
            processed_text_object["stemmed_word"] = stemmer.stem(processed_word)
            # processed_text.append(stemmer.stem(processed_word))
            processed_text_object["processed_word"] = processed_word
            processed_text_object["actual_word"] = word

        processed_text.append(processed_text_object)
    return processed_text


def tf_idf_reduce_noun_adjectives(text,
                                  nlp_server: StanfordCoreNLP,
                                  min_cut: float = 0.1,
                                  max_cut: float = 0.9):
    """Takes a document and gets rid of stopwords and counts the frequency
    of nouns and adjectives

    Parameters
    ----------
    text
        the document to get frequency for
    nlp_server
        the instance of the stanford core nlp server
    min_cut
        get rid of words that don't occur much
    max_cut
        get rid of words that occur too much

    Returns
    -------
    Dict[str, int]
        Dictionary with key of words and value of frequence
    """

    freq = {}

    annotated_text = nlp_server.annotate(
        text[:50000],
        properties={
            'annotators': 'tokenize, ssplit, pos',
            'outputFormat': 'json'
        })

    for sentence in annotated_text['sentences']:
        for token in sentence['tokens']:
            # TODO - should I do something a bit more advanced here e.g. use adjective/noun pairs
            # if token['pos'] == 'JJ':
            #     if token['word'] not in self.stopwords:
            #         print(token['word'])
            if token['pos'] in ['NN', 'NNS', 'JJ']:
                if token['word'] not in stopwords:
                    if len(token['word']) > 3:
                        if token['word'] in freq.keys():
                            freq[token['word']] += 1
                        else:
                            freq.setdefault(token['word'], 1)

    max_freq = float(max(freq.values()))
    words_to_delete = []
    for word in freq.keys():
        freq[word] = freq[word] / max_freq
        if freq[word] >= max_cut or freq[word] <= min_cut:
            words_to_delete.append(word)

    for word in words_to_delete:
        del freq[word]

    return freq


def tf_idf_reduce(text,
                  nlp_server: StanfordCoreNLP,
                  min_cut: float = 0.1,
                  max_cut: float = 0.9):
    """Takes a document and gets rid of stopwords and counts the frequency

    Parameters
    ----------
    text
        the document to get frequency for
    nlp_server
        the instance of the stanford core nlp server
    min_cut
        get rid of words that don't occur much
    max_cut
        get rid of words that occur too much

    Returns
    -------
    Dict[str, int]
        Dictionary with key of words and value of frequence
    """

    freq = {}

    annotated_text = nlp_server.annotate(
        text[:50000],
        properties=dict(annotators='tokenize, ssplit, pos', outputFormat='json'))

    for sentence in annotated_text['sentences']:
        for token in sentence['tokens']:
            if token['word'] not in stopwords:
                if len(token['word']) > 3:
                    if token['word'] in freq.keys():
                        freq[token['word']] += 1
                    else:
                        freq.setdefault(token['word'], 1)

    max_freq = float(max(freq.values()))
    words_to_delete = []
    for word in freq.keys():
        freq[word] = freq[word] / max_freq
        if freq[word] >= max_cut or freq[word] <= min_cut:
            words_to_delete.append(word)

    for word in words_to_delete:
        del freq[word]

    return freq
