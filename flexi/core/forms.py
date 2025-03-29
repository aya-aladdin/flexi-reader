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
    cover_image_url = forms.URLField(label='Cover Image URL', required=False)

    class Meta:
        model = Book
        fields = ['title', 'file', 'cover_image_url']  # Use cover_image_url

        labels = {
            'title': 'Book Title',
            'file': 'Book File',
            'cover_image_url': 'Cover Image URL'  # Correct label
        }
        help_texts = {
            'file': 'Upload the book file (e.g., .pdf)',
            'cover_image_url': 'Enter the URL of the cover image.'
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.cover_image = self.cleaned_data.get('cover_image_url')
        if commit:
            instance.save()
        return instance

class BookForm(forms.ModelForm):
    """
    Form for editing book details.
    """
    cover_image_url = forms.URLField(label='Cover Image URL', required=False)

    class Meta:
        model = Book
        fields = ['title', 'cover_image_url']  # Use cover_image_url
        labels = {
            'title': 'Book Title',
            'cover_image_url': 'Cover Image URL (Optional)',
        }