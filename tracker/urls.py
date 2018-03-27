from django.urls import path

from . import views

app_name = 'tracker'
urlpatterns = [
    path('posts/', views.IndexView.as_view(), name='index'),
    path('tracker/', views.TrackerListView.as_view(), name='tracker_list'),
    path('tracker/<int:pk>/', views.TrackerDetailView.as_view(), name='tracker_detail'),
]