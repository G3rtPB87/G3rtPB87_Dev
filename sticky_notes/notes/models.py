from django.db import models


class Note(models.Model):
    """
    Model representing a single sticky note.
    """
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Returns a string representation of the note.
        """
        return self.title
