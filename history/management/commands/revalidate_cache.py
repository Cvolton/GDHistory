from history.models import Level, Song

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Revalidates level cache'

	def recalculate_levels(self, levels):
		level_count = levels.count()
		for i in range(0,level_count):
			level = levels[0:1][0]
			print(f"{i} / {level_count} - Updating {level.online_id}")
			level.revalidate_cache()

	def handle(self, *args, **options):
		levels = Level.objects.filter(cache_needs_revalidation=True).prefetch_related('levelrecord_set__save_file').prefetch_related('levelrecord_set__level_string')
		print("pass 1")
		self.recalculate_levels(levels.filter(cache_submitted=None))
		print("pass 2")
		self.recalculate_levels(levels)

		print("Done")