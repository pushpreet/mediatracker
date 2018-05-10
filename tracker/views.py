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
    user = User.objects.get(id=1) # user which is logged in
    user_trackers = Tracker.objects.filter(created_by=user) # trackers which this user has created
    user_posts = Post.objects.filter(trackers_in=user_trackers).distinct() # all posts which belong to these trackers and without duplication
    
    q = request.GET.get('q')
    selected_trackers = request.GET.getlist('trackers')
    selected_tracker_categories = request.GET.getlist('tracker_categories')
    selected_time = request.GET.get('timeFrom', '')
    selected_relevancy = request.GET.get('relevancy', '')

    query = None
    rank_annotation = None
    required_values = ['pk']

    filtered_posts = None

    if q:
        query = SearchQuery(q)
        rank_annotation = SearchRank(F('search_document'), query)
        values.append('rank')
    
    # Start with a .none() queryset just so we can union stuff onto it
    qs = Post.objects.annotate(
        type=models.Value('empty', output_field=models.CharField())
    )
    # add rank as annotation
    if q:
        qs = qs.annotate(rank=rank_annotation)
    qs = qs.values(*required_values).none()
        
    tracker_counts = {}
    tracker_category_counts = {}
    relevancy_counts = {'Starred': 0, 'Removed': 0}

    for tracker in selected_trackers:
        qs = qs.filter()

    for post in filtered_posts:
        for tracker in post.trackers.all():
            if tracker.name in tracker_counts:
                tracker_counts[tracker.name] += 1
            else:
                tracker_counts[tracker.name] = 1

            if tracker.category.name in tracker_category_counts:
                tracker_category_counts[tracker.category.name] += 1
            else:
                tracker_category_counts[tracker.category.name] = 1

    tracker_counts = sorted(
        [
            {'name': name, 'count': value}
            for name, value in list(tracker_counts.items())
        ],
        key=lambda t: t['count'], reverse=True
    )

    tracker_category_counts = sorted(
        [
            {'name': name, 'count': value}
            for name, value in list(tracker_category_counts.items())
        ],
        key=lambda t: t['count'], reverse=True
    )
    # page = request.GET.get('page', 1)
    # paginator = Paginator(filtered_posts, 20)
    
    # try:
    #     filtered_posts_page = paginator.page(page)
    # except PageNotAnInteger:
    #     filtered_posts_page = paginator.page(1)
    # except EmptyPage:
    #     filtered_posts_page = paginator.page(paginator.num_pages)
    
    filtered_posts_page = filtered_posts

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
        data['trackers'] = post.trackers

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
        'q': q,
        'total': len(filtered_posts_page_data),
        'filters': [
            {'type': 'tracker_category', 'counts': tracker_category_counts},
            {'type': 'tracker', 'counts': tracker_counts},
        ],
        # 'page': paginator.page,
    }

    return render(request, 'tracker/post_list.html', context)

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

def delete_tracker(request):
    tracker_id = request.POST.get('tracker-id', False)
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
                data['removed'] = 'true'
            
            elif post_relevancy[0].relevancy == 2: # already irrelevant
                post_relevancy[0].delete()
                data['removed'] = 'false'
            
            elif post_relevancy[0].relevancy == 1: # marked starred
                post_relevancy[0].relevancy = 2
                data['removed'] = 'true'
        
        elif action == 'toggle_read':
            post_read = user.read_posts.filter(uuid=post.uuid)
            
            if not post_read: # not read
                user.read_posts.add(post)
                data['read'] = 'true'
            
            else: # read
                post_read[0].delete()
                data['read'] = 'false'

        return HttpResponse(JsonResponse(data), content_type="application/json")