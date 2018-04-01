from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Post, Tracker

# Create your views here.
class IndexView(generic.ListView):
    template_name = 'tracker/index.html'
    context_object_name = 'latest_post_list'

    def get_queryset(self):
        """ Return the last 10 posts. """
        return Post.objects.all().order_by('-published')

class PostDetailView(generic.DetailView):
    model = Post
    template_name = 'tracker/post_detail.html'

class TrackerListView(generic.ListView):
    template_name = 'tracker/tracker_list.html'
    context_object_name = 'tracker_list'

    def get_queryset(self):
        """ Return the last 10 posts. """
        return Tracker.objects.all().order_by('-last_modified')

class TrackerDetailView(generic.DetailView):
    model = Tracker
    template_name = 'tracker/tracker_detail.html'

def refresh_tracker(request, tracker_id):
    tracker = get_object_or_404(Tracker, pk=tracker_id)
    print(tracker)
    
    if tracker.update():
        return HttpResponseRedirect(reverse('tracker:index'))
