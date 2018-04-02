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
    color = models.CharField(max_length=6, default='e67e22')
    created_by = models.ForeignKey(User, models.SET_NULL, null=True)
    category = models.ForeignKey(TrackerCategory, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def update(self):
        webhoseio.config(token='e187b1d6-59c5-4b3b-9614-1c42b3e3658e')
        output = webhoseio.query("filterWebContent", {"q": self.query})

        previous_posts = [post.uuid for post in Post.objects.all()]
        print(previous_posts)
        for post in output['posts']:
            if post['thread']['uuid'] not in previous_posts:
                Post.objects.create(
                    uuid = post['thread']['uuid'],
                    url = post['thread']['url'],
                    site_full = post['thread']['site_full'],
                    site_categories = post['thread']['site_categories'],
                    title = post['thread']['title_full'],
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
                    tracker = self
                )
        
        return True

class Post(models.Model):
    uuid = models.CharField(primary_key=True, max_length=40)
    url = models.URLField(max_length=500)
    site_full = models.URLField(max_length=500)
    site_categories = models.TextField()
    title = models.CharField(max_length=255)
    published = models.DateTimeField()
    site_type = models.CharField(max_length=30)
    country = models.CharField(max_length=30)
    main_image = models.URLField(max_length=500, null=True)
    performance_score = models.PositiveSmallIntegerField()
    domain_rank = models.PositiveIntegerField(null=True)
    author = models.CharField(max_length=200)
    text = models.TextField()
    language = models.CharField(max_length=30)
    entities = models.TextField()
    social = models.TextField()
    tracker = models.ForeignKey(Tracker, on_delete=models.CASCADE)

    def __str__(self):
        return self.title