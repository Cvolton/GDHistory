import os
import html

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
		value = html.unescape(value)
	return value

def get_data_path():
	return os.getenv('DATA_PATH', 'data')