import os

def assign_key(data, key):
	if key not in data:
		return None
	value = data[key]
	data.pop(key)
	return value

def assign_key_no_pop(data, key):
	if key not in data:
		return None
	value = data[key]
	return value

def get_data_path():
	return os.getenv('DATA_PATH', 'data')