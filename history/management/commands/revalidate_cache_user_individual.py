from history.models import GDUser

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Revalidates user cache'

	def add_arguments(self, parser):
		parser.add_argument('users', nargs='+')

	def handle(self, *args, **options):
		total = len(options['users'])
		for i, level in enumerate(options['users']):
			levels = GDUser.objects.filter(online_id=level)
			for level_object in levels:
				print(f"{i} / {total} - Updating {level_object.online_id}")
				level_object.revalidate_cache()

		print("Done")