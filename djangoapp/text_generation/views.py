# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import logging
import sys
import threading
sys.setrecursionlimit(10**7)  # max depth of recursion
threading.stack_size(2**27)

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from nltk.stem.porter import *
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny

from text_generation.models import Document, Section, Sentence, Article, Keyword
from text_generation.serializers import DocumentSerializer

logger = logging.getLogger(__name__)


class TripleGraphViewSet(viewsets.ModelViewSet):
    """
    Return document graph in JSON format (root and children) to frontend
    """
    @api_view(['GET', 'POST'])
    def get_tree_data(request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return HttpResponse(status=404)
        if request.method == 'GET':
            logger.warn("before tfidf scores")
            document.calculate_tf_idf_scores(useAllSentences=True)
            logger.warn("before trying build graph")
            document.build_triple_graph(useAllSentences=True)
            # if document.graph is None:
            #     document.build_triple_graph()
            logger.warn("after trying build graph")
            graph_arr = []
            visited = []

            def get_tree_help(node, level):
                # node.children
                if node not in visited:
                    ch_obj = {"name": str(node), "children": []}
                    visited.append(node)
                    for n in node.children:
                        ch_obj["children"].append(get_tree_help(n, level+1))
                    return ch_obj
                else:
                    return {"name": str(node), "children": []}

            i = 0
            for root in document.graph.roots:
                # if root.speech_type != "RELATION":
                graph_arr.append({"name": str(root), "children": []})
                visited.append(root)

                # parent = str(root)
                for child in root.children:
                    # graph_arr[i]["parent"] = parent
                    graph_arr[i]["children"].append(get_tree_help(child, 1))

                i = i + 1

            logger.warning("Graph Array: " + str(graph_arr))
            logger.warning("Confirmation: I'm in my string era. Not anymore o")
            return JsonResponse({'doc_graph': graph_arr})
            # return JsonResponse({"graph_string_version": str(document.graph)})
            # return JsonResponse({'doc_graph': graph_arr, "graph_string_version": str(document.graph)})

    
class SectionViewSet(viewsets.ModelViewSet):
    # only send section details, user has to save from front end
    @api_view(['GET', 'POST'])
    def generate_new_section(request, summarizer, pk):
        """
        Adds new Section to Document and returns section details and summary
        """
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return HttpResponse(status=404)
        if request.method == 'POST':
            data = JSONParser().parse(request)
            num_sections = len(document.sections.all())
            section = Section.objects.create(
                document=document,
                position=num_sections,
                heading=data['heading'])

            logger.warning("New Section Summary about to start")

            document.generate_section_summarization(section=section, summarizer=summarizer)

            logger.warning("Added Sentences to Section and Document")

            serializer = DocumentSerializer(document)
            return JsonResponse(serializer.data)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    @api_view(['GET', 'POST', 'DELETE'])
    def doc_delete(request, pk):
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return HttpResponse(status=404)
        if request.method == 'DELETE':
            Sentence.objects.filter(document=doc).delete()
            Section.objects.filter(document=doc).delete()
            Article.objects.filter(document=doc).delete()
            Keyword.objects.filter(document=doc).delete()

            doc.delete()
            document_list = [(DocumentSerializer(doc_)).data for doc_ in list(Document.objects.all())]
            return JsonResponse({'data': document_list})

    @api_view(['GET', 'POST', 'DELETE'])
    def generate_user_summary(request, summarizer, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return HttpResponse(status=404)
        if request.method == 'GET':
            try:
                if len(document.articles.all()) > 0:
                    document.generate_summarization(get_articles=False, summarizer=summarizer)
                else:
                    document.generate_summarization(get_articles=True, summarizer=summarizer)
            except ValueError:
                logger.warning('Value Error in summarization')
                pass
            logger.warning('Finishing get summary from view')
            serializer = DocumentSerializer(document)
            return JsonResponse(serializer.data)

    # get text for new section that's user defined
    @csrf_exempt
    @api_view(['POST'])
    def get_new_section_text(request, summarizer,  pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return HttpResponse(status=404)
        if request.method == 'POST':
            data = JSONParser().parse(request)
            try:
                section = Section.objects.get(heading=data['section_heading'], document=document)
            except Section.DoesNotExist:
                section = Section.objects.create(
                    document=document,
                    heading=data['section_heading'])
            if len(section.articles.all()) > 0:
                document.generate_section_summarization(section=section, summarizer=summarizer, get_articles=False)
            else:
                document.generate_section_summarization(section=section, summarizer=summarizer, get_articles=True)

            document.save()

            serializer = DocumentSerializer(document)
            return JsonResponse(serializer.data)

    @api_view(['GET', 'POST'])
    def change_word_using_triple_graph(request, pk):
        try:
            document = Document.objects.get(pk=pk)
            logger.warn('here')
        except Document.DoesNotExist:
            return HttpResponse(status=404)

        if request.method == 'POST':
            document.calculate_tf_idf_scores()
            document.build_triple_graph()
            data = JSONParser().parse(request)
            old_word = data['old_word'].lower()
            new_word = data['new_word'].lower()

        # get new sentences (IDs) with new_word doing more targeted search
        new_word_model = document.change_word_text(old_word, new_word)  # change this 100
        logger.warn(new_word_model)
        logger.warn("Received new text")
        new_text_triples = []
        # sents = []
        for id_sent in new_word_model:
            logger.warn("Building Triples...")
            sentence_obj = Sentence.objects.get(pk=id_sent)
            sentence_obj.build_triples()
            logger.warn("Built Triples...")
            triples = sentence_obj.triple_set.all()
            # logger.warn(triples)
            new_text_triples.append(triples)
            # sents.append(sent)

        stemmer = PorterStemmer()

        tokenized_old_word = stemmer.stem(old_word)
        # logger.warn("tokenize-d word: " + tokenized_old_word)
        # logger.warn(document.graph._token_lookup)
        for node in document.graph._token_lookup:
            if tokenized_old_word == str(node):
                logger.warn("found in token lookup")
                # for sent in node.sentences:
                #     document.graph.delete_sentence(sent)
                # should be empty
                rem_sent = [document.graph.delete_sentence(sent) for sent in list(node.sentences)]
                # sent.delete()  # from django
                logger.warn("Old Node sentences deleted")
                break

        i = 0  # loop variable
        for one_sent_triples in new_text_triples:
            for one_sent_triple in one_sent_triples:
                document.graph.insert_triple(sentence=Sentence.objects.get(pk=new_word_model[i]),
                                             triple=one_sent_triple)
            i = i + 1

        # document.graph.sentence_ordering_output()
        output_summary = document.graph.sentence_ordering_output()

        def copy_sentences(new_list_sentences):
            new_sentences = []
            for sent56 in new_list_sentences:
                new_sent = Sentence(text=sent56.text, position=sent56.position)
                new_sent.save()
                new_sentences.append(new_sent.id)
            return new_sentences

        logger.warning('{}: Retaining sentences that were ordered after change word order'.format(
            datetime.datetime.now()))
        doc_sentences = copy_sentences(output_summary)
        Sentence.objects.filter(document=document).delete()
        for doc_sent_id in doc_sentences:
            new_sent_9 = Sentence.objects.get(pk=doc_sent_id)
            new_sent_9.document = document
            new_sent_9.save()

        document.save()
        logger.warn('Changed word summary being sent')
        serializer = DocumentSerializer(document)
        return JsonResponse(serializer.data)
