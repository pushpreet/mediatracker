from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Post, Tracker, User, TrackerCategory

def index(request):
    latest_post_list = Post.objects.all().order_by('-published')
    page = request.GET.get('page', 1)
    paginator = Paginator(latest_post_list, 20)
    
    try:
        latest_posts = paginator.page(page)
    except PageNotAnInteger:
        latest_posts = paginator.page(1)
    except EmptyPage:
        latest_posts = paginator.page(paginator.num_pages)

    return render(request, 'tracker/index.html', {'latest_post_list': latest_posts})

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
    
    if tracker.update():
        return HttpResponseRedirect(reverse('tracker:index'))

def delete_tracker(request, tracker_id):
    tracker = get_object_or_404(Tracker, pk=tracker_id)
    tracker.delete()
    
    return HttpResponseRedirect(reverse('tracker:tracker_list'))

def add_tracker(request):
    tracker_name = request.POST.get('tracker-name', False)
    tracker_query = request.POST.get('query', False)
    
    Tracker.objects.create(
        name = tracker_name,
        query = tracker_query,
        color = '#e67e22',
        last_modified = timezone.now(),
        last_updated = timezone.now(),
        created_by = User.objects.get(name = 'Pushpreet'),
        category = TrackerCategory.objects.get(name = 'Test')
    )

    return HttpResponseRedirect(reverse('tracker:tracker_list'))