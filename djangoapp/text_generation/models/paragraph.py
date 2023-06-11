from django.db import models


class Paragraph(models.Model):
    document = models.ForeignKey('Document', null=True, on_delete=models.CASCADE)
    section = models.ForeignKey('Section', null=True, on_delete=models.CASCADE)
    position = models.IntegerField()
