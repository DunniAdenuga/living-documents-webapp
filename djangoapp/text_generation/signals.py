from text_generation.models.document import Document
from text_generation.models.document_history import DocumentHistory
from django.db.models.signals import post_save, pre_save
from django.db import transaction
from django.dispatch import receiver
import logging
import html

logger = logging.getLogger(__name__)


def make_history(instance_id):
    if isinstance(instance_id, int) is True:
        instance = Document.objects.get(id=instance_id)

        all_sentences = instance.sentences.filter(section=None)
        full_text = ''
        for sent in all_sentences:
            full_text = full_text + sent.text + ' '
        all_sections = instance.sections.all()
        for section in all_sections:
            full_text = full_text + f"\n\n<b>{section.heading}</b>\n"
            for sent in section.sentences.all():
                full_text = full_text + sent.text + ' '

        # all_articles = instance.articles.all()
        all_articles = instance.articles.filter(section=None)
        allArticlesText = ''
        for article in all_articles:
            allArticlesText = allArticlesText + article.url + "\n"
        for section in all_sections:
            allArticlesText = allArticlesText + f"\n\n<u>{section.heading}</u>\n"
            for section_article in section.articles.all():
                allArticlesText = allArticlesText + section_article.url + "\n"
        # if full_text != '':

        dh = DocumentHistory.objects.create(text=full_text, articleList=allArticlesText)
        instance.documentHistories.add(dh)


@receiver(post_save, sender=Document)
def make_history_signal(sender, instance, **kwargs):
    transaction.on_commit(lambda: make_history(instance.id))


