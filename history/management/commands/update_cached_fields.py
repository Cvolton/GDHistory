from history.models import LevelRecord, Level
from history.constants import MiscConstants
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def do_is_public_updating(self, records):
		record_count = records.count()
		i = 1
		for record in records:
			print(f"{i} / {record_count} - Updating {record.level.online_id}")
			record.cache_is_public = record.level.is_public
			#record.save()
			i += 1

		LevelRecord.objects.bulk_update(records, ['cache_is_public'], batch_size=1000)

	def do_none_updating(self, records):
		record_count = records.count()
		i = 1
		for record in records:
			print(f"{i} / {record_count} - Updating {record.online_id}")
			record.cache_downloads = record.cache_downloads if record.cache_downloads is not None else 0
			record.cache_likes = record.cache_likes if record.cache_likes is not None else 0
			record.cache_stars = record.cache_stars if record.cache_stars is not None else 0
			#record.save()
			i += 1

		Level.objects.bulk_update(records, ['cache_stars', 'cache_likes', 'cache_downloads'], batch_size=1000)

	def do_search_cache_updating(self, records, status):
		record_count = records.count()
		i = 1
		for record in records:
			print(f"{i} / {record_count} - Updating {record.online_id}")
			record.cache_search_available = status
			#record.save()
			i += 1

		Level.objects.bulk_update(records, ['cache_stars', 'cache_likes', 'cache_downloads'], batch_size=1000)

	def handle(self, *args, **options):
		self.do_is_public_updating(LevelRecord.objects.prefetch_related('level').filter(cache_is_public=False).exclude(level__is_public=False))
		self.do_is_public_updating(LevelRecord.objects.prefetch_related('level').filter(cache_is_public=True).exclude(level__is_public=True))
		self.do_is_public_updating(LevelRecord.objects.prefetch_related('level').filter(cache_is_public=None).exclude(level__is_public=None))

		self.do_none_updating(Level.objects.filter( Q(cache_downloads=None) | Q(cache_likes=None) | Q(cache_stars=None) ))

		self.do_search_cache_updating(Level.objects.filter(is_public=True, hide_from_search=False).exclude(cache_level_name=None).exclude(cache_search_available=True), True)
		self.do_search_cache_updating(Level.objects.filter( Q(is_public=False) | Q( hide_from_search=True) | Q(cache_level_name=None) ).exclude(cache_search_available=False), False)

		print("Done")