# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class TextGenerationConfig(AppConfig):
    name = 'text_generation'

    def ready(self):
        import text_generation.signals
