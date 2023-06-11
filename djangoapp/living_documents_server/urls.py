from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import SimpleRouter

from text_generation.views import DocumentViewSet, TripleGraphViewSet

router = SimpleRouter()
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('documents/<int:pk>/get_tree/', TripleGraphViewSet.get_tree_data),
    path('documents/<int:pk>/doc_delete/', DocumentViewSet.doc_delete),
    path('documents/<slug:summarizer>/<int:pk>/user_summary/', DocumentViewSet.generate_user_summary),
    path('documents/<slug:summarizer>/<int:pk>/section_summary/', DocumentViewSet.get_new_section_text),
    # path('documents/<slug:summarizer>/<int:pk>/change_word/', DocumentViewSet.change_word_using_triple_graph),
    # path('documents/<slug:summarizer>/<int:pk>/generate_new_section/', SectionViewSet.generate_new_section),
]
