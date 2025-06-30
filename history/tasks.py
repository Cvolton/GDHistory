from celery import shared_task

from .models import Level

import math

@shared_task
def revalidate_cache_level(online_id):
	Level.objects.get(online_id=online_id).revalidate_cache()
 
def batch_update_levels(params):
    max_level_id = Level.objects.order_by('-pk').first().pk if Level.objects.exists() else 0
    batch_size = 100000
    for i in range(0, math.ceil(max_level_id / batch_size)):
        start = i * batch_size
        end = (i + 1) * batch_size

        levels_to_revalidate = Level.objects.filter(pk__gt=start, pk__lt=end)
        if not levels_to_revalidate.exists():
            continue
        levels_to_revalidate.update(**params)
        print(f"Forced {params} for levels from {start} to {end}")

@shared_task
def revalidate_cache_all():
    batch_update_levels({'cache_needs_revalidation': True})
 
@shared_task
def search_update_all():
    batch_update_levels({'cache_needs_search_update': True})