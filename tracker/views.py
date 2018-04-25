from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F

from .models import Post, Tracker, User, TrackerCategory

def post_list(request):
    context = {}
    latest_post_list = Post.objects.all().order_by('-published')
    
    keywords = request.GET.get('q')
    if keywords:
        query = SearchQuery(keywords)
        latest_post_list = Post.objects.filter(search_document=query).annotate(rank=SearchRank(F('search_document'), query)).order_by('-rank')
        # title_vector = SearchVector('title', weight='A')
        # text_vector = SearchVector('text', weight='B')
        # vectors = title_vector + text_vector
        # latest_post_list = latest_post_list.annotate(search=vectors).filter(search=query)
        # latest_post_list = latest_post_list.annotate(rank=SearchRank(vectors, query)).order_by('-rank')

    tracker_list = set()
    tracker_category_list = set()
    for post in latest_post_list:
        for tracker in post.trackers.all():
            tracker_list.add(tracker)
            tracker_category_list.add(tracker.category)

    context['tracker_list'] = tracker_list
    context['tracker_category_list'] = tracker_category_list

    page = request.GET.get('page', 1)
    paginator = Paginator(latest_post_list, 20)
    
    try:
        context['latest_post_list'] = paginator.page(page)
    except PageNotAnInteger:
        context['latest_post_list'] = paginator.page(1)
    except EmptyPage:
        context['latest_post_list'] = paginator.page(paginator.num_pages)

    return render(request, 'tracker/post_list.html', {'context': context})

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
        return HttpResponseRedirect(reverse('tracker:post_list'))

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