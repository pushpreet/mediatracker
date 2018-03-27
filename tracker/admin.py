from django.contrib import admin

from .models import User, Post, Tracker, TrackerCategory

# Register your models here.
admin.site.register(Post)
admin.site.register(User)
admin.site.register(Tracker)
admin.site.register(TrackerCategory)