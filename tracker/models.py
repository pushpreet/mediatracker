import uuid
import webhoseio
import ast
from django.db import models
from django.utils import timezone
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from datetime import timedelta, datetime

from django.db.utils import DataError

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    relevent_posts = models.ManyToManyField('Post', through='UserPostRelevant', related_name='relevant_posts')
    read_posts = models.ManyToManyField('Post', related_name='read_posts')

    def __str__(self):
        return self.name

class TrackerCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Tracker(models.Model):
    name = models.CharField(max_length=200)
    query = models.TextField(null=True)
    color = models.CharField(max_length=7, default='#e67e22')
    last_modified = models.DateTimeField()
    last_updated = models.DateTimeField(null=True)
    auto_refresh = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, models.SET_NULL, null=True)
    category = models.ForeignKey(TrackerCategory, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def update(self):
        crawledFrom = self.last_updated.timestamp()
        if abs(self.last_updated - self.last_modified) < timedelta(seconds=1):
            crawledFrom = (timezone.now() - timedelta(days=3)).timestamp()
        
        webhoseio.config(token='e187b1d6-59c5-4b3b-9614-1c42b3e3658e')
        output = webhoseio.query(
            "filterWebContent", 
            {
                "q": self.query,
                "ts": crawledFrom,
                "language": "english",
                "site_type": "news",
            })
        
        output = output['posts']
        while True:
            temp = webhoseio.get_next()
            output += temp['posts']
            if temp['moreResultsAvailable'] <= 0:
                break

        previous_posts_uuid = []
        previous_posts_title = []
        
        if len(output) > 0:
            previous_posts_uuid = [post.uuid for post in Post.objects.all()]
            previous_posts_title = [post.title.lower() for post in Post.objects.all()]

        for post in output:
            if post['thread']['uuid'] in previous_posts_uuid:
                old_post = Post.objects.get(uuid = post['thread']['uuid'])
                if self not in old_post.trackers.all():
                    old_post.trackers.add(self)
            
            elif post['thread']['title'].lower() in previous_posts_title:
                old_post = Post.objects.get(title__iexact = post['thread']['title'])
                if self not in old_post.trackers.all():
                    old_post.trackers.add(self)

            else:
                try:
                    new_post = Post(
                        uuid = post['thread']['uuid'],
                        url = post['thread']['url'],
                        site_full = post['thread']['site_full'],
                        site_categories = post['thread']['site_categories'],
                        title = post['thread']['title'][:1024],
                        published = post['thread']['published'],
                        site_type = post['thread']['site_type'],
                        country = post['thread']['country'],
                        main_image = post['thread']['main_image'],
                        performance_score = post['thread']['performance_score'],
                        domain_rank = post['thread']['domain_rank'],
                        author = post['author'],
                        text = post['text'],
                        language = post['language'],
                        entities = post['entities'],
                        social = post['thread']['social'],
                    )

                    new_post.save()
                    new_post.trackers.add(self)
                    
                    previous_posts_uuid.append(post['thread']['uuid'])
                    previous_posts_title.append(post['thread']['title'].lower())
                
                except DataError as err:
                    print("Error: %s"%(err))
                    print(post)

        self.last_updated = timezone.now()
        self.save()
        
        return True

class Post(models.Model):
    uuid = models.CharField(primary_key=True, max_length=40)
    url = models.URLField(max_length=512)
    site_full = models.URLField(max_length=512)
    site_categories = models.TextField()
    title = models.CharField(max_length=1024)
    published = models.DateTimeField()
    site_type = models.CharField(max_length=30)
    country = models.CharField(max_length=30)
    main_image = models.URLField(max_length=512, null=True)
    performance_score = models.PositiveSmallIntegerField()
    domain_rank = models.PositiveIntegerField(null=True)
    author = models.CharField(max_length=255)
    text = models.TextField()
    language = models.CharField(max_length=30)
    entities = models.TextField()
    social = models.TextField()
    trackers = models.ManyToManyField(Tracker)
    search_document = SearchVectorField(null=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_document'])
        ]

    def index_components(self):
        return {
            'A': self.title,
            'B': ' '.join(self.get_entities()),
            'C': self.text,
        }

    def get_entities(self):
        entities = ast.literal_eval(str(self.entities))
        return [item['name'] for item in (entities['persons'] + entities['organizations'] + entities['locations'])]

    def __str__(self):
        return self.title

class UserPostRelevant(models.Model):
    DEFAULT = 0
    STARRED = 1
    REMOVED = 2

    RELEVANCY_CHOICES = (
        (DEFAULT, 'Default'),
        (STARRED, 'Starred'),
        (REMOVED, 'Removed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    relevancy = models.PositiveSmallIntegerField(default=0, choices=RELEVANCY_CHOICES)