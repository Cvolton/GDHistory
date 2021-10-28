from history.models import LevelRecord

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Deletes all LevelRecords'

	def handle(self, *args, **options):
		level_records = LevelRecord.objects.all()
		for record in level_records:
			record.delete()