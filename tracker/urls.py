from django.urls import path
from django.http import HttpResponseRedirect
from django.urls import reverse

from . import views

app_name = 'tracker'
urlpatterns = [
    path('', lambda r: HttpResponseRedirect(reverse('tracker:post_list'))),
    path('posts/', views.post_list, name='post_list'),
    path('posts/<str:post_uuid>/', views.post_detail, name='post_detail'),
    path('tracker/', views.TrackerListView.as_view(), name='tracker_list'),
    path('tracker/add-category/', views.add_tracker_category, name='add_category'),
    path('tracker/delete-category/', views.delete_tracker_category, name='delete_category'),
    path('tracker/add-tracker/', views.add_tracker, name='add_tracker'),
    path('tracker/<int:tracker_id>/refresh/', views.refresh_tracker, name='refresh'),
    path('tracker/edit-tracker/', views.edit_tracker, name='edit_tracker'),
    path('tracker/delete-tracker/', views.delete_tracker, name='delete_tracker'),
    path('posts/api/user-attr/', views.set_user_attr, name='set_user_attr'),
]