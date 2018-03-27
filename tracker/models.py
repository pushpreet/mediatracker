import uuid
import webhoseio
from django.db import models

# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()

    def __str__(self):
        return self.name

class TrackerCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Tracker(models.Model):
    name = models.CharField(max_length=200)
    last_modified = models.DateTimeField(auto_now=True)
    query = models.TextField(null=True)
    created_by = models.ForeignKey(User, models.SET_NULL, null=True)
    category = models.ForeignKey(TrackerCategory, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def update(self):
        webhoseio.config(token='e187b1d6-59c5-4b3b-9614-1c42b3e3658e')
        output = webhoseio.query("filterWebContent", {"q", this.query})

        previous_posts = [post['uuid'] for post in Post.objects.all()]
        for post in output['posts']:
            if post['uuid'] not in previous_posts:
                Post.objects.create(
                    uuid = post['uuid'],
                    url = post['url'],
                    site = post['site_full'],
                    site_categories = post['site_category'],
                    title = post['title_full'],
                    published = post['published'],
                    site_type = post['site_type'],
                    country = post['country'],
                    main_image = post['main_image'],
                    performance_score = post['performance_score'],
                    domain_rank = post['domain_rank'],
                    author = post['author'],
                    text = post['text'],
                    language = post['langauge'],
                    entities = post['entities'],
                    social = post['social'],
                    tracker = this.primary_key
                )

class Post(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField()
    site = models.URLField()
    site_categories = models.TextField()
    title = models.CharField(max_length=255)
    published = models.DateTimeField()
    site_type = models.CharField(max_length=30)
    country = models.CharField(max_length=30)
    main_image = models.URLField()
    performance_score = models.PositiveSmallIntegerField()
    domain_rank = models.PositiveSmallIntegerField()
    author = models.CharField(max_length=200)
    text = models.TextField()
    language = models.CharField(max_length=30)
    entities = models.TextField()
    social = models.TextField()
    tracker = models.ForeignKey(Tracker, on_delete=models.CASCADE)

    def __str__(self):
        return self.title