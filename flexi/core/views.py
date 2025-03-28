from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Book, Annotation
from .forms import UserProfileForm, BookUploadForm, BookForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, FileResponse, HttpResponse
import logging
import os
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect

# Configure logging at the module level
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'core/home.html')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()  # Save directly
                UserProfile.objects.create(user=user)
                login(request, user)
                return redirect('core:home')
            except Exception as e:
                logger.error(f"Error during signup process: {e}, type: {type(e)}", exc_info=True)
                return render(request, 'core/signup.html', {'form': form, 'error': 'An error occurred during signup.'})
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

@login_required
def upload_book(request):
    if request.method == 'POST':
        form = BookUploadForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.user = request.user
            book.save()
            return redirect('core:library')
        else:
            return render(request, 'core/upload_book.html', {'form': form})
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
    annotations = Annotation.objects.filter(book=book, user=request.user).order_by('start_position')

    file_name = book.file.name
    file_extension = os.path.splitext(file_name)[1].lower()
    file_type = ''
    if file_extension == '.pdf':
        file_type = 'pdf'
    else:
        file_type = 'unsupported'

    context = {
        'book': book,
        'user_profile': user_profile,
        'annotations': annotations,
        'file_type': file_type,
    }

    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'create':
            text = request.POST.get('text')
            note = request.POST.get('note', '')
            try:
                start_position = int(request.POST.get('start_position', 0))
                end_position = int(request.POST.get('end_position', 0))
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid position values'}, status=400)
            color = request.POST.get('color', '#FFFF00')
            annotation = Annotation.objects.create(
                book=book, user=request.user, text=text, note=note,
                start_position=start_position, end_position=end_position, color=color
            )
            return JsonResponse({
                'id': annotation.id,
                'text': annotation.text,
                'note': annotation.note,
                'start_position': annotation.start_position,
                'end_position': annotation.end_position,
                'color': annotation.color,
                'created_at': annotation.created_at.isoformat()
            })

        elif action == 'update':
            try:
                annotation_id = int(request.POST.get('annotation_id'))
                annotation = Annotation.objects.get(id=annotation_id, user=request.user, book=book)
                annotation.text = request.POST.get('text')
                annotation.note = request.POST.get('note', '')
                try:
                    annotation.start_position = int(request.POST.get('start_position', 0))
                    annotation.end_position = int(request.POST.get('end_position', 0))
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid position values for update'}, status=400)
                annotation.color = request.POST.get('color', '#FFFF00')
                annotation.save()
                return JsonResponse({'status': 'success'})
            except (Annotation.DoesNotExist, ValueError):
                return JsonResponse({'status': 'error', 'message': 'Annotation not found'}, status=404)

        elif action == 'delete':
            try:
                annotation_id = int(request.POST.get('annotation_id'))
                annotation = Annotation.objects.get(id=annotation_id, user=request.user, book=book)
                annotation.delete()
                return JsonResponse({'status': 'success'})
            except (Annotation.DoesNotExist, ValueError):
                return JsonResponse({'status': 'error', 'message': 'Annotation not found'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)

    return render(request, 'core/read_book.html', context)

@login_required
def book_file_url(request, book_id):
    book = get_object_or_404(Book, id=book_id, user=request.user)
    return FileResponse(book.file, as_attachment=False)

@login_required
def get_edit_form_json(request, book_id):
    book = get_object_or_404(Book, pk=book_id, user=request.user) #added user
    form = BookForm(instance=book)

    # Convert the form data to a JSON-serializable format
    form_data = {
        'id': book.id,  # Include the book ID
        'title': form['title'].value(),
        'cover_image_url': book.cover_image.url if book.cover_image else None,
        'book_file_url': book.file.url if book.file else None,
        'uploaded_at': book.uploaded_at.isoformat(),
        #If you have more fields in Book model, add them here.
    }

    return JsonResponse(form_data)


@require_POST
@login_required
def update_book(request, book_id):
    """
    View to update an existing book via a JSON/FormData submission.
    """
    book = get_object_or_404(Book, id=book_id, user=request.user)
    form = BookForm(request.POST, request.FILES, instance=book)  # request.FILES is needed for images
    if form.is_valid():
        form.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)  # Return errors for display

@csrf_protect # or @method_decorator(csrf_protect, name='dispatch') for class-based views
@require_POST #make sure only post is allowed
@login_required
def delete_book(request, book_id):
    try:
        book = get_object_or_404(Book, id=book_id, user=request.user)  # Assuming 'Book' is your model
        book.delete()
        return JsonResponse({'status': 'success', 'message': 'Book deleted'}) # Return JSON response
    except Exception as e:
        logger.exception(f"Error deleting book {book_id}: {e}") # Log the error
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500) # Return error

