from history.models import LevelRecord
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def handle(self, *args, **options):
		records = LevelRecord.objects.filter(record_type=LevelRecord.RecordType.GET).exclude(level__is_public=True).prefetch_related('level')
		record_count = records.count()
		i = 1
		for record in records:
			print(f"{i} / {record_count} - Updating {record.level.online_id}")
			record.level.is_public = True
			record.level.save()
			i += 1

		print("Done")