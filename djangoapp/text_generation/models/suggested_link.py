from django.db import models


class SuggestedLink(models.Model):
    document = models.ForeignKey(
        'Document',
        related_name='suggested_links',
        on_delete=models.CASCADE,
        null=True,
        blank=True)

    url = models.URLField(blank=True, null=True, max_length=1000)
