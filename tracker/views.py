from django.shortcuts import render
from django.views import generic

from .models import Post, Tracker

# Create your views here.
class IndexView(generic.ListView):
    template_name = 'tracker/index.html'
    context_object_name = 'latest_post_list'

    def get_queryset(self):
        """ Return the last 10 posts. """
        return Post.objects.all().order_by('-published')[:10]

class TrackerListView(generic.ListView):
    template_name = 'tracker/tracker_list.html'
    context_object_name = 'tracker_list'

    def get_queryset(self):
        """ Return the last 10 posts. """
        return Tracker.objects.all().order_by('-last_modified')

class TrackerDetailView(generic.DetailView):
    model = Tracker
    template_name = 'tracker/tracker_detail.html'
