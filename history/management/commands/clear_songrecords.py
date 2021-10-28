from history.models import SongRecord

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Deletes all SongRecords'

	def handle(self, *args, **options):
		level_records = SongRecord.objects.all()
		for record in level_records:
			record.delete()