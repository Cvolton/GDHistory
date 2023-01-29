from celery import shared_task

from .models import Level

@shared_task
def revalidate_cache_level(online_id):
	Level.objects.get(online_id=online_id).revalidate_cache()