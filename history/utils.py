import os
import html
import hashlib
import urllib
import base64
from w3lib.html import replace_entities

from django.utils import timezone
from django.utils.timezone import make_aware, is_naive
from django.core.cache import cache
from django.db.models import Max

from .constants import MiscConstants

class DecodeResult:
	def __init__(self, encoded, text):
		self.encoded = encoded
		self.text = text

def encode_base64_text(content):
	if content is None: return None
	return base64.b64encode(content.encode('windows-1252'), altchars=b'-_').decode('windows-1252')

def decode_base64_text(content):
	try:
		content = base64.b64decode(content, altchars='-_').decode('windows-1252')
		encoded = False
	except:
		encoded = True
	return DecodeResult(encoded, content)

def assign_key(data, key):
	if key not in data and str(key) not in data:
		return None
	value = assign_key_no_pop(data, key)
	if key in data:
		data.pop(key)
	if str(key) in data:
		data.pop(str(key))
	return value

def assign_key_no_pop(data, key):
	if key not in data or data[key] == '':
		if not isinstance(key, str):
			return assign_key_no_pop(data, str(key))
		return None
	value = data[key]
	if isinstance(value, str): #TODO: proper escaping
		value = value.replace('@@amp@@','&')
		value = value.replace('@@hash@@','#')
		"""value = value.replace('@@inverted_question@@','¿')
		value = value.replace('@@inverted_exclamation@@','¡')
		value = value.replace('@@c2@@','Â')
		value = value.replace('@@squared@@','²')
		value = value.replace('@@ce@@','Î')"""
		for i in range(128,256):
			try: #TODO: deal with out of range characters in a sensible manner
				value = value.replace('@@char'+str(i)+'@@', i.to_bytes(1, byteorder='big').decode('windows-1252'))
			except:
				pass
		value = replace_entities(value)
	return value

def get_data_path():
	return os.getenv('DATA_PATH', 'data')

def create_level_string(level_string):
	from .models import LevelString

	level_string = level_string.encode('windows-1252', errors='xmlcharrefreplace')
	sha256 = hashlib.sha256(level_string).hexdigest()
	try:
		level_string_object = LevelString.objects.get(sha256=sha256)
		file_size = level_string_object.get_file_size()
		if file_size is None or file_size == 0:
			record.write_string(level_string)
		return level_string_object
	except Exception as error:
		record = LevelString(sha256=sha256)
		record.write_string(level_string)
		return record

def robtop_unxor(string, key):
	key = str(key)
	string = bytearray(base64.b64decode(string, altchars='-_'))
	for i in range(0, len(string)):
		string[i] ^= ord(key[i%len(key)])
	return string.decode('windows-1252')

def get_song_object(song):
	from .models import Song

	if song == 0 or song is None:
		return None

	try:
		song_object = Song.objects.get(online_id=song)
	except:
		song_object = Song(online_id=song)
		song_object.save()
	return song_object

def create_song_record_from_data(data, song_object, record_type, date, *args, **kwargs):
	from .models import SongRecord

	link = assign_key(data, 10)
	if kwargs.get('decode_link', True) and link is not None:
		link = urllib.parse.unquote(link)

	try:
		record = SongRecord.objects.get(song=song_object,
			song_name = assign_key_no_pop(data, 2),
			artist_id = assign_key_no_pop(data, 3),
			artist_name = assign_key_no_pop(data, 4),
			size = assign_key_no_pop(data, 5),
			youtube_id = assign_key_no_pop(data, 6),
			youtube_channel = assign_key_no_pop(data, 7),
			is_verified = assign_key_no_pop(data, 8),
			link = link,
			record_type = record_type
		)
		real_date = record.get_real_date()
		if real_date is None or date < real_date:
			record.cache_real_date = date
			record.save()
		return record
	except:
		song_name = assign_key(data, 2)
		if song_name is not None and len(song_name) > 255:
			data['song_name_untrimmed'] = song_name
			song_name = song_name[:255]
	
		record = SongRecord(song=song_object,
			song_name = song_name,
			artist_id = assign_key(data, 3),
			artist_name = assign_key(data, 4),
			size = assign_key(data, 5),
			youtube_id = assign_key(data, 6),
			youtube_channel = assign_key(data, 7),
			is_verified = assign_key(data, 8),
			link = link,
			record_type = record_type,
			unprocessed_data = data,
			cache_real_date = date
		)
		record.save()
		return record

def get_user_object(user_id):
	if user_id is None: return None

	from .models import GDUser
	try:
		user_object = GDUser.objects.get(online_id=user_id)
	except:
		user_object = GDUser(online_id=user_id)
		user_object.save()
	return user_object

def create_user_record(user_object, account_id, username, date):
	if user_object is None: return None

	from .models import GDUserRecord

	try:
		record = GDUserRecord.objects.get(user=user_object,
			username = username, 
			account_id = account_id,
		)
	except:
		record = GDUserRecord(user=user_object,
			username = username, 
			account_id = account_id,
		)
		record.save()

	parsed_date = date
	parsed_cache = record.cache_created
	parsed_cache_last_seen = record.cache_last_seen
	if isinstance(date, str): parsed_date = timezone.datetime.fromisoformat(date)
	if isinstance(record.cache_created, str): parsed_cache = timezone.datetime.fromisoformat(record.cache_created)
	if isinstance(record.cache_last_seen, str): parsed_cache_last_seen = timezone.datetime.fromisoformat(record.cache_last_seen)

	if parsed_date is not None and is_naive(parsed_date):
		parsed_date = make_aware(parsed_date)

	if parsed_cache is not None and is_naive(parsed_cache):
		parsed_cache = make_aware(parsed_cache)

	if date is not None and ((record.cache_created is not None and parsed_date < parsed_cache) or record.cache_created is None):
		record.cache_created = parsed_date
		record.save()

	if date is not None and ((record.cache_last_seen is not None and parsed_date > parsed_cache_last_seen) or record.cache_last_seen is None):
		record.cache_last_seen = parsed_date
		record.save()
	
	return record

def get_level_object(level_id, validate_id_range=False):
	try:
		level_id = int(level_id)
	except:
		return None

	from .models import Level
	try:
		level_object = Level.objects.get(online_id=level_id)
	except Level.DoesNotExist:
		if validate_id_range and level_id < MiscConstants.LAST_FULL_SCRAPE_ID: return None

		level_object = Level(online_id=level_id)
		level_object.save()
	except:
		return None
	return level_object

def recalculate_counts():
	from .models import Level, Song, SaveFile, ServerResponse, LevelString, LevelRecord, GDUser

	counts = {
		'level_count': Level.objects.filter(cache_search_available=True).count(),
		'song_count': Song.objects.all().aggregate(max_id=Max('id'))['max_id'],
		'save_count': SaveFile.objects.count(),
		'request_count': ServerResponse.objects.all().aggregate(max_id=Max('id'))['max_id'],
		'level_string_count': LevelString.objects.all().aggregate(max_id=Max('id'))['max_id'],
		'gduser_count': GDUser.objects.all().aggregate(max_id=Max('id'))['max_id'],
	}
	cache.set('counts', counts, None)
	return counts

def recalculate_daily_records():
	from .models import Level
	levels = Level.objects.filter(cache_search_available=True, cache_daily_id__gt=0).order_by('cache_daily_id')

	if len(levels) < 1:
		return {}

	records = {}

	records["Weekly"] = []
	records["Event"] = []
	#TODO: do not hardcode years
	for i in range(2016, 2026):
		records[i] = []
		#records[f"Weekly {i}"] = []

	#TODO: read year from level if possible
	for record in levels:
		if record.cache_daily_id is None: continue
		if record.cache_daily_id < 100000:
			if record.cache_daily_id < 12: records[2016].append(record.get_serialized_base())
			elif record.cache_daily_id < 385: records[2017].append(record.get_serialized_base())
			elif record.cache_daily_id < 752: records[2018].append(record.get_serialized_base()) #estimated - 2019 start: Code by Anubis + 5
			elif record.cache_daily_id < 1124: records[2019].append(record.get_serialized_base()) #estimated - Both Suiteki and True Damage are off by 18 on this list: https://geometry-dash.fandom.com/es/wiki/Daily_Level/Niveles_1101_-_1200, therefore Overdoze's ID should be 1106+1
			elif record.cache_daily_id < 1493: records[2020].append(record.get_serialized_base()) #estimated - unable to determine if off by 20 or 21 from said list, assuming 20; this was wrong, it's 21
			elif record.cache_daily_id < 1858: records[2021].append(record.get_serialized_base())
			elif record.cache_daily_id < 2223: records[2022].append(record.get_serialized_base())
			elif record.cache_daily_id < 2590: records[2023].append(record.get_serialized_base())
			elif record.cache_daily_id < 2958: records[2024].append(record.get_serialized_base())
			else: records[2025].append(record.get_serialized_base())
		else:
			if record.cache_daily_id < 200000: records["Weekly"].append(record.get_serialized_base())
			else: records["Event"].append(record.get_serialized_base())

	cache.set('daily', records, None)
	recalculate_daily_records_current_year()
	return records

def recalculate_daily_records_current_year():
	records = get_daily_records()
	for record in records:
		if record == 2025: continue
		records[record] = []
	cache.set('daily_current_year', records, None)

def get_daily_records():
	records = cache.get('daily')
	if records is None:
		return recalculate_daily_records()
	return records

def get_daily_records_current_year():
	records = cache.get('daily_current_year')
	if records is None:
		return recalculate_daily_records_current_year()
	return records

def recalculate_everything():
	recalculate_counts()
	recalculate_daily_records()

def get_level_id_within_window():
	two_years_ago = timezone.now() - timezone.timedelta(days=365*2)
	print(two_years_ago)
	return get_level_id_before(two_years_ago)

def get_level_id_before(last_date):
	from history.models import LevelDateEstimation
	time_estimation = LevelDateEstimation.objects.filter(estimation__lt=last_date).order_by('-estimation')[:1]
	if len(time_estimation) < 1:
		return 0
	time_estimation = time_estimation[0]
	estimated_id = time_estimation.cache_online_id
	print(estimated_id)
	return estimated_id

def annotate_record_set_with_date(record_set):
	from django.db.models import Min
	from django.db.models.functions import Coalesce
	return record_set.annotate(oldest_created=Min('save_file__created'), real_date=Coalesce('oldest_created', 'server_response__created', 'manual_submission__created'))

def get_blacklisted_userids(force_reload = False):
	values = cache.get('blacklisted_userids')
	if values is None or force_reload:
		data_path = get_data_path()
		if not os.path.exists(f"{data_path}/blacklisted_userids.txt"):
			values = []
		else:
			with open(f"{data_path}/blacklisted_userids.txt", "r") as f:
				values = f.read().splitlines()
			values = [int(value.strip()) for value in values if value.isdigit]
		cache.set('blacklisted_userids', values, None)
	return values
