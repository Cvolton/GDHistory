import os
import html
from w3lib.html import replace_entities

def assign_key(data, key):
	if key not in data:
		return None
	value = assign_key_no_pop(data, key)
	data.pop(key)
	return value

def assign_key_no_pop(data, key):
	if key not in data:
		return None
	value = data[key]
	if isinstance(value, str):
		value = value.replace('@@amp@@','&')
		value = value.replace('@@hash@@','#')
		value = replace_entities(value)
	return value

def get_data_path():
	return os.getenv('DATA_PATH', 'data')