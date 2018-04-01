from django.urls import path

from . import views

app_name = 'tracker'
urlpatterns = [
    path('posts/', views.IndexView.as_view(), name='index'),
    path('posts/<str:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('tracker/', views.TrackerListView.as_view(), name='tracker_list'),
    path('tracker/<int:pk>/', views.TrackerDetailView.as_view(), name='tracker_detail'),
    path('tracker/<int:tracker_id>/refresh/', views.refresh_tracker, name='refresh'),
]