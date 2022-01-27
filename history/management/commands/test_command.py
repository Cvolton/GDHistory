from history.models import LevelRecord
from history.constants import MiscConstants
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'is test'

	def handle(self, *args, **options):
		print("loading")
		top_record = 0
		records = LevelRecord.objects.all()
		record_count = records.count()
		i = 1
		print("working")
		for record in records:
			if record.relative_upload_date is not None and len(record.relative_upload_date) >= top_record:
				top_record = len(record.relative_upload_date)
				print(f"{i} / {record_count} - {top_record}: {record.level.online_id} - {record.relative_upload_date}")
			i += 1

		print("Done")