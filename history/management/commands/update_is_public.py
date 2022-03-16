from history.models import LevelRecord, LevelRecordType
from history.constants import MiscConstants
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.db import connection

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def handle(self, *args, **options):

		user_whitelist = [21297937]
		records = LevelRecord.objects.filter( Q(level__cache_user_id__in=user_whitelist) | Q(level__cache_stars__gt=0) | Q(level__online_id__lt=MiscConstants.FIRST_2_1_LEVEL) | Q(record_type=LevelRecordType.GET) | ( Q(record_type=LevelRecordType.DOWNLOAD) & Q(server_response__created__gte="2021-11-24 02:10:00+00:00") ) ).filter( Q(level__is_public=None) | Q(level__is_public=False) ).prefetch_related('level')
		record_count = records.count()
		for i in range(0,record_count):
			record = records[0:1]
			record = record[0]
			print(f"{i} / {record_count} - Updating {record.level.online_id}")
			record.level.set_public(True)

		print("Done")