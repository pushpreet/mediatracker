from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect, Http404, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Count
import django.db.models as models

from .models import Post, Tracker, User, TrackerCategory, UserPostRelevant

def post_list(request):
    user = User.objects.get(id=1) # user which is logged in
    user_trackers = Tracker.objects.filter(created_by=user) # trackers which this user has created
    user_posts = Post.objects.filter(trackers__in=user_trackers).distinct() # all posts which belong to these trackers and without duplication
    
    q = request.GET.get('q')
    selected_trackers = request.GET.get('tracker')
    selected_tracker_categories = request.GET.get('tracker_category')
    selected_relevancy = request.GET.get('relevancy', None)

    query = None
    rank_annotation = None

    filtered_posts = None

    if q:
        query = SearchQuery(q)
        rank_annotation = SearchRank(models.F('search_document'), query)

        filtered_posts = user_posts.filter(search_document=query).annotate(rank=rank_annotation).order_by('-rank')
    else:
        filtered_posts = user_posts.order_by('-published')
    
    # filters
    tracker_counts = {}
    tracker_category_counts = {}
    relevancy_counts = {'Starred': 0, 'Removed': 0}

    tracker_counts = user_trackers.filter(post__in=filtered_posts).annotate(count=Count('post')).values('id', 'name', 'count').order_by('-count')
    tracker_category_counts = TrackerCategory.objects.filter(tracker__post__in=filtered_posts).annotate(count=Count('tracker')).values('id', 'name', 'count').order_by('-count')
    relevancy_counts = UserPostRelevant.objects.filter(post__in=filtered_posts).values('relevancy').annotate(count=Count('relevancy'))
    relevancy_counts = [
        {'id': item['relevancy'], 'name': ('Starred' if (item['relevancy']==1) else 'Removed'), 'count': item['count']}
        for item in relevancy_counts
    ]

    if selected_trackers:
        filtered_posts = filtered_posts.filter(trackers__id__in=selected_trackers)
        selected_trackers = int(selected_trackers)
    
    if selected_tracker_categories:
        filtered_posts = filtered_posts.filter(trackers__category__id__in=selected_tracker_categories)
        selected_tracker_categories = int(selected_tracker_categories)

    if selected_relevancy:
        filtered_posts = filtered_posts.filter(userpostrelevant__relevancy=selected_relevancy)
        selected_relevancy = int(selected_relevancy)
    else:
        filtered_posts = filtered_posts.exclude(userpostrelevant__relevancy=UserPostRelevant.REMOVED)

    filtered_posts_data = []

    for post in filtered_posts:
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
            if post_relevancy[0].relevancy == UserPostRelevant.STARRED:
                data['starred'] = 'true'
                data['removed'] = 'false'
            
            if post_relevancy[0].relevancy == UserPostRelevant.REMOVED:
                data['starred'] = 'false'
                data['removed'] = 'true'
        
        if post_read:
            data['read'] = 'true'
        else:
            data['read'] = 'false'
        
        filtered_posts_data.append(data)
    
    paginator = Paginator(filtered_posts_data, 30)

    if request.is_ajax():
        page_number = request.GET.get('page')
        try:
            filtered_posts_data = paginator.page(page_number)
        except PageNotAnInteger as err:
            return HttpResponseBadRequest(content='Error when processing Response: {}'.format(err))
        except EmptyPage as err:
            return HttpResponseBadRequest(content='Error when processing Response: {}'.format(err))
        
        return render(request, 'tracker/post_list_page.html', {'filtered_posts': filtered_posts_data})
    
    else:
        filtered_posts_data = paginator.page(1)

        context = {
            'filtered_posts': filtered_posts_data,
            'q': q,
            'total': paginator.count,
            'filters': [
                # {'type': 'tracker_category', 'counts': tracker_category_counts, 'selected': selected_tracker_categories},
                {'type': 'tracker', 'counts': tracker_counts, 'selected': selected_trackers},
                {'type': 'relevancy', 'counts': relevancy_counts, 'selected': selected_relevancy},
            ],
            'page': paginator.page,
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
            
            elif post_relevancy[0].relevancy == UserPostRelevant.STARRED: # already starred
                post_relevancy[0].delete()
                data['starred'] = 'false'
            
            elif post_relevancy[0].relevancy == UserPostRelevant.REMOVED: # marked removed
                post_relevancy[0].relevancy = UserPostRelevant.STARRED
                data['starred'] = 'true'
                data['removed'] = 'false'
                post_relevancy[0].save()
        
        elif action == 'toggle_removed':
            post_relevancy = UserPostRelevant.objects.filter(user=user, post=post)
            
            if not post_relevancy:  # neither starred not irrelevant
                UserPostRelevant.objects.create(user=user, post=post, relevancy=2)
                data['removed'] = 'true'
            
            elif post_relevancy[0].relevancy == UserPostRelevant.REMOVED: # already removed
                post_relevancy[0].delete()
                data['removed'] = 'false'
            
            elif post_relevancy[0].relevancy == UserPostRelevant.STARRED: # marked starred
                post_relevancy[0].relevancy = UserPostRelevant.REMOVED
                data['removed'] = 'true'
                data['starred'] = 'false'
                post_relevancy[0].save()
        
        elif action == 'toggle_read':
            post_read = user.read_posts.filter(uuid=post.uuid)
            
            if not post_read: # not read
                user.read_posts.add(post)
                data['read'] = 'true'
            
            else: # read
                user.read_posts.remove(post_read[0])
                data['read'] = 'false'

        return HttpResponse(JsonResponse(data), content_type="application/json")