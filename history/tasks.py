from celery import shared_task

from .models import Level

import math

@shared_task
def revalidate_cache_level(online_id):
	Level.objects.get(online_id=online_id).revalidate_cache()
 
@shared_task
def revalidate_cache_all():
    max_level_id = Level.objects.order_by('-pk').first().pk if Level.objects.exists() else 0
    batch_size = 100000
    for i in range(0, math.ceil(max_level_id / batch_size)):
        start = i * batch_size
        end = (i + 1) * batch_size

        levels_to_revalidate = Level.objects.filter(pk__gt=start, pk__lt=end)
        if not levels_to_revalidate.exists():
            continue
        levels_to_revalidate.update(cache_needs_revalidation=True)
        print(f"Forced revalidation for levels from {start} to {end}")