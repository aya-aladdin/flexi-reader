from django import forms
from .models import UserProfile, Book

class UserProfileForm(forms.ModelForm):
    """
    Form for editing user profile settings.
    """
    class Meta:
        model = UserProfile
        fields = ['theme', 'font_size', 'font_family', 'background_color', 'text_color', 'line_spacing']
        widgets = {
            'background_color': forms.TextInput(attrs={'type': 'color'}),
            'text_color': forms.TextInput(attrs={'type': 'color'}),
        }

class BookUploadForm(forms.ModelForm):
    """
    Form for uploading books.
    """
    class Meta:
        model = Book
        fields = ['title', 'file', 'cover_image']
        # Optionally, customize labels or add help text:
        labels = {
            'title': 'Book Title',
            'file': 'Book File',
            'cover_image': 'Cover Image (Optional)'
        }
        help_texts = {
            'file': 'Upload the book file (e.g., .pdf',
        }

class BookForm(forms.ModelForm):
    """
    Form for editing book details.
    """
    class Meta:
        model = Book
        fields = ['title', 'cover_image']  #  file should NOT be editable.
        labels = {
            'title': 'Book Title',
            'cover_image': 'Cover Image (Optional)',
        }
