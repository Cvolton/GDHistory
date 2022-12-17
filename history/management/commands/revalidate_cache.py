from history.models import Level, Song

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Revalidates level cache'

	def handle(self, *args, **options):
		levels = Level.objects.filter(cache_needs_revalidation=True).prefetch_related('levelrecord_set__save_file').prefetch_related('levelrecord_set__level_string')
		level_count = levels.count()
		for i in range(0,level_count):
			level = levels[0:1]
			print(f"{i} / {level_count} - Updating {level.online_id}")
			level.revalidate_cache()

		print("Done")