from history.models import LevelRecord, LevelRecordType, Level, LevelDateEstimation
from history.constants import MiscConstants

from django.db.models import Q
from django.db import connection

def update_is_public():
	user_whitelist = [21297937, 16, 11094602, 20417551]
	records = LevelRecord.objects.filter( Q(level__cache_user_id__in=user_whitelist) | Q(level__cache_stars__gt=0) | Q(level__cache_downloads__gte=1000) | Q(level__online_id__lt=MiscConstants.FIRST_2_1_LEVEL) | Q(record_type=LevelRecordType.GET) | ( Q(record_type=LevelRecordType.DOWNLOAD) & Q(server_response__created__gte="2021-11-24 02:10:00+00:00") ) ).filter( Q(level__is_public=None) | Q(level__is_public=False) ).prefetch_related('level')
	record_count = records.count()
	for i in range(0,record_count):
		record = records[0:1]
		if len(record) < 1:
			return
		record = record[0]
		print(f"{i} / {record_count} - Updating {record.level.online_id}")
		record.level.set_public(True)

def do_is_public_updating(records):
	record_count = records.count()
	i = 1
	for record in records:
		print(f"{i} / {record_count} - Updating {record.level.online_id}")
		record.cache_is_public = record.level.is_public
		#record.save()
		i += 1

	LevelRecord.objects.bulk_update(records, ['cache_is_public'], batch_size=1000)

def do_none_updating(records):
	record_count = records.count()
	i = 1
	for record in records:
		print(f"{i} / {record_count} - Updating {record.online_id}")
		record.cache_downloads = record.cache_downloads if record.cache_downloads is not None else 0
		record.cache_likes = record.cache_likes if record.cache_likes is not None else 0
		record.cache_stars = record.cache_stars if record.cache_stars is not None else 0
		record.cache_needs_search_update = True
		#record.save()
		i += 1

	Level.objects.bulk_update(records, ['cache_stars', 'cache_likes', 'cache_downloads', 'cache_needs_search_update'], batch_size=1000)

def do_search_cache_updating(records, status):
	record_count = records.count()
	i = 1
	for record in records:
		print(f"{i} / {record_count} - Updating {record.online_id}")
		record.cache_search_available = status
		record.cache_needs_search_update = True
		#record.save()
		i += 1

	Level.objects.bulk_update(records, ['cache_search_available', 'cache_needs_search_update'], batch_size=1000)

def update_cached_fields():
	do_is_public_updating(LevelRecord.objects.prefetch_related('level').filter(cache_is_public=False).exclude(level__is_public=False))
	do_is_public_updating(LevelRecord.objects.prefetch_related('level').filter(cache_is_public=True).exclude(level__is_public=True))
	do_is_public_updating(LevelRecord.objects.prefetch_related('level').filter(cache_is_public=None).exclude(level__is_public=None))

	do_none_updating(Level.objects.filter( Q(cache_downloads=None) | Q(cache_likes=None) | Q(cache_stars=None) ))

	do_search_cache_updating(Level.objects.filter(is_public=True, hide_from_search=False).exclude(cache_level_name=None).exclude(cache_search_available=True), True)
	do_search_cache_updating(Level.objects.filter( Q(is_public=False) | Q( hide_from_search=True) | Q(cache_level_name=None) ).exclude(cache_search_available=False), False)

def fix_date_estimation():
	to_fix = LevelDateEstimation.objects.filter(cache_online_id=None)
	total = len(to_fix)
	for i,estimation in enumerate(to_fix):
		print(f"fixing {i}/{total}")
		estimation.save()