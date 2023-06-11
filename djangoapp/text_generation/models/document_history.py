from django.db import models


class DocumentHistory(models.Model):
    """(Document History description)"""

    timestamp = models.DateTimeField(auto_now_add=True)
    # timestamp = models.TextField()
    document = models.ForeignKey(
        'Document',
        related_name="documentHistories",
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    # documentID = models.
    # previousDocument =
    text = models.TextField(blank=True)
    articleList = models.TextField(blank=True)

    def __str__(self):
        """String for representing document histories"""
        return f'{self.id}: {self.timestamp}: {self.text}: {self.articleList}'
