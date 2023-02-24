from history.models import Level, Song

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Revalidates level cache'

	def add_arguments(self, parser):
		parser.add_argument('levels', nargs='+')

	def handle(self, *args, **options):
		total = len(options['levels'])
		for i, level in enumerate(options['levels']):
			levels = Level.objects.filter(online_id=level)
			for level_object in levels:
				print(f"{i} / {total} - Updating {level_object.online_id}")
				level_object.revalidate_cache()

		print("Done")