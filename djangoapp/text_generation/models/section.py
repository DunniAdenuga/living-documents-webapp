import logging
import datetime

from django.db import models
from sklearn.feature_extraction.text import TfidfVectorizer
from text_generation.utilities import process_text

logger = logging.getLogger(__name__)

class Section(models.Model):
    """(Section description)"""

    heading = models.TextField(blank=True)
    position = models.IntegerField(null=True)
    document = models.ForeignKey(
        'Document',
        related_name="sections",
        null=True,
        blank=True,
        on_delete=models.CASCADE)

    def __str__(self):
        """String for representing sections"""
        return f'{self.id}: {self.heading}'

        # TODO this is currently only calculating it for the 'intro' section and not the subsections
    def calculate_tf_idf_scores(self):
        """Mostly an internal function that processes the text in the sentences and vectorizes the tokens, you
        shouldn't need to call this
        :return: None
        """
        texts = []
        for sentence in self.sentences.all():
            process_text_result = process_text(sentence.text)
            list_of_stemmed_words = []
            # get list of stemmed words
            for res in process_text_result:
                list_of_stemmed_words.append(res["stemmed_word"])
            texts.append(' '.join(list_of_stemmed_words))

        tfidf_vec = TfidfVectorizer()
        transformed = tfidf_vec.fit_transform(texts)
        index_value = {i[1]: i[0] for i in tfidf_vec.vocabulary_.items()}
        temp_tf_idf_scores = []
        # set em
        for row in transformed:
            temp_tf_idf_scores.append({
                index_value[column]: value
                for (column, value) in zip(row.indices, row.data)
            })

        self.tf_idf_scores = {}
        for row in temp_tf_idf_scores:
            for token in row.keys():
                self.tf_idf_scores[token] = row[token]

    # TODO this is currently only building it for the 'intro' section and not the subsections
    def build_triple_graph(self) -> None:
        """
        Builds the triple graph for the sentences in the document
        :return: None
        """
        logger.warn("in build-triple graph")
        from text_generation.annotators.triple_graph import TripleGraph
        # logger.warn("self.sentences.all()")
        # logger.warn(self.sentences.all())
        # logger.warn("self.tf_idf_scores")
        # logger.warn(self.tf_idf_scores)
        self.graph = TripleGraph(self.sentences.all(),
                                 self.tf_idf_scores)  # saw this in test
        logger.warning('{}: Triple Graph built for section'.format(datetime.datetime.now()))