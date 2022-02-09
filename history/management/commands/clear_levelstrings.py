from history.models import LevelString

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Deletes all SongRecords'

	def handle(self, *args, **options):
		LevelString.objects.all().delete()