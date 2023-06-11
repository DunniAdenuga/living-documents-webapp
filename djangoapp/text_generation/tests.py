from collections import OrderedDict

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from text_generation.extractors.article_extractor import ArticleExtractor
from text_generation.extractors.google_extractor import GoogleExtractor
from .models import Sentence, Document, Section, Keyword, Article
from .serializers import DocumentSerializer, ArticleSerializer, SentenceSerializer


class DeepLearningIntegrationTest(TestCase):
    def test_pytorch_version(self):
        import torch
        version = torch.__version__
        self.assertTrue(version)


class DocumentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')

    def tearDown(self):
        self.user.delete()

    def test_delete(self):
        numDocuments = len(Document.objects.all())
        self.document = Document.objects.create(title='Crowdsourcing')
        self.assertEqual(len(Document.objects.all()), numDocuments + 1)
        self.document.delete()
        self.assertEqual(len(Document.objects.all()), numDocuments)

    def test_generate_summarization(self):
        self.document = Document.objects.create(title='Machine Learning')
        self.document.generate_summarization()
        self.assertTrue(len(self.document.articles.all()) > 0)
        self.assertTrue(len(self.document.tf_idf_scores.keys()) > 0)

        self.document = Document.objects.get(pk=self.document.id)
        self.assertTrue(len(self.document.sentences.all()) > 0)
        self.assertEqual(self.document.sentences.all()[0].position, 0)

    def test_get_new_section(self):
        self.document = Document.objects.create(title='Crowdsourcing and Ethics')
        self.document.generate_summarization()
        pre_len = len(self.document.sentences.all())
        self.section = Section.objects.create(heading='Machine Learning')
        self.document.generate_section_summarization(self.section)
        self.assertTrue(self.section.sentences.all().count() > 0)

    def test_remove_repeat_sentence(self):
        self.document = Document.objects.create(title='Mary')
        sentence = Sentence.objects.create(
            text='Mary had a little lamb.', document=self.document, position=0)
        sentence_dup = Sentence.objects.create(
            text='Mary had a little lamb.', document=self.document, position=1)
        sentence_not_dup = Sentence.objects.create(
            text='Mary did not have a little lamb.', document=self.document, position=2)
        self.document._remove_repeat_sentences()
        self.assertEqual(self.document.sentences.all().count(), 2)

    def test_build_triple_graph(self):
        self.document = Document.objects.create(title="Crowdsourcing")
        self.document.generate_summarization()
        self.document.build_triple_graph()

    def test_query_expansion(self):
        self.document = Document.objects.create(title="ipad")
        self.document.generate_summarization()

    def test_user_defined_summaries(self):
        self.document = Document.objects.create(title="Education")
        self.document.articles.create(
            url='https://www.brookings.edu/blog/brown-center-chalkboard/2016/02/08/can-crowdsourcing-be-ethical/')
        self.document.articles.create(url='https://rossdawson.com/blog/debate-the-ethics-of-crowdsourcing/')
        self.document.articles.create(url='https://onlinelibrary.wiley.com/doi/full/10.1111/isj.12227')
        self.document.articles.create(url='https://lans-tts.uantwerpen.be/index.php/LANS-TTS/article/view/279')
        self.document.articles.create(
            url='https://blogs.lse.ac.uk/impactofsocialsciences/2017/04/05/crowdsourcing-raises-methodological-and-ethical-questions-for-academia/')
        self.document.generate_summarization(get_articles=False)
        self.assertTrue(len(self.document.sentences.all()) > 0)
        self.assertTrue(len(self.document.articles.all()) >= 5)

    def test_summarizer_given_url(self):
        # self.document = Document.objects.create(title="Olympics Baseball News")
        # self.document.articles.create(url='https://www.espn.com/mlb/story/_/id/17223754/baseball-returning-olympics-how-long')
        # self.document.articles.create(url='https://www.denverpost.com/2020/05/14/mlb-olympics/')
        # self.document.articles.create(url='https://www.forbes.com/sites/nickdiunte/2020/03/26/usa-baseball-puts-their-qualifying-bid-on-hold-after-tokyo-2020-summer-olympics-postponement/?sh=6e9c653a3fa1')
        # self.document.generate_summarization(get_articles=False)
        # print(self.document.sentences.all())

        self.document = Document.objects.create(title="Self-Driving Car Accident")
        self.document.articles.create(
            url='https://www.nytimes.com/2020/09/15/technology/uber-autonomous-crash-driver-charged.html')
        self.document.articles.create(
            url='https://www.nbcnews.com/'
                'tech/tech-news/self-driving-uber-car-hit-killed-woman-did-not-recognize-n1079281')
        self.document.articles.create(
            url='https://www.theverge.com/'
                '2019/11/20/20973971/uber-self-driving-car-crash-investigation-human-error-results')
        # # self.document.articles.create(
        # url='https://www.theverge.com/2020/9/16/21439354/uber-backup-driver-charged-autonomous-self-driving-car-crash-negligent-homicide')
        # # self.document.articles.create(url='https://en.wikipedia.org/wiki/Death_of_Elaine_Herzberg')

        # self.document.generate_summarization(get_articles=False, summarizer="t5")
        self.document.generate_summarization(get_articles=False, summarizer="gpt3")
        print(self.document.sentences.all())

        # self.document = Document.objects.create(title="Omelette History")
        # self.document.articles.create(url='https://en.wikipedia.org/wiki/Omelette')
        # self.document.articles.create(url='https://www.everybuddyscasualdining.com/2019/03/11/the-origin-of-the-omelet/')
        # self.document.articles.create(url='https://www.eggrecipes.co.uk/blog/who-invented-omelette')
        # self.document.articles.create(url='https://ifood.tv/omelette/about')
        # self.document.articles.create(url='https://ardisarts.wordpress.com/2016/03/01/a-history-of-omelettes/')
        # self.document.generate_summarization(get_articles=False)
        # print(self.document.sentences.all())


class DocumentSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')

    def tearDown(self):
        Document.objects.all().delete()
        self.user.delete()

    def test_serialize(self):
        self.document = Document.objects.create(title='Crowdsourcing')
        self.document.author = 'Ben'
        self.document.articles.create(text='Some article', url='www.google.com')

        # simple case
        serializer = DocumentSerializer(self.document)
        self.assertTrue(serializer.data['id'] > 0)
        self.assertEqual(serializer.data['title'], 'Crowdsourcing')
        self.assertEqual(serializer.data['author'], 'Ben')
        self.assertEqual(serializer.data['articles'][0]['text'], 'Some article')

        # with sections
        self.section = Section.objects.create(
            document=self.document,
            heading="Section Test",
            position=0)
        self.section.articles.create(text='Some section article', url='www.google.com')
        serializer = DocumentSerializer(self.document)
        self.assertEqual(serializer.data['sections'][0]['heading'], 'Section Test')
        self.assertEqual(serializer.data['sections'][0]['articles'][0]['text'], 'Some section article')

        # with keywords
        self.keyword = Keyword.objects.create(
            document=self.document,
            text='ethical'
        )
        serializer = DocumentSerializer(self.document)
        self.assertEqual(serializer.data['keywords'][0]['text'], 'ethical')

    def test_sentence_ordering(self):
        self.document = Document.objects.create(title='Document')
        self.document.author = 'Ben'

        Sentence.objects.create(text='Second sentence.', document=self.document, position=1)
        Sentence.objects.create(text='Last sentence.', document=self.document, position=2)
        Sentence.objects.create(text='First sentence.', document=self.document, position=0)

        serializer = DocumentSerializer(self.document)
        self.assertEqual(serializer.data['sentences'][0]['position'], 0)

    def test_update_existing_keywords(self):
        self.document = Document.objects.create(title='Crowdsourcing')
        self.document.author = 'Ben'
        self.section = Section.objects.create(
            document=self.document, heading='Section Test', position=0)
        self.sentence = Sentence.objects.create(
            text='This is a sentence.',
            document=self.document,
            section=self.section,
            position=0)
        self.sentence_two = Sentence.objects.create(
            text='This is a sentence without a section.',
            document=self.document,
            position=0)
        self.section_two = Section.objects.create(
            document=self.document, heading='Section Two Test', position=0)
        self.keyword = Keyword.objects.create(
            document=self.document, text='Keyword Test'
        )
        self.document.save()

        self.assertFalse(Keyword.objects.get(pk=self.keyword.id).is_user_defined)

        validated_data = {'id': self.document.id, 'title': 'UPDATED', 'author': 'BenJAMIN',
                          'sections': [
                              OrderedDict([('id', self.section.id), ('heading', 'UPDATED Section'), ('position', 0),
                                           ('articles', []),
                                           ('sentences', [OrderedDict(
                                               [('id', self.sentence.id), ('text', 'UPDATED This is a sentence.'),
                                                ('position', 0), ('articles', []), ('is_deleted', False),
                                                ('is_user_defined', True)]),
                                               OrderedDict(
                                                   [('text', 'NEW SENTENCE'), ('position', 2), ('articles', []),
                                                    ('is_deleted', False), ('is_user_defined', True)])])]),
                              OrderedDict([('heading', 'NEW Section'), ('position', 1),
                                           ('sentences', []), ('articles', [])])],
                          'sentences': [
                              OrderedDict(
                                  [('id', self.sentence_two.id), ('text', 'This is a sentence without a section.'),
                                   ('position', 1), ('articles', []), ('is_deleted', False), ('is_user_defined', True)])
                          ],
                          'keywords': [
                              OrderedDict([('id', self.keyword.id), ('text', 'Keyword Test'), ('is_user_defined', True),
                                           ('is_deleted', False)])
                          ],
                          'articles': [],
                          'suggested_links': [],
                          'documentHistories': []}
        serializer = DocumentSerializer(self.document)
        serializer.update(self.document, validated_data)

        # assert that keyword was changed to is_user_defined == True
        self.assertTrue(Keyword.objects.get(pk=self.keyword.id).is_user_defined)

    def test_update_new_keyword(self):
        self.document = Document.objects.create(title='Crowdsourcing')
        self.document.author = 'Ben'
        self.section = Section.objects.create(
            document=self.document, heading='Section Test', position=0)
        self.sentence = Sentence.objects.create(
            text='This is a sentence.',
            document=self.document,
            section=self.section,
            position=0)
        self.sentence_two = Sentence.objects.create(
            text='This is a sentence without a section.',
            document=self.document,
            position=0)
        self.section_two = Section.objects.create(
            document=self.document, heading='Section Two Test', position=0)
        self.keyword = Keyword.objects.create(
            document=self.document, text='Keyword Test'
        )
        self.document.save()

        self.assertEqual(len(Document.objects.get(pk=self.document.id).keywords.all()), 1)

        validated_data = {'id': self.document.id, 'title': 'UPDATED', 'author': 'BenJAMIN',
                          'sections': [
                              OrderedDict([('id', self.section.id), ('heading', 'UPDATED Section'), ('position', 0),
                                           ('articles', []),
                                           ('sentences', [OrderedDict(
                                               [('id', self.sentence.id), ('text', 'UPDATED This is a sentence.'),
                                                ('position', 0), ('articles', []), ('is_deleted', False),
                                                ('is_user_defined', True)]),
                                               OrderedDict(
                                                   [('text', 'NEW SENTENCE'), ('position', 2), ('articles', []),
                                                    ('is_deleted', False), ('is_user_defined', True)])])]),
                              OrderedDict([('heading', 'NEW Section'), ('position', 1),
                                           ('sentences', []), ('articles', []), ('is_deleted', False),
                                           ('is_user_defined', True)])],
                          'sentences': [
                              OrderedDict(
                                  [('id', self.sentence_two.id), ('text', 'This is a sentence without a section.'),
                                   ('position', 1), ('articles', []), ('is_deleted', False), ('is_user_defined', True)])
                          ],
                          'keywords': [
                              OrderedDict([('id', self.keyword.id), ('text', 'Keyword Test'), ('is_user_defined', True),
                                           ('is_deleted', False)]),
                              OrderedDict([('text', 'New Keyword Test'), ('is_user_defined', True),
                                           ('is_deleted', False)])
                          ],
                          'articles': [],
                          'suggested_links': [],
                          'documentHistories': []
                          }
        serializer = DocumentSerializer(self.document)
        serializer.update(self.document, validated_data)

        # assert that keyword was created
        self.assertEqual(len(Document.objects.get(pk=self.document.id).keywords.all()), 2)


class DocumentViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')

    def tearDown(self):
        # Document.objects.all().delete()
        self.user.delete()

    def test_get_view(self):
        self.document = Document.objects.create(title='Testing Get View')
        self.section = Section.objects.create(
            document=self.document, heading='Section Test', position=0)
        self.sentence = Sentence.objects.create(
            text='This is a sentence.',
            document=self.document,
            section=self.section,
            position=0)
        self.sentence = Sentence.objects.create(
            text='This is a sentence without a section.',
            document=self.document,
            position=0)

        c = APIClient()
        response = c.get('/documents/{}/'.format(str(self.document.id)))
        self.assertEqual(response.json()['title'], 'Testing Get View')
        self.assertEqual(len(response.json()['sections']), 1)
        self.assertEqual(response.json()['sections'][0]['heading'],
                         'Section Test')
        self.assertEqual(response.json()['sentences'][0]['text'],
                         'This is a sentence without a section.')

    def test_update_view_empty_doc(self):
        self.document = Document.objects.create()

        c = APIClient()
        response = c.put(
            f'/documents/{self.document.id}/', {
                'id': self.document.id,
                'author': 'Benjamin',
                'title': 'Crowdsourcing',
                'sections': [],
                'sentences': [],
                'keywords': [],
                'articles': [],
                'suggested_links': [],
                'documentHistories': []
            },
            format='json'
        )

        self.assertTrue(response.status_code != 400)

    def test_update_view_empty_one_url(self):
        self.document = Document.objects.create()

        c = APIClient()
        response = c.put(
            f'/documents/{self.document.id}/', {
                'id': self.document.id,
                'author': 'Benjamin',
                'title': 'Crowdsourcing',
                'sections': [],
                'sentences': [],
                'keywords': [],
                'articles': [{
                    'url': "https://www.brookings.edu/blog/brown-center-chalkboard/2016/02/08/can-crowdsourcing-be-ethical/",
                    'text': "",
                    'sentences': []
                }],
                'suggested_links': [],
                'documentHistories': []

            },
            format='json'
        )

        self.assertTrue(response.status_code != 400)
        self.document = Document.objects.get(pk=self.document.id)
        self.assertEqual(len(self.document.articles.all()), 1)

    def test_update_view(self):
        self.document = Document.objects.create(title='Testing Get View')
        self.section = Section.objects.create(
            document=self.document, heading='Section Test', position=0)
        self.sentence = Sentence.objects.create(
            text='This is a sentence.',
            section=self.section,
            position=0)
        self.sentence_two = Sentence.objects.create(
            text='This is a sentence without a section.',
            document=self.document,
            position=0)
        self.section_two = Section.objects.create(
            document=self.document, heading='Section Two Test', position=0)
        self.keyword = Keyword.objects.create(
            document=self.document, text='Keyword Test'
        )

        c = APIClient()
        response = c.put(
            '/documents/{}/'.format(str(self.document.id)), {
                'id': self.document.id,
                'title': 'UPDATED',
                'author': 'BenJAMIN',
                'sections': [{
                    'id': self.section.id,
                    'heading': 'UPDATED Section',
                    'position': 0,
                    'sentences': [{
                        'id': self.sentence.id,
                        'text': 'UPDATED This is a sentence.',
                        'position': 0,
                        'articles': [],
                        'is_deleted': False,
                        'is_user_defined': True
                    }, {
                        'text': 'NEW SENTENCE',
                        'position': 2,
                        'articles': [],
                        'is_deleted': False,
                        'is_user_defined': True
                    }],
                    'articles': []
                }, {
                    'heading': 'NEW Section',
                    'position': 1,
                    'sentences': [],
                    'articles': []
                }],
                'sentences': [{
                    'id': self.sentence_two.id,
                    'text': 'This is a sentence without a section.',
                    'position': 1,
                    'articles': [],
                    'is_deleted': False,
                    'is_user_defined': True
                }],
                'keywords': [{
                    'id': self.keyword.id,
                    'text': self.keyword.text,
                    'is_deleted': self.keyword.is_deleted,
                    'is_user_defined': self.keyword.is_user_defined,
                }],
                'articles': [],
                'suggested_links': [],
                'documentHistories': []
            },
            format='json')

        self.assertTrue(response.status_code != 400)
        updated = Document.objects.get(pk=self.document.id)
        self.assertEqual(updated.title, 'UPDATED')
        self.assertEqual(updated.sections.filter(heading='UPDATED Section').count(), 1)
        self.assertEqual(updated.sections.all().count(), 2)
        self.assertEqual(Sentence.objects.filter(text='UPDATED This is a sentence.').count(), 1)
        self.assertEqual(Sentence.objects.filter(text='NEW SENTENCE').count(), 1)
        self.assertEqual(updated.sentences.count(), 1)

        Section.objects.filter(heading='New Section')
        # remove some stuff and check it deletes
        response = c.put(
            '/documents/{}/'.format(str(self.document.id)), {
                'id': self.document.id,
                'title': 'UPDATED',
                'author': 'BenJAMIN',
                'sections': [{
                    'id': self.section.id,
                    'heading': 'UPDATED Section',
                    'position': 0,
                    'sentences': [{
                        'id': self.sentence.id,
                        'text': 'UPDATED This is a sentence.',
                        'position': 0,
                        'articles': [],
                        'is_deleted': False,
                        'is_user_defined': True
                    }],
                    'articles': []
                }],
                'sentences': [],
                'keywords': [],
                'articles': [],
                'suggested_links': [],
                'documentHistories': []
            },
            format='json')

        self.assertTrue(response.status_code != 400)
        updated = Document.objects.get(pk=self.document.id)
        self.assertEqual(updated.sentences.count(), 0)
        self.assertEqual(updated.sections.count(), 1)
        self.assertEqual(updated.sections.all()[0].sentences.count(), 1)

    def test_create_view(self):
        c = APIClient()
        response = c.post(
            '/documents/', {
                'title': 'CREATED',
                'author': 'Ben',
                'sections': [{
                    'heading': 'NEW Section 1',
                    'position': 0,
                    'sentences': [
                        {
                            'text': 'This is a sentence in a section.',
                            'position': 1,
                            'articles': [],
                            'is_deleted': False,
                            'is_user_defined': True
                        },
                    ],
                    'articles': []
                }, {
                    'heading': 'NEW Section 2',
                    'position': 1,
                    'sentences': [],
                    'articles': []
                }],
                'sentences': [],
                'keywords': [],
                'articles': [],
                'suggested_links': [],
                'documentHistories': []
            },
            format='json')

        self.assertTrue(response.status_code != 400)
        instance = Document.objects.filter(title='CREATED')[0]
        self.assertEqual(instance.title, 'CREATED')
        self.assertEqual(instance.sections.count(), 2)
        self.assertEqual(instance.sections.filter(heading='NEW Section 1')[0].sentences.count(), 1)
        self.assertEqual(instance.sections.filter(heading='NEW Section 1')[0].sentences.all()[0].text,
                         'This is a sentence in a section.')

    def test_create_empty_view(self):
        c = APIClient()
        response = c.post(
            '/documents/', {
                'title': '',
                'author': '',
                'sections': [],
                'sentences': [],
                'keywords': [],
                'articles': [],
                'suggested_links': [],
                'documentHistories': []
            },
            format='json')
        print("here")
        print(response)
        self.assertTrue(response.status_code != 400)

    def test_create_generate_summary(self):
        c = APIClient()
        response = c.post(
            '/documents/', {
                'title': 'Crowdsourcing and Machine Learning',
                'author': '',
                'sections': [],
                'sentences': [],
                'keywords': [],
                'articles': [],
                'suggested_links': [],
                'documentHistories': []
            },
            format='json')
        self.assertTrue(response.status_code != 400)

        response = c.get(
            '/documents/fast/{}/user_summary/'.format(response.json()['id'])
        )

        self.assertTrue(len(Document.objects.get(pk=response.json()['id']).sentences.all()) > 0)

    def test_delete_view(self):
        self.document = Document.objects.create(title='Testing Get View')
        self.document2 = Document.objects.create(title='Testing Get View 2')

        c = APIClient()
        response = c.delete('/documents/{}/'.format(str(self.document.id)))
        self.assertEqual(Document.objects.all().count(), 1)

    def test_remove_keyword_view(self):
        # Create the document to remove the keywords from
        self.document = Document.objects.create(title="Crowdsourcing")
        self.document.generate_summarization()
        self.assertTrue(len(self.document.articles.all()) > 0)
        self.assertTrue(len(self.document.tf_idf_scores.keys()) > 0)
        self.assertTrue(len(self.document.sentences.all()) > 0)
        self.assertTrue(len(self.document.keywords.all()) > 1)

        c = APIClient()
        url = '/documents/{}/remove_keyword/{}/'.format(self.document.id, self.document.keywords.all()[0].text)
        response = c.get(
            url
        )

        self.assertTrue(response.status_code != 400)

    def test_generate_user_summary(self):
        self.document = Document.objects.create(title="Education")
        self.document.articles.create(
            url='https://www.brookings.edu/blog/brown-center-chalkboard/2016/02/08/can-crowdsourcing-be-ethical/')
        self.document.articles.create(url='https://rossdawson.com/blog/debate-the-ethics-of-crowdsourcing/')
        self.document.articles.create(url='https://onlinelibrary.wiley.com/doi/full/10.1111/isj.12227')
        self.document.articles.create(url='https://lans-tts.uantwerpen.be/index.php/LANS-TTS/article/view/279')
        self.document.articles.create(
            url='https://blogs.lse.ac.uk/impactofsocialsciences/2017/04/05/crowdsourcing-raises-methodological-and-ethical-questions-for-academia/')

        c = APIClient()
        url = '/documents/presum/{}/user_summary/'.format(self.document.id)
        response = c.get(url)

        self.assertTrue(response.status_code != 400)

        self.document = Document.objects.get(pk=self.document.id)
        self.assertTrue(len(self.document.sentences.all()) > 0)
        self.assertTrue(len(self.document.articles.all()) >= 5)

    def test_chen_links(self):
        self.document = Document.objects.create(title="Education")
        self.document.articles.create(url='https://www.nytimes.com/2020/09/15/technology/uber-autonomous-crash-driver-charged.html')
        self.document.articles.create(url='https://onlinelibrary.wiley.com/doi/full/10.1111/isj.1222://www.nbcnews.com/tech/tech-news/self-driving-uber-car-hit-killed-woman-did-not-recognize-n1079281')
        self.document.articles.create(url='https://www.theverge.com/2019/11/20/20973971/uber-self-driving-car-crash-investigation-human-error-results')
        c = APIClient()
        url = '/documents/presum/{}/user_summary/'.format(self.document.id)
        response = c.get(url)

        self.assertTrue(response.status_code != 400)

        self.document = Document.objects.get(pk=self.document.id)
        self.assertTrue(len(self.document.sentences.all()) > 0)
        self.assertTrue(len(self.document.articles.all()) >= 3)

    def test_generate_section_summarization(self):
        self.document = Document.objects.create(title="Education")
        self.section = Section.objects.create(heading="Test", document=self.document)
        self.section.articles.create(url='https://stackify.com/unit-testing-basics-best-practices/')
        self.section.articles.create(
            url='https://www.toptal.com/qa/how-to-write-testable-code-and-why-it-matters')

        c = APIClient()
        url = '/documents/fast/{}/section_summary/'.format(self.document.id)
        response = c.post(url,
                          {
                              'section_heading': self.section.heading
                          },
                          format='json')

        self.assertTrue(response.status_code != 400)

        self.document = Document.objects.get(pk=self.document.id)
        self.assertTrue(len(self.section.sentences.all()) > 0)
        print(self.section)
        print(self.document)

    def test_big_put(self):
        self.document = Document.objects.create(title="Unit Testing")

        data = {
            "id": self.document.id,
            "title": "Unit Testing",
            "author": "",
            "sections": [],
            "sentences": [
                {
                    "text": "",
                    "position": 0,
                    "is_user_defined": True,
                    "is_deleted": False
                }
            ],
            "keywords": [
                {
                    "text": "yes",
                    "is_user_defined": False,
                    "is_deleted": False
                },
                {
                    "text": "pages",
                    "is_user_defined": False,
                    "is_deleted": False
                },
                {
                    "text": "22",
                    "is_user_defined": False,
                    "is_deleted": False
                },
                {
                    "text": "adder",
                    "is_user_defined": False,
                    "is_deleted": False
                },
                {
                    "text": "self",
                    "is_user_defined": False,
                    "is_deleted": False
                },
                {
                    "text": "calculator",
                    "is_user_defined": False,
                    "is_deleted": False
                },
                {
                    "text": "datetime",
                    "is_user_defined": False,
                    "is_deleted": False
                },
                {
                    "text": "solitary",
                    "is_user_defined": False,
                    "is_deleted": False
                },
                {
                    "text": "commit",
                    "is_user_defined": False,
                    "is_deleted": False
                },
                {
                    "text": "subcategory",
                    "is_user_defined": False,
                    "is_deleted": False
                }
            ],
            "articles": [],
            "suggested_links": [
                {
                    "url": "https://en.wikipedia.org/wiki/List_of_unit_testing_frameworks"
                },
                {
                    "url": "https://en.wikipedia.org/wiki/Software_testing"
                },
                {
                    "url": "https://stackify.com/unit-testing-basics-best-practices/"
                },
                {
                    "url": "https://www.guru99.com/unit-testing-guide.html"
                },
                {
                    "url": "https://www.testingxperts.com/blog/unit-testing"
                },
                {
                    "url": "https://www.tutorialspoint.com/software_testing_dictionary/unit_testing.htm"
                },
                {
                    "url": "https://en.wikipedia.org/wiki/Unit_testing"
                },
                {
                    "url": "https://www.toptal.com/qa/how-to-write-testable-code-and-why-it-matters"
                },
                {
                    "url": "https://softwaretestingfundamentals.com/unit-testing/"
                },
                {
                    "url": "https://smartbear.com/learn/automated-testing/what-is-unit-testing/"
                },
                {
                    "url": "https://martinfowler.com/bliki/UnitTest.html"
                },
                {
                    "url": "https://en.wikipedia.org/wiki/Category:Unit_testing"
                },
                {
                    "url": "https://en.wikipedia.org/wiki/Integration_testing"
                },
                {
                    "url": "https://docs.python.org/3/library/unittest.html"
                }
            ],
            "documentHistories": [
                {
                    "timestamp": "2021-02-18T14:12:16",
                    "text": ""
                }
            ]
        }
        url = '/documents/{}/'.format(self.document.id)

        c = APIClient()
        response = c.put(url, data, format='json')
        import ipdb; ipdb.set_trace()
        print(response)


class ArticleTest(TestCase):
    def setup(self):
        self.user = User.objects.create_user('test_user')

    def test_serializer(self):
        article = Article.objects.create(text='Some article', url='www.google.com')
        serializer = ArticleSerializer(article)
        self.assertTrue(serializer.data['id'] > 0)
        self.assertEqual(serializer.data['text'], 'Some article')
        self.assertEqual(serializer.data['url'], 'www.google.com')


class KeywordTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.document = Document.objects.create(title='Mary')

    def test_creation(self):
        # keyword1 = Keyword.objects.create(text='love')
        keyword2 = Keyword.objects.create(text='apple', document=self.document)
        # self.assertEqual(keyword1.text, 'love')
        self.assertEqual(keyword2.text, 'apple')


class SentenceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.document = Document.objects.create(title='Mary')

    def test_create(self):
        sentence = Sentence.objects.create(
            text='Mary had a little lamb.', document=self.document, position=0)
        self.assertTrue(sentence)
        self.assertEqual(sentence.text, 'Mary had a little lamb.')
        self.assertFalse(sentence.is_deleted)
        self.assertFalse(sentence.is_user_defined)
        sentence.is_deleted = True
        sentence.is_user_defined = True
        self.assertTrue(sentence.is_deleted)
        self.assertTrue(sentence.is_user_defined)

    def test_build_triples(self):
        sentence = Sentence.objects.create(
            text='Mary had a little lamb.', document=self.document, position=0)
        sentence.build_triples()
        self.assertTrue(len(sentence.triple_set.all()) > 0)

    def test_incomplete_sentence(self):
        sentence = Sentence.objects.create(
            text='Mary had.', document=self.document, position=0)
        sentence.build_triples()
        self.assertTrue(len(sentence.triple_set.all()) == 0)

    def test_hashing(self):
        sentence = Sentence.objects.create(
            text='Mary had a little lamb.', document=self.document, position=0)
        sentence_dup = Sentence.objects.create(
            text='Mary had a little lamb.', document=self.document, position=1)
        sentence_not_dup = Sentence.objects.create(
            text='Mary did not have a little lamb.', document=self.document, position=2)

        dict = {sentence, '1'}
        self.assertTrue(sentence_dup in dict)
        self.assertFalse(sentence_not_dup in dict)

    def test_serializer(self):
        sentence = Sentence.objects.create(
            text='Mary had a little lamb.', document=self.document, position=0)
        sentence.articles.create(text='Some article', url='www.google.com')
        serializer = SentenceSerializer(sentence)
        self.assertTrue(serializer.data['id'] > 0)
        self.assertEqual(serializer.data['text'], 'Mary had a little lamb.')
        self.assertEqual(serializer.data['position'], 0)
        self.assertEqual(serializer.data['articles'][0]['text'], 'Some article')


class ArticleExtractorTest(TestCase):
    def test_extract_articles(self):
        urls = ['https://en.wikipedia.org/wiki/Crowdsourcing',
                'https://en.wikipedia.org/wiki/Crowdsourcing%23Definitions',
                'https://en.wikipedia.org/wiki/Crowdsourcing%23Historical_examples',
                'https://en.wikipedia.org/wiki/Crowdsourcing%23Modern_methods']

        extractor = ArticleExtractor()
        extractor.extract_articles(urls)

        self.assertEquals(len(extractor.articles), 1)


class GoogleExtractorTest(TestCase):
    def setUp(self):
        self.extractor = GoogleExtractor()

    def test_execute_google_query(self):
        urls = self.extractor.execute_google_query(['crowdsourcing'], [])
        self.assertNotEqual(urls, [])

    def test_extract_articles(self):
        links = [
            'https://dailycrowdsource.com/training/crowdsourcing/what-is-crowdsourcing',
            'https://www.crowdsource.com/',
            'https://www.seattletimes.com/seattle-news/in-seattle-some-homeless-people-find-help-via-crowdsourcing-how-do-you-know-how-to-give/',
            'http://crowdsourcingweek.com/what-is-crowdsourcing/',
            'https://www.wired.com/2006/06/crowds/',
            'https://www.cbsnews.com/news/what-is-crowdsourcing/',
            'http://www.crowdsourcing.com/'
        ]

        self.extractor.extract_articles(links)
        self.assertNotEqual(self.extractor.articles, [])
        self.assertTrue(self.extractor.articles[0].text)
        # print([article.text for article in self.extractor.articles])

    def test_extract_pdfs(self):
        links = [
            'https://sistemas-humano-computacionais.wdfiles.com/local--files'
            + '/capitulo%3Aredes-sociais/Howe_The_Rise_of_Crowdsourcing.pdf',
            'http://www.pertanika.upm.edu.my/Pertanika%20PAPERS/'
            + 'JST%20Vol.%2025%20(S)%20Oct.%202017/07%20JST(S)-0403-2017-2ndProof.pdf',
            'https://aisel.aisnet.org/cgi/viewcontent.cgi?article=1031&context=acis2010'
        ]

        self.extractor.extract_articles(links)
        self.assertNotEqual(self.extractor.articles, [])
        self.assertTrue(self.extractor.articles[0])
        self.assertEquals(len(self.extractor.articles), 3)
        # for article in self.extractor.articles:
        #     print(article)


class DocumentHistoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user')
        self.document = Document.objects.create(title='Mary')

    def test_create(self):
        sentence = Sentence.objects.create(
            text='Mary had a little lamb.', document=self.document, position=0)
        sentence.save()
        # self.document.save()
        section = Section.objects.create(heading='Color', document=self.document)
        section.save()
        sentence2 = Sentence.objects.create(
            text='It had a white fleece.', document=self.document, section=section,
            position=1)
        sentence2.save()
        self.document.save()
        self.assertTrue(self.document.documentHistories.all().count() > 0)
        print(self.document.documentHistories.all().count() > 0)
        print(self.document.documentHistories.all())
