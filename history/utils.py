import os
import html
import hashlib
import urllib
import base64
from w3lib.html import replace_entities

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
	if isinstance(value, str):
		value = value.replace('@@amp@@','&')
		value = value.replace('@@hash@@','#')
		value = replace_entities(value)
	return value

def get_data_path():
	return os.getenv('DATA_PATH', 'data')

def create_level_string(level_string):
	from .models import LevelString

	level_string = level_string.encode('windows-1252')
	sha256 = hashlib.sha256(level_string).hexdigest()
	try:
		return LevelString.objects.get(sha256=sha256)
	except:
		requires_base64 = False
		if level_string[:2] == b'eJ' or level_string[:2] == b'H4':
			level_string = base64.b64decode(level_string, altchars='-_')
			requires_base64 = True

		record = LevelString(sha256=sha256, requires_base64=requires_base64)
		record.save()
		f = open(record.get_file_path(), "wb")
		f.write(level_string)
		f.close()
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

def create_song_record_from_data(data, song_object, record_type, *args, **kwargs):
	from .models import SongRecord

	link = assign_key(data, 10)
	if kwargs.get('decode_link', True) and link is not None:
		link = urllib.parse.unquote(link)

	try:
		return SongRecord.objects.get(song=song_object,
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
	except:
		record = SongRecord(song=song_object,
			song_name = assign_key(data, 2),
			artist_id = assign_key(data, 3),
			artist_name = assign_key(data, 4),
			size = assign_key(data, 5),
			youtube_id = assign_key(data, 6),
			youtube_channel = assign_key(data, 7),
			is_verified = assign_key(data, 8),
			link = link,
			record_type = record_type,
			unprocessed_data = data
		)
		record.save()
		return record

def get_user_object(user_id):
	from .models import GDUser
	try:
		user_object = GDUser.objects.get(online_id=user_id)
	except:
		user_object = GDUser(online_id=user_id)
		user_object.save()
	return user_object

def create_user_record(user_object, account_id, username, date, server_response, save_file, record_type):
	if username == "": return
	from .models import GDUserRecord, ServerResponse, SaveFile, LevelRecord

	try:
		record = GDUserRecord.objects.get(user=user_object,
			username = username, 
			account_id = account_id,
			server_response = server_response,
			record_type = record_type
		)
	except:
		record = GDUserRecord(user=user_object,
			username = username, 
			account_id = account_id,
			server_response = server_response,
			record_type = record_type
		)
		record.save()
	if date is not None and ((record.cache_created is not None and date < record.cache_created) or record.cache_created):
		record.cache_created = date
		record.save()
	record.save_file.add(*(save_file.all()))
	return record