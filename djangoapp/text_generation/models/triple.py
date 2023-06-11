from django.db import models


class Triple(models.Model):
    sentence = models.ForeignKey('Sentence', on_delete=models.CASCADE)
    subject = models.TextField()  # TODO change this to token (text, location, length)
    # processed_subject = models.TextField()
    relation = models.TextField()
    # processed_relation = models.TextField()
    object = models.TextField()
    # processed_object = models.TextField()
    # store more info, anaphora, another class maybe, (original, anaphora)- only useful for sub and obj

    is_user_defined = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        """String for representing the Model object."""
        info = "%s, %s, %s" % (self.subject, self.relation, self.object)
        return info