from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('library/', views.library, name='library'),
    path('upload/', views.upload_book, name='upload_book'),
    path('settings/', views.settings, name='settings'),
    path('read/<int:book_id>/', views.read_book, name='read_book'),
    path('book_file/<int:book_id>/', views.book_file_url, name='book_file_url'),
    path('get_edit_form/<int:book_id>/', views.get_edit_form_json, name='get_edit_form'),
    path('delete_book/<int:book_id>/', views.delete_book, name='delete_book'),
    path('update_book/<int:book_id>/', views.update_book, name='update_book'),
]
