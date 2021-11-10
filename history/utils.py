import os
import html
import hashlib
import base64
from w3lib.html import replace_entities

from .models import LevelString

def assign_key(data, key):
	if key not in data:
		return None
	value = assign_key_no_pop(data, key)
	data.pop(key)
	return value

def assign_key_no_pop(data, key):
	if key not in data or data[key] == '':
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
	sha256 = hashlib.sha256(level_string.encode('utf-8')).hexdigest()
	try:
		return LevelString.objects.get(sha256=sha256)
	except:
		data_path = get_data_path()
		record = LevelString(sha256=sha256)
		record.save()
		f = open(f"{data_path}/LevelString/{record.pk}", "w")
		f.write(level_string)
		f.close()
		return record

def robtop_unxor(string, key):
	key = str(key)
	string = bytearray(base64.b64decode(string, altchars='-_'))
	for i in range(0, len(string)):
		string[i] ^= ord(key[i%len(key)])
	return string.decode('utf-8')