from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect, Http404, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Count, Sum, CharField, Case, When, Value, IntegerField, Q
from datetime import timedelta, datetime
from django.utils import timezone
import django.db.models as models

from .models import Post, Tracker, User, TrackerCategory, UserPostRelevant

def post_list(request):
    ### get all posts by the current user
    user = User.objects.get(id=1) # user which is logged in
    user_trackers = Tracker.objects.filter(created_by=user) # trackers which this user has created
    user_posts = Post.objects.filter(trackers__in=user_trackers).distinct() # all posts which belong to these trackers and without duplication
    
    ### get all form paramters
    q = request.GET.get('q')
    selected_tracker = request.GET.get('tracker', None)
    selected_tracker_category = request.GET.get('tracker_category', None)
    selected_relevancy = request.GET.get('relevancy', None)
    selected_read_status = request.GET.get('read_status', None)
    selected_time_from = request.GET.get('time_from', None)
    
    query = None
    rank_annotation = None
    filtered_posts = None

    ### get and order all which match the query
    if q:
        query = SearchQuery(q)
        rank_annotation = SearchRank(models.F('search_document'), query)

        filtered_posts = user_posts.filter(search_document=query).annotate(rank=rank_annotation).order_by('-rank')
    else:
        filtered_posts = user_posts.order_by('-published')
    
    ### filter posts by form selection
    if selected_tracker_category:
        selected_tracker_category = int(selected_tracker_category)
        filtered_posts = filtered_posts.filter(trackers__category__id=selected_tracker_category)

    if selected_tracker:
        selected_tracker = int(selected_tracker)
        filtered_posts = filtered_posts.filter(trackers__id=selected_tracker)
    
    if selected_relevancy:
        selected_relevancy = int(selected_relevancy)
        filtered_posts = filtered_posts.filter(userpostrelevant__relevancy=selected_relevancy)
    else:
        filtered_posts = filtered_posts.exclude(userpostrelevant__relevancy=UserPostRelevant.REMOVED)
    
    if selected_read_status:
        if selected_read_status == 'true':
            filtered_posts = filtered_posts.filter(read_posts=user)
        if selected_read_status == 'false':
            filtered_posts = filtered_posts.exclude(read_posts=user)

    if selected_time_from:
        selected_time_from = int(selected_time_from)
        filtered_posts = filtered_posts.filter(published__gt=datetime.fromtimestamp(selected_time_from/1000))
    
    ### add starred, removed and read flags
    filtered_posts = filtered_posts.annotate(
        starred=Case(
            When(userpostrelevant__relevancy=1, userpostrelevant__user=user, then=Value('true')),
            defualt=Value('false'), 
            output_field=CharField()
        ),
        removed=Case(
            When(userpostrelevant__relevancy=2, userpostrelevant__user=user, then=Value('true')),
            defualt=Value('false'), 
            output_field=CharField()
        ),
        read=Case(
            When(read_posts=user, then=Value('true')),
            defualt=Value('false'), 
            output_field=CharField()
        ),
    )

    ### calculate counts for filters
    tracker_counts = user_trackers.annotate(
        count=Count(Case(
            When(post__in=filtered_posts, then=Value(1))
        ))
    ).values('id', 'name', 'count').order_by('-count')

    tracker_category_counts = TrackerCategory.objects.annotate(count=Count(Case(
            When(tracker__post__in=filtered_posts, then=Value(1))
        ))
    ).values('id', 'name', 'count').order_by('-count')

    relevancy_counts = [
        {'id': 1, 'name': 'Starred', 'count': len(filtered_posts.filter(starred='true'))},
        {'id': 2, 'name': 'Removed', 'count': len(filtered_posts.filter(removed='true'))}
    ]

    read_status_counts = [
        {'id': 'true', 'name': 'Marked Read', 'count': len(filtered_posts.filter(read_posts=user))},
        {'id': 'false', 'name': 'Unmarked', 'count': len(filtered_posts.exclude(read_posts=user))}
    ]

    last_day = int((timezone.now().replace(minute=0, second=0, microsecond=0) - timedelta(days=1)).timestamp()*1000)
    last_7_days = int((timezone.now().replace(minute=0, second=0, microsecond=0) - timedelta(days=7)).timestamp()*1000)
    last_30_days = int((timezone.now().replace(minute=0, second=0, microsecond=0) - timedelta(days=30)).timestamp()*1000)
    time_from_counts = [
        {'id': last_day, 'name': 'Last Day', 'count': len(filtered_posts.filter(published__gt=datetime.fromtimestamp(last_day/1000)))},
        {'id': last_7_days, 'name': 'Last 7 Days', 'count': len(filtered_posts.filter(published__gt=datetime.fromtimestamp(last_7_days/1000)))},
        {'id': last_30_days, 'name': 'Last 30 Days', 'count': len(filtered_posts.filter(published__gt=datetime.fromtimestamp(last_30_days/1000)))}
    ]

    ### paginate
    paginator = Paginator(filtered_posts, 30)
    
    ### if ajax request, return only page
    if request.is_ajax():
        page_number = request.GET.get('page')
        try:
            filtered_posts = paginator.page(page_number)
        except PageNotAnInteger as err:
            return HttpResponseBadRequest(content='Error when processing Response: {}'.format(err))
        except EmptyPage as err:
            return HttpResponseBadRequest(content='Error when processing Response: {}'.format(err))
        
        return render(request, 'tracker/post_list_page.html', {'filtered_posts': filtered_posts})
    
    ### if normal request, send first page
    else:
        filtered_posts = paginator.page(1)
        context = {
            'filtered_posts': filtered_posts,
            'q': q,
            'total': paginator.count,
            'filters': [
                {'type': 'tracker_category', 'counts': tracker_category_counts, 'selected': selected_tracker_category},
                {'type': 'tracker', 'counts': tracker_counts, 'selected': selected_tracker},
                {'type': 'relevancy', 'counts': relevancy_counts, 'selected': selected_relevancy},
                {'type': 'read_status', 'counts': read_status_counts, 'selected': selected_read_status},
                {'type': 'time_from', 'counts': time_from_counts, 'selected': selected_time_from},
            ],
            'page': paginator.page,
        }

        return render(request, 'tracker/post_list.html', context)

def post_detail(request, post_uuid):
    post = Post.objects.get(uuid=post_uuid)
    user = User.objects.get(id=1)

    user.read_posts.add(post)

    return render(request, 'tracker/post_detail.html', {'post': post})

class TrackerListView(generic.ListView):
    template_name = 'tracker/tracker_list.html'
    context_object_name = 'tracker_category_list'

    def get_queryset(self):
        tracker_categories = TrackerCategory.objects.order_by('name').values('id', 'name')
        trackers = Tracker.objects.order_by('category__name', '-last_modified')
        
        for tracker in trackers:
            for category in tracker_categories:
                if category['name'] == tracker.category.name:
                    if 'trackers' not in category.keys():
                        category['trackers'] = [tracker]
                    else:
                        category['trackers'].append(tracker)

        return tracker_categories

def add_tracker_category(request):
    tracker_category_name = request.POST.get('tracker-category-name', False)
    
    TrackerCategory.objects.create(
        name = tracker_category_name,
    )

    return HttpResponseRedirect(reverse('tracker:tracker_list'))

def delete_tracker_category(request):
    tracker_category_id = int(request.POST.get('tracker-category-id', False))
    tracker_category = get_object_or_404(TrackerCategory, pk=tracker_category_id)

    tracker_category.delete()

    return HttpResponseRedirect(reverse('tracker:tracker_list'))

def add_tracker(request):
    tracker_name = request.POST.get('tracker-name', False)
    tracker_query = request.POST.get('query', False)
    tracker_category_id = request.POST.get('tracker-category-id', False)
    
    Tracker.objects.create(
        name = tracker_name,
        query = tracker_query,
        color = '#e67e22',
        last_modified = timezone.now(),
        last_updated = timezone.now(),
        created_by = User.objects.get(name = 'Pushpreet'),
        category = TrackerCategory.objects.get(id = int(tracker_category_id))
    )

    return HttpResponseRedirect(reverse('tracker:tracker_list'))

def refresh_tracker(request, tracker_id):
    tracker = get_object_or_404(Tracker, pk=tracker_id)
    
    if tracker.update():
        return HttpResponseRedirect(reverse('tracker:post_list'))

def edit_tracker(request):
    tracker_id = request.POST.get('tracker-id', False)
    tracker_name = request.POST.get('tracker-name', False)
    tracker_query = request.POST.get('query', False)
    tracker_category_id = request.POST.get('tracker-category-id', False)

    if tracker_id:
        tracker = Tracker.objects.get(id=tracker_id)

        tracker.name = tracker_name
        tracker.query = tracker_query
        tracker.last_modified = timezone.now()
        tracker.category = TrackerCategory.objects.get(id = int(tracker_category_id))
        tracker.save()

    return HttpResponseRedirect(reverse('tracker:tracker_list'))

def delete_tracker(request):
    tracker_id = request.POST.get('tracker-id', False)
    tracker = get_object_or_404(Tracker, pk=tracker_id)
    tracker.delete()
    
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
        
        elif action == 'set_read':
            user.read_posts.add(post)

        return HttpResponse(JsonResponse(data), content_type="application/json")