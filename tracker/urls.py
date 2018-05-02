from django.urls import path
from django.http import HttpResponseRedirect
from django.urls import reverse

from . import views

app_name = 'tracker'
urlpatterns = [
    path('', lambda r: HttpResponseRedirect(reverse('tracker:post_list'))),
    path('posts/', views.post_list, name='post_list'),
    path('posts/<str:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('tracker/', views.TrackerListView.as_view(), name='tracker_list'),
    path('tracker/<int:pk>/', views.TrackerDetailView.as_view(), name='tracker_detail'),
    path('tracker/<int:tracker_id>/refresh/', views.refresh_tracker, name='refresh'),
    path('tracker/<int:tracker_id>/delete/', views.delete_tracker, name='delete'),
    path('tracker/add/', views.add_tracker, name='add'),
    path('tracker/edit/', views.edit_tracker, name='edit'),
    path('posts/api/user-attr/', views.set_user_attr, name='set_user_attr'),
]