from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.conf import settings
import os

class UserProfile(models.Model):
    """
    Stores user preferences and settings.  Extends the built-in User model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    theme = models.CharField(max_length=50, default='default')  # e.g., 'default', 'pastel'
    font_size = models.IntegerField(default=16)
    font_family = models.CharField(max_length=50, default='sans-serif')  # e.g., 'sans-serif', 'serif'
    background_color = models.CharField(max_length=20, default='#f0f0f0') # Default background
    text_color = models.CharField(max_length=20, default='#000000')
    line_spacing = models.FloatField(default=1.5)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def delete(self, *args, **kwargs):
        """
        Override the delete method to also delete the associated User instance.
        This ensures that when a UserProfile is deleted, the User is also deleted,
        preventing orphaned User records.
        """
        user = self.user  # Store the User instance
        super().delete(*args, **kwargs)  # Delete the UserProfile instance
        user.delete()  # Delete the User instance


def get_book_cover_path(instance, filename):
    """
    Generates the upload path for book covers, including the user ID.
    The cover will be saved in a directory specific to the user and book.
    """
    user_id = instance.user.id  # Get the user ID from the instance
    return os.path.join('book_covers', str(user_id), str(instance.id), filename)



class Book(models.Model):
    """
    Represents a book uploaded by a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='books/')  # Store the actual book file
    uploaded_at = models.DateTimeField(auto_now_add=True)
    cover_image = models.ImageField(upload_to=get_book_cover_path, null=True, blank=True) #optional cover

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Override the save method to ensure that the upload path
        is correctly set even if the instance.id is not yet available.
        """
        if self.pk is None:  # check if it is a new object
            super().save(*args, **kwargs)  # save it to get an id
            # update the upload path, the instance id is available now.
            if self.cover_image:
                self.cover_image.field.upload_to = get_book_cover_path(self, self.cover_image.name)
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Delete the file(s) associated with the book (cover and book file)
        when the Book instance is deleted.  This prevents orphaned files.
        """
        # Delete the cover image, if it exists
        if self.cover_image:
            if default_storage.exists(self.cover_image.name):
                default_storage.delete(self.cover_image.name)
                # Delete the directory if it is empty
                cover_dir = os.path.dirname(self.cover_image.name)
                if not default_storage.listdir(cover_dir):
                    default_storage.delete(cover_dir)

        # Delete the book file
        if self.file:
            if default_storage.exists(self.file.name):
                default_storage.delete(self.file.name)
        super().delete(*args, **kwargs)


class Annotation(models.Model):
    """
    Stores user annotations (highlights, notes) for a book.
    """
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='annotations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='annotations')
    text = models.TextField()          # The annotated text
    note = models.TextField(blank=True, null=True)  # User's note for the annotation
    start_position = models.IntegerField()  # Character start position in the book
    end_position = models.IntegerField()    # Character end position in the book
    created_at = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=20, default='#FFFF00') # highlight color

    def __str__(self):
        return f"Annotation on '{self.book.title}' by {self.user.username}"
