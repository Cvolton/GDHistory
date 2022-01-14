from history.models import LevelRecord
from history.constants import MiscConstants
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def do_updating(self, records):
		record_count = records.count()
		i = 1
		for record in records:
			print(f"{i} / {record_count} - Updating {record.level.online_id}")
			record.cache_is_public = record.level.is_public
			#record.save()
			i += 1

		LevelRecord.objects.bulk_update(records, ['cache_is_public'])

	def handle(self, *args, **options):
		self.do_updating(LevelRecord.objects.prefetch_related('level').filter(cache_is_public=False).exclude(level__is_public=False))
		self.do_updating(LevelRecord.objects.prefetch_related('level').filter(cache_is_public=True).exclude(level__is_public=True))
		self.do_updating(LevelRecord.objects.prefetch_related('level').filter(cache_is_public=None).exclude(level__is_public=None))

		print("Done")