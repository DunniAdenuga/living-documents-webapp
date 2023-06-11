import logging

from typing import List, Dict, Set
from datetime import datetime

from rest_framework import serializers

from text_generation.models import Sentence, Document, Section, Triple, Keyword, Article, DocumentHistory
from text_generation.models.suggested_link import SuggestedLink

logger = logging.getLogger(__name__)


class SuggestedLinkSerializer(serializers.ModelSerializer):

    """SuggestedLink serializer"""

    id = serializers.IntegerField(required=False, read_only=False)

    class Meta:
        model = SuggestedLink
        fields = ('id', 'url')

    def create(self, validated_data, document: Document = None):
        """Creates the article from the serialized data, added the document arg

        :param List[] validated_data: all of the data passed by django rest framework
        :param Document document: document that this will be related to, defaults to None
        :return SuggestedLink: the link that was created
        """

        # create the instance and set the fields
        instance = SuggestedLink.objects.create()
        instance.url = validated_data.get('url', instance.url)

        # set the doc if it is not None
        if document:
            instance.document = document
        # save regardless if doc is modified due to fields above
        instance.save()

        return instance

    def update(self, instance, validated_data, document: Document = None):
        """Creates the section from the serialized data, added the document arg

        :param SuggestedLink instance: the instance to run the update on
        :param List[] validated_data: all of the data passed by django rest framework
        :param Document document: document that this will be related to, defaults to None
        """

        instance.url = validated_data.get('url', instance.url)

        # set the doc if it is not None
        if document:
            instance.document = document

        # save regardless if doc is modified due to fields above
        instance.save()

        # handle the sentence part of the data

        return instance

    @staticmethod
    def handle_data(validated_data: Dict, instance):
        """Creates/updates/deletes whatever links need to be that are attached to this instance

        :param validated_data:
        :param instance:
        :return:
        """
        # keep track of new ids for what needs to be removed
        created_ids = set()
        for link_data in validated_data.get('suggested_links'):
            link_serializer = SuggestedLinkSerializer(data=link_data)
            link_serializer.is_valid()

            # this check is necessary if they create a new article
            if 'id' in link_serializer.data.keys():
                link_instance = SuggestedLink.objects.get(pk=link_serializer.data.get('id'))
                link_serializer.update(link_instance, link_data)
            else:
                link_instance = link_serializer.create(link_data)
                created_ids.add(link_instance.id)

            if type(instance) == Document:
                link_instance.document = instance

            link_instance.save()

        SuggestedLinkSerializer.clean_up_removed(validated_data, created_ids, instance)

    @staticmethod
    def clean_up_removed(validated_data: Dict, created_ids: Set, instance):
        """Cleans the link that were deleted from the front end and not included in the data

        :param validated_data: all of the data passed by the framework
        :param created_ids: ids of the things that have been created
        :param instance: whatever instance we are cleaning up could be Sentence, Section, or Document
        """
        # get the set of article ids related to sentence
        all_links = set([link.id for link in instance.suggested_links.all()])
        # get the set of articles in the update dictionary
        updated_links = set([link_data.get('id') for link_data in validated_data.get('suggested_links')])
        # get what is missing because we need to delete them
        ids_to_delete = (all_links - updated_links) - created_ids
        # clean up articles to be deleted
        for to_delete in ids_to_delete:
            SuggestedLink.objects.get(pk=to_delete).delete()


class TripleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Triple
        fields = ('id', 'subject', 'relation', 'object')


class DocumentHistorySerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(required=False, read_only=False)
    timestamp = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S")

    class Meta:
        model = DocumentHistory
        fields = ('id', 'timestamp', 'text', 'articleList')


class KeywordSerializer(serializers.ModelSerializer):
    """Serializer for the Keyword model"""

    id = serializers.IntegerField(required=False, read_only=False)

    class Meta:
        model = Keyword
        fields = ('id', 'text', 'is_user_defined', 'is_deleted')

    def create(self, validated_data, document: Document = None):
        """Creates the sentence from the serialized data, added the document and section arg

        :param List[] validated_data: all of the data passed by django rest framework
        :param Document document: document that this will be related to, defaults to None
        :return Keyword: the keyword that was created
        """
        # Create the sentence with the validated document
        instance = Keyword.objects.create()
        instance.text = validated_data.get('text', instance.text)
        instance.is_user_defined = validated_data.get('is_user_defined', instance.is_user_defined)
        instance.is_deleted = validated_data.get('is_deleted', instance.is_deleted)

        # set the doc if not None
        if document:
            instance.document = document

        instance.save()

        return instance
        

    def update(self, instance, validated_data, document: Document = None):
        """Updates the sentence from the serialized data, added the document and section arg

        :param Sentence instance: the thing to update
        :param List[] validated_data: all of the data passed by django rest framework
        :param Document document: document that this will be related to, defaults to None
        :param Section section: section that this will be related to, defaults to None
        :return Sentence: the sentence that was updated
        """
        instance.text = validated_data.get('text', instance.text)
        instance.is_user_defined = validated_data.get('is_user_defined', instance.is_user_defined)
        instance.is_deleted = validated_data.get('is_deleted', instance.is_deleted)

        # set the doc if not None
        if document:
            instance.document = document

        instance.save()

        return instance

    @staticmethod
    def handle_data(validated_data: Dict, instance):
        # key track of new ids for what doesn't need to be removed later on
        created_ids = set()
        # update existing keywords and create any new ones that are new
        for keyword_data in validated_data.get('keywords'):
            keyword_serializer = KeywordSerializer(data=keyword_data)
            keyword_serializer.is_valid()
            # check if it exists already
            if 'id' in keyword_serializer.data.keys():
                keyword_instance = Keyword.objects.get(pk=keyword_serializer.data.get('id'))
                keyword_serializer.update(keyword_instance, keyword_data, document=instance)
            else:
                keyword_instance = keyword_serializer.create(keyword_data, document=instance)
                created_ids.add(keyword_instance.id)

        KeywordSerializer.clean_up_removed(validated_data=validated_data, created_ids=created_ids, instance=instance)

    @staticmethod
    def clean_up_removed(validated_data: Dict, created_ids: Set, instance):
        # get entire set of keywords related to doc
        all_keywords = set([keyword.id for keyword in instance.keywords.all()])
        # get the keywords that were updated
        updated_keywords = set([keyword_data.get('id') for keyword_data in validated_data.get('keywords')])
        # get the keywords that we need to delete
        ids_to_delete = (all_keywords - updated_keywords) - created_ids

        for id in ids_to_delete:
            Keyword.objects.get(pk=id).delete()


class SentenceSerializer(serializers.ModelSerializer):
    """Serializer for the Sentence model"""

    id = serializers.IntegerField(required=False, read_only=False)

    class Meta:
        model = Sentence
        fields = ('id', 'text', 'position', 'is_user_defined', 'is_deleted')

    def create(self, validated_data, document: Document = None, section: Section = None, article: Article = None):
        """Creates the sentence from the serialized data, added the document and section arg

        :param List[] validated_data: all of the data passed by django rest framework
        :param Document document: document that this will be related to, defaults to None
        :param Section section: section that this will be related to, defaults to None
        :param Article article: article that this will be related to, defaults to None
        :return Sentence: the sentence that was created
        """

        # Create the sentence with the validated document
        instance = Sentence.objects.create(text=validated_data.get('text'),
                                           position=validated_data.get('position'),
                                           is_user_defined=validated_data.get('is_user_defined'),
                                           is_deleted=validated_data.get('is_deleted'))

        # set the doc and section if they aren't None
        if document:
            instance.document = document
        if section:
            instance.section = section
        if article:
            instance.article = article

        # ArticleSerializer.handle_data(validated_data, instance)

        instance.save()

        return instance

    def update(self, instance, validated_data: List, document: Document = None, section: Section = None, article: Article = None):
        """Updates the sentence from the serialized data, added the document and section arg

        :param Sentence instance: the thing to update
        :param List[] validated_data: all of the data passed by django rest framework
        :param Document document: document that this will be related to, defaults to None
        :param Section section: section that this will be related to, defaults to None
        :param Article article: article that this will be related to, defaults to None
        :return Sentence: the sentence that was updated
        """
        instance.text = validated_data.get('text')
        instance.position = validated_data.get('position')
        instance.is_user_defined = validated_data.get('is_user_defined')
        instance.is_deleted = validated_data.get('is_deleted')

        # set the doc and section if they aren't None
        if document:
            instance.document = document
        if section:
            instance.section = section
        if article:
            instance.article = article

        # go ahead and do an update since we likely changed something above
        instance.save()
        # ArticleSerializer.handle_data(validated_data, instance)

        return instance

    @staticmethod
    def handle_data(validated_data: Dict, instance):
        # keep track of new ids for what needs to be removed
        created_ids = set()
        # update existing sentences that aren't in sections, create any new ones that aren't in there
        for sentence_data in validated_data.get('sentences'):
            sentence_serializer = SentenceSerializer(data=sentence_data)
            sentence_serializer.is_valid()
            # check if it exists already
            # if 'id' in sentence_serializer.data.keys():
            logger.warning("sentence_serializer.data")
            logger.warning(sentence_serializer.data)
            idMadeSense = True

            if sentence_serializer.data.get('id'):
                try:
                    sentence_instance = Sentence.objects.get(pk=sentence_serializer.data.get('id'))
                    sentence_serializer.update(instance=sentence_instance, validated_data=sentence_data)
                except Sentence.DoesNotExist:
                    sentence_instance = None
            else:
                sentence_instance = sentence_serializer.create(sentence_data)
                created_ids.add(sentence_instance.id)

            if sentence_instance is not None:
                if type(instance) == Document:
                    sentence_instance.document = instance
                elif type(instance) == Section:
                    sentence_instance.section = instance
                elif type(instance) == Article:
                    sentence_instance.article = instance
                sentence_instance.save()

        SentenceSerializer.clean_up_removed(validated_data, created_ids, instance)

    @staticmethod
    def clean_up_removed(validated_data: Dict, created_ids: Set, instance):
        # get the entire set of sentence ids that are currently related to document
        all_sentences = set([sentence.id for sentence in instance.sentences.filter()])
        # empty_sentences = set([sentence.id for sentence in instance.sentences.filter(section=None, is_deleted=True)])
        empty_sentences = set([sentence.id for sentence in instance.sentences.filter(text='')])
        # get the set of sentences that were included in update dictionary
        updated_sentences = set([sentence_data.get('id') for sentence_data in validated_data.get('sentences')])
        # get the sentences that we need to delete by getting set difference
        ids_to_delete = (all_sentences - updated_sentences) - created_ids
        # clean up the sentences that need to be deleted
        for to_remove in empty_sentences:
            Sentence.objects.get(pk=to_remove).delete()
        for to_remove in ids_to_delete:
            Sentence.objects.get(pk=to_remove).delete()


class ArticleSerializer(serializers.ModelSerializer):
    """Article serializer"""

    id = serializers.IntegerField(required=False, read_only=False)
    sentences = SentenceSerializer(many=True, read_only=False)

    class Meta:
        model = Article
        fields = ('id', 'text', 'url', 'sentences')

    def create(self, validated_data, document: Document = None, section: Section = None):
        """Creates the article from the serialized data, added the document arg

        :param List[] validated_data: all of the data passed by django rest framework
        :param Document document: document that this will be related to, defaults to None
        :param Section section: section that this will be related to, defaults to None
        :return Article: the article that was created
        """

        # create the instance and set the fields
        instance = Article.objects.create()
        instance.text = validated_data.get('text', instance.text)
        instance.url = validated_data.get('url', instance.url)

        # set the doc if it is not None
        if document:
            instance.document = document
        if section:
            instance.section = section
        # save regardless if doc is modified due to fields above
        instance.save()

        # handle the sentence part of the data
        SentenceSerializer.handle_data(validated_data=validated_data, instance=instance)

        return instance

    def update(self, instance, validated_data, document: Document = None, section: Section = None):
        """Creates the section from the serialized data, added the document arg

        :param Article instance: the instance to run the update on
        :param List[] validated_data: all of the data passed by django rest framework
        :param Document document: document that this will be related to, defaults to None
        :param Section section: section that this will be related to, defaults to None
        :return Article: the article that was created
        """

        instance.text = validated_data.get('text', instance.text)
        instance.url = validated_data.get('url', instance.url)

        # set the doc if it is not None
        if document:
            instance.document = document
        if section:
            instance.section = section
        # save regardless if doc is modified due to fields above
        instance.save()

        # handle the sentence part of the data
        SentenceSerializer.handle_data(validated_data=validated_data, instance=instance)

        return instance

    @staticmethod
    def handle_data(validated_data: Dict, instance):
        """Creates/updates/deletes whatever articles need to be that are attached to this instance

        :param validated_data:
        :param instance:
        :return:
        """
        # keep track of new ids for what needs to be removed
        created_ids = set()
        for article_data in validated_data.get('articles'):
            article_serializer = ArticleSerializer(data=article_data)
            article_serializer.is_valid()

            # this check is necessary if they create a new article
            if 'id' in article_serializer.data.keys():
                try:
                    article_instance = Article.objects.get(pk=article_serializer.data.get('id'))
                    article_serializer.update(article_instance, article_data)
                except Article.DoesNotExist:
                    article_instance = None
            else:
                article_instance = article_serializer.create(article_data)
                created_ids.add(article_instance.id)

            if article_instance is not None:
                if type(instance) == Document:
                    article_instance.document = instance
                elif type(instance) == Section:
                    article_instance.section = instance
                article_instance.save()

        ArticleSerializer.clean_up_removed(validated_data, created_ids, instance)

    @staticmethod
    def clean_up_removed(validated_data: Dict, created_ids: Set, instance):
        """Cleans the articles that were deleted from the front end and not included in the data

        :param validated_data: all of the data passed by the framework
        :param created_ids: ids of the things that have been created
        :param instance: whatever instance we are cleaning up could be Sentence, Section, or Document
        """
        # get the set of article ids related to sentence
        all_articles = set([article.id for article in instance.articles.all()])
        # get the set of articles in the update dictionary
        updated_articles = set([article_data.get('id') for article_data in validated_data.get('articles')])
        # get what is missing because we need to delete them
        ids_to_delete = (all_articles - updated_articles) - created_ids
        # clean up articles to be deleted
        for to_delete in ids_to_delete:
            Article.objects.get(pk=to_delete).delete()


class SectionSerializer(serializers.ModelSerializer):
    """Section serializer"""

    id = serializers.IntegerField(required=False, read_only=False)
    sentences = SentenceSerializer(many=True, read_only=False)
    articles = ArticleSerializer(many=True, read_only=False)

    class Meta:
        model = Section
        fields = ('id', 'heading', 'position', 'sentences', 'articles')

    def create(self, validated_data, document: Document = None):
        """Creates the section from the serialized data, added the document arg

        :param List[] validated_data: all of the data passed by django rest framework
        :param Document document: document that this will be related to, defaults to None
        :return Section: the section that was created
        """

        # create the instance and set the fields
        instance = Section.objects.create()
        instance.heading = validated_data.get('heading', instance.heading)
        instance.position = validated_data.get('position', instance.position)

        # set the doc if it is not None
        if document:
            instance.document = document
        # save regardless if doc is modified due to fields above
        instance.save()

        # handle the sentence part of the data
        SentenceSerializer.handle_data(validated_data=validated_data, instance=instance)
        # handle the article part of the data
        ArticleSerializer.handle_data(validated_data=validated_data, instance=instance)

        return instance

    def update(self, instance, validated_data, document: Document = None):
        """Creates the section from the serialized data, added the document arg

        :param Section instance: the instance to run the update on
        :param List[] validated_data: all of the data passed by django rest framework
        :param Document document: document that this will be related to, defaults to None
        :return Section: the section that was created
        """
        instance.heading = validated_data.get('heading', instance.heading)
        instance.position = validated_data.get('position', instance.position)

        # set the doc if it is not None
        if document:
            instance.document = document
        # save regardless if doc is modified due to fields above
        instance.save()

        # handle the sentence part of the data
        SentenceSerializer.handle_data(validated_data=validated_data, instance=instance)
        # handle the article part of the data
        ArticleSerializer.handle_data(validated_data=validated_data, instance=instance)

        return instance

    @staticmethod
    def handle_data(validated_data: Dict, instance):
        # keep track of new ids for what needs to be removed
        created_ids = set()
        # update existing sections, create any new ones that aren't in there
        for section_data in validated_data.get('sections'):
            section_serializer = SectionSerializer(data=section_data)
            section_serializer.is_valid()
            # check if it exists already
            if 'id' in section_serializer.data.keys():
                section_instance = Section.objects.get(pk=section_serializer.data.get('id'))
                section_serializer.update(section_instance, section_data, document=instance)
            else:
                section_instance = section_serializer.create(section_data, document=instance)
                created_ids.add(section_instance.id)

        SectionSerializer.clean_up_removed(validated_data=validated_data, created_ids=created_ids, instance=instance)

    @staticmethod
    def clean_up_removed(validated_data: Dict, created_ids: Set, instance):
        # get entire set of sections related to doc
        all_sections = set([section.id for section in instance.sections.all()])
        # what was updated
        updated_sections = set([section_data.get('id') for section_data in validated_data.get('sections')])
        # what is the difference
        section_ids_to_delete = (all_sections - updated_sections) - created_ids
        # delete what is left
        for to_remove in section_ids_to_delete:
            Section.objects.get(pk=to_remove).delete()


class DocumentSerializer(serializers.ModelSerializer):
    """Document serializer for rest framework stuff"""
    id = serializers.IntegerField(required=False, read_only=False)
    title = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    author = serializers.CharField(
        required=True, allow_blank=True, max_length=100)
    sections = SectionSerializer(many=True)
    sentences = SentenceSerializer(many=True)
    keywords = KeywordSerializer(many=True)
    articles = ArticleSerializer(many=True, read_only=False)
    suggested_links = SuggestedLinkSerializer(many=True, read_only=False)
    documentHistories = DocumentHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ('id', 'title', 'author', 'sections', 'sentences', 'keywords',
                  'articles', 'suggested_links', 'documentHistories')

    def create(self, validated_data):
        """Creates the document from the serialized data, added the document arg

        :param List[] validated_data: all of the data passed by django rest framework
        :return Document : the document that was created
        """
        # create the document and set some fields
        instance = Document.objects.create()
        instance.title = validated_data.get('title', instance.title)
        instance.author = validated_data.get('author', instance.author)
        instance.save()

        SectionSerializer.handle_data(validated_data=validated_data, instance=instance)
        SentenceSerializer.handle_data(validated_data=validated_data, instance=instance)
        KeywordSerializer.handle_data(validated_data=validated_data, instance=instance)
        ArticleSerializer.handle_data(validated_data=validated_data, instance=instance)
        SuggestedLinkSerializer.handle_data(validated_data=validated_data, instance=instance)
        # DocumentHistorySerializer.handle_data(validated_data=validated_data, instance=instance)

        return instance

    def update(self, instance, validated_data):
        """Creates the document from the serialized data, added the document arg

        :param Document instance: existing document to update
        :param List[] validated_data: all of the data passed by django rest framework
        :return Document : the document that was created
        """
        # update the fields
        instance.title = validated_data.get('title', instance.title)
        instance.author = validated_data.get('author', instance.author)
        instance.save()
        
        SectionSerializer.handle_data(validated_data=validated_data, instance=instance)
        SentenceSerializer.handle_data(validated_data=validated_data, instance=instance)
        KeywordSerializer.handle_data(validated_data=validated_data, instance=instance)
        ArticleSerializer.handle_data(validated_data=validated_data, instance=instance)
        SuggestedLinkSerializer.handle_data(validated_data=validated_data, instance=instance)
        # DocumentHistorySerializer.handle_data(validated_data=validated_data, instance=instance)

        return instance
