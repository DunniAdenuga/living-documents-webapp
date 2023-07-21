from django.db import models


class Article(models.Model):
    text = models.TextField(blank=True)
    document = models.ForeignKey(
        'Document',
        related_name='articles',
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    section = models.ForeignKey(
        'Section',
        related_name='articles',
        null=True,
        blank=True,
        on_delete=models.CASCADE)

    url = models.URLField(blank=True, null=True, max_length=1000)

    def __str__(self):
        """String for representing the Model object."""
        info = "%d: %s" % (self.id, self.url)
        return info
