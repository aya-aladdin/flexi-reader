import logging
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Book, Annotation
from .forms import UserProfileForm, BookUploadForm, BookForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, FileResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django.core.files.base import ContentFile
from PyPDF2 import PdfReader, PdfWriter
import io

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'core/home.html')


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                UserProfile.objects.create(user=user)
                login(request, user)
                return redirect('core:home')
            except Exception as e:
                logger.error(f"Error during signup: {e}", exc_info=True)
                return render(request, 'core/signup.html', {'form': form, 'error': 'Signup failed.'})
        else:
            logger.debug(f"Signup form errors: {form.errors}")
            return render(request, 'core/signup.html', {'form': form})
    else:
        form = UserCreationForm()
    return render(request, 'core/signup.html', {'form': form})


def signin(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('core:home')
    else:
        form = AuthenticationForm()
    return render(request, 'core/signin.html', {'form': form})


def signout(request):
    logout(request)
    return redirect('core:home')


@login_required
def library(request):
    books = Book.objects.filter(user=request.user).order_by('-uploaded_at')
    paginator = Paginator(books, 10)
    page = request.GET.get('page')
    try:
        books_page = paginator.page(page)
    except PageNotAnInteger:
        books_page = paginator.page(1)
    except EmptyPage:
        books_page = paginator.page(paginator.num_pages)
    return render(request, 'core/library.html', {'books': books_page})



def remove_page_numbers(pdf_file):
    """Removes page numbers from a PDF file."""
    try:
        pdf_reader = PdfReader(pdf_file)
        pdf_writer = PdfWriter()

        for page in pdf_reader.pages:
            #  Remove the bottom 50 units of the page.
            page.mediabox.lower_left = (page.mediabox.lower_left[0], 50)
            pdf_writer.add_page(page)

        output_stream = io.BytesIO()
        pdf_writer.write(output_stream)
        output_stream.seek(0)
        return output_stream
    except Exception as e:
        logger.error(f"Error removing page numbers: {e}", exc_info=True)
        return None



@login_required
def upload_book(request):
    if request.method == 'POST':
        form = BookUploadForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.user = request.user
            try:
                cleaned_pdf = remove_page_numbers(book.file)
                if cleaned_pdf:
                    book.file.save(book.file.name, ContentFile(cleaned_pdf.read()), save=False)
                book.save()
                return redirect('core:library')
            except Exception as e:
                logger.error(f"Error saving book: {e}", exc_info=True)
                return render(request, 'core/upload_book.html', {'form': form, 'error': 'Upload failed.'})
        else:
            logger.warning(f"Form errors: {form.errors}")
            return render(request, 'core/upload_book.html', {'form': form, 'error': 'Invalid form data.'})
    else:
        form = BookUploadForm()
    return render(request, 'core/upload_book.html', {'form': form})



@login_required
def settings(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('core:settings')
    else:
        form = UserProfileForm(instance=user_profile)
    return render(request, 'core/settings.html', {'form': form})



@login_required
def read_book(request, book_id):
    book = get_object_or_404(Book, id=book_id, user=request.user)
    user_profile = get_object_or_404(UserProfile, user=request.user)
    annotations = Annotation.objects.filter(
        book=book, user=request.user).order_by('start_position')
    file_name = book.file.name
    file_extension = os.path.splitext(file_name)[1].lower()
    file_type = 'pdf' if file_extension == '.pdf' else 'unsupported'
    context = {
        'book': book,
        'user_profile': user_profile,
        'annotations': annotations,
        'file_type': file_type,
    }

    if request.method == "POST":
        action = request.POST.get('action')
        return handle_annotation_action(request, book, action)

    return render(request, 'core/read_book.html', context)


def handle_annotation_action(request, book, action):
    """Helper function to handle annotation actions."""
    try:
        if action == 'create':
            text = request.POST.get('text')
            note = request.POST.get('note', '')
            start_position = int(request.POST.get('start_position', 0))
            end_position = int(request.POST.get('end_position', 0))
            color = request.POST.get('color', '#FFFF00')
            annotation = Annotation.objects.create(
                book=book, user=request.user, text=text, note=note,
                start_position=start_position, end_position=end_position, color=color
            )
            return JsonResponse({
                'id': annotation.id, 'text': annotation.text, 'note': annotation.note,
                'start_position': annotation.start_position, 'end_position': annotation.end_position,
                'color': annotation.color, 'created_at': annotation.created_at.isoformat()
            })
        elif action == 'update':
            annotation_id = int(request.POST.get('annotation_id'))
            annotation = Annotation.objects.get(id=annotation_id, user=request.user, book=book)
            annotation.text = request.POST.get('text')
            annotation.note = request.POST.get('note', '')
            annotation.start_position = int(request.POST.get('start_position', 0))
            annotation.end_position = int(request.POST.get('end_position', 0))
            annotation.color = request.POST.get('color', '#FFFF00')
            annotation.save()
            return JsonResponse({'status': 'success'})
        elif action == 'delete':
            annotation_id = int(request.POST.get('annotation_id'))
            annotation = Annotation.objects.get(id=annotation_id, user=request.user, book=book)
            annotation.delete()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
    except (ValueError, Annotation.DoesNotExist) as e:
        logger.error(f"Error handling annotation action {action}: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400 if isinstance(e, ValueError) else 404)
    except Exception as e:
        logger.exception(f"Unexpected error handling annotation action {action}: {e}")
        return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)



@login_required
def book_file_url(request, book_id):
    book = get_object_or_404(Book, id=book_id, user=request.user)
    try:
        return FileResponse(open(book.file.path, 'rb'), as_attachment=False)
    except Exception as e:
        logger.exception(f"Error serving file for book {book_id}: {e}")
        return HttpResponse("Internal server error", status=500)


@login_required
def get_edit_form_json(request, book_id):
    book = get_object_or_404(Book, pk=book_id, user=request.user)
    form = BookForm(instance=book)
    form_data = {
        'id': book.id,
        'title': form['title'].value(),
        'cover_image_url': book.cover_image.url if book.cover_image else None,
        'book_file_url': book.file.url if book.file else None,
        'uploaded_at': book.uploaded_at.isoformat(),
    }
    return JsonResponse(form_data)



@require_POST
@login_required
def update_book(request, book_id):
    book = get_object_or_404(Book, id=book_id, user=request.user)
    form = BookForm(request.POST, request.FILES, instance=book)
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


@csrf_protect
@require_POST
@login_required
def delete_book(request, book_id):
    try:
        book = get_object_or_404(Book, id=book_id, user=request.user)
        book.delete()
        return JsonResponse({'status': 'success', 'message': 'Book deleted'})
    except Exception as e:
        logger.exception(f"Error deleting book {book_id}: {e}")
        return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)

from django.db.models import Q

@login_required
def book_library(request):
    query = request.GET.get('search', '')  # Get the search query from the GET request
    books = Book.objects.filter(user=request.user)  # Start with all books for the current user

   
    if query:
        books = books.filter(title__icontains=query)

    context = {
        'books': books,
    }
    return render(request, 'core/booklibrary.html', context)