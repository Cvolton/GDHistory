from history.models import LevelRecord
from history.constants import MiscConstants
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.db import connection

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def handle(self, *args, **options):

		records = LevelRecord.objects.filter( Q(level__online_id__lt=MiscConstants.FIRST_2_1_LEVEL) | Q(record_type=LevelRecord.RecordType.GET) | ( Q(record_type=LevelRecord.RecordType.DOWNLOAD) & Q(server_response__created__gte="2021-11-24 02:10:00+00:00") ) ).filter( Q(level__is_public=None) | Q(level__is_public=False) ).prefetch_related('level')
		record_count = records.count()
		i = 1
		for record in records:
			print(f"{i} / {record_count} - Updating {record.level.online_id}")
			record.level.set_public(True)

			i += 1

		print("Done")