from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.models import Value
from django.contrib.postgres.search import SearchVector
from django.db import transaction
from .models import Post
import operator
from functools import reduce


@receiver(post_save)
def on_save(sender, **kwargs):
    if not issubclass(sender, Post):
        return
    transaction.on_commit(make_updater(kwargs['instance']))


def make_updater(instance):
    components = instance.index_components()
    pk = instance.pk

    def on_commit():
        search_vectors = []
        for weight, text in components.items():
            search_vectors.append(
                SearchVector(Value(text), weight=weight)
            )
        instance.__class__.objects.filter(pk=pk).update(
            search_document=reduce(operator.add, search_vectors)
        )
    return on_commit