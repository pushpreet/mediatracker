from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect, Http404, JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F

from .models import Post, Tracker, User, TrackerCategory, UserPostRelevant

def post_list(request):
    filtered_posts = Post.objects.all().order_by('-published')
    
    q = request.GET.get('q')
    if q:
        query = SearchQuery(q)
        filtered_posts = Post.objects.filter(search_document=query).annotate(rank=SearchRank(F('search_document'), query)).order_by('-rank')

    tracker_list = set()
    tracker_category_list = set()
    for post in filtered_posts:
        for tracker in post.trackers.all():
            tracker_list.add(tracker)
            tracker_category_list.add(tracker.category)

    page = request.GET.get('page', 1)
    paginator = Paginator(filtered_posts, 20)
    
    try:
        filtered_posts_page = paginator.page(page)
    except PageNotAnInteger:
        filtered_posts_page = paginator.page(1)
    except EmptyPage:
        filtered_posts_page = paginator.page(paginator.num_pages)
    
    user = User.objects.get(id=1)

    filtered_posts_page_data = []

    for post in filtered_posts_page:
        data = {}
        data['uuid'] = post.uuid
        data['url'] = post.url
        data['title'] = post.title
        data['main_image'] = post.main_image
        data['author'] = post.author
        data['site_full'] = post.site_full
        data['published'] = post.published
        data['text'] = post.text

        post_relevancy = UserPostRelevant.objects.filter(user=user, post=post)
        post_read = User.objects.filter(id=user.id, read_posts=post)

        if post_relevancy:
            if post_relevancy[0].relevancy == 1:
                data['starred'] = 'true'
                data['irrelevant'] = 'false'
            
            if post_relevancy[0].relevancy == 2:
                data['starred'] = 'false'
                data['irrelevant'] = 'true'
        
        if post_read:
            data['read'] = 'true'
        else:
            data['read'] = 'false'
        
        filtered_posts_page_data.append(data)

    context = {
        'latest_post_list': filtered_posts_page_data,
        'tracker_list': tracker_list,
        'tracker_category_list': tracker_category_list,
        'q': q,
        'total': paginator.count,
        'page': paginator.page,
    }

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

def edit_tracker(request):
    tracker_id = request.POST.get('tracker-id', False)
    tracker_name = request.POST.get('tracker-name', False)
    tracker_query = request.POST.get('query', False)

    if tracker_id:
        tracker = Tracker.objects.get(id=tracker_id)

        tracker.name = tracker_name
        tracker.query = tracker_query

        tracker.save()

    return HttpResponseRedirect(reverse('tracker:tracker_list'))

def set_user_attr(request):
    if request.method == "POST":
        post_id = request.POST.get('post_id', None)
        user_id = request.POST.get('user_id', None)
        action = request.POST.get('action', None)
        
        if (post_id is None) or (user_id is None) or (action is None):
            raise Http404("Insufficient data provided.")

        data = {}

        user = User.objects.get(id=user_id)
        post = Post.objects.get(uuid=post_id)

        if action == 'toggle_star':
            post_relevancy = UserPostRelevant.objects.filter(user=user, post=post)
            
            if not post_relevancy:  # neither starred not irrelevant
                UserPostRelevant.objects.create(user=user, post=post, relevancy=1)
                data['starred'] = 'true'
            
            elif post_relevancy[0].relevancy == 1: # already starred
                post_relevancy[0].delete()
                data['starred'] = 'false'
            
            elif post_relevancy[0].relevancy == 2: # marked irrelevant
                post_relevancy[0].relevancy = 1
                data['starred'] = 'true'
        
        elif action == 'toggle_irrelevant':
            post_relevancy = UserPostRelevant.objects.filter(user=user, post=post)
            
            if not post_relevancy:  # neither starred not irrelevant
                UserPostRelevant.objects.create(user=user, post=post, relevancy=2)
                data['irrelevant'] = 'true'
            
            elif post_relevancy[0].relevancy == 2: # already irrelevant
                post_relevancy[0].delete()
                data['irrelevant'] = 'false'
            
            elif post_relevancy[0].relevancy == 1: # marked starred
                post_relevancy[0].relevancy = 2
                data['irrelevant'] = 'true'
        
        elif action == 'toggle_read':
            post_read = user.read_posts.filter(uuid=post.uuid)
            
            if not post_read: # not read
                user.read_posts.add(post)
                data['read'] = 'true'
            
            else: # read
                post_read[0].delete()
                data['read'] = 'false'

        return HttpResponse(JsonResponse(data), content_type="application/json")