import logging
import json
from django.db import models
from pycorenlp import StanfordCoreNLP
from living_documents_server.settings import NLP_SERVER_URL

logger = logging.getLogger(__name__)

nlp_server = StanfordCoreNLP(NLP_SERVER_URL)
# an article has many sentences


class Sentence(models.Model):
    """(Sentence description)"""
    text = models.TextField(blank=True)
    document = models.ForeignKey(
        'Document',
        related_name='sentences',
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    section = models.ForeignKey(
        'Section',
        related_name='sentences',
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    article = models.ForeignKey(
        'Article',
        related_name='sentences',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    position = models.IntegerField()
    # TODO remove this
    url = models.URLField(blank=True, null=True)  # remove url

    is_user_defined = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['position']

    def __hash__(self):
        return hash((self.text))

    def __eq__(self, other):
        return (self.text) == (other.text)

    def __ne__(self, other):
        return self.text != other.text

    def build_triples(self):
        # logger.warn("TRIPLES ARE BEING BUILT: " + self.text)
        from text_generation.models.triple import Triple
        logger.warning("About to run nlp server")
        annotation_json = nlp_server.annotate(
            self.text,
            properties={
                'annotators': 'openie',
                'outputFormat': 'json',
                'openie.triple.strict': 'true'
            })
        logger.warning("Ran nlp server==")
        logger.warning("NLP server output stored in annotation_json")
        # logger.warning(annotation_json)
        annotation_json = json.loads(annotation_json)
        # TODO BVH To speed this up I can move this to document and do a bunch of them at the same time
        if 'sentences' in annotation_json:
            if len(annotation_json['sentences']) > 0:
                if 'openie' in annotation_json['sentences'][0]:
                    triples = annotation_json['sentences'][0]['openie']
                    for triple in triples:
                        new_triple = Triple(
                            sentence=self,
                            subject=triple["subject"],
                            relation=triple["relation"],
                            object=triple["object"])
                        new_triple.save()
                else:
                    logger.warning(f"NO TRIPLES FOUND:\n{self.text}\n\n{annotation_json}")
        else:
            logger.warning("NO RESULTS FROM NLP SERVER")

    def __str__(self):
        """String for representing the Model object."""
        info = "%d: %s" % (self.position, self.text)
        return info
