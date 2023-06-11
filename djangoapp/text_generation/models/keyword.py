from django.db import models


class Keyword(models.Model):
    """ Model representing a key word for query """
    text = models.CharField(max_length=200)
    is_user_defined = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    document = models.ForeignKey('Document',
                                 related_name='keywords',
                                 on_delete=models.CASCADE,
                                 null=True,
                                 blank=True)

    def get_text(self):
        return self.text

    def __str__(self):
        """String for representing the Model object."""
        user_define_info = ""
        delete_info = ""
        if self.is_user_defined:
            user_define_info = "user_defined"
        else:
            user_define_info = "not user_defined"

        if self.is_deleted:
            delete_info = "deleted"
        else:
            delete_info = "not deleted"

        info = "%s, %s, %s" % (self.text, user_define_info, delete_info)
        return info
