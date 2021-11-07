from .utils import assign_key, get_data_path

import requests

def send_request(endpoint, data):

	mandatory_data = {
		"gameVersion": "21",
		"binaryVersion": "35",
		"gdw": "0",
		"secret": "Wmfd2893gb7"
	}

	data |= mandatory_data 

	headers = {'User-Agent': ''}

	response = requests.post("http://www.boomlings.com/database/downloadGJLevel22.php", data=data, headers=headers)
	return response.text

def response_to_dict(response):
	result = {}
	i = 0
	last_key = 0
	for item in response.split(':'):
		if i % 2 == 0:
			last_key = int(item)
		else:
			result[last_key] = item
		i += 1
	return result

def download_level(online_id):
	response = send_request('downloadGJLevel22', {'levelID': '8887031'})
	data_path = get_data_path()

	level_info = response_to_dict(response.split('#')[0])

	f = open(f"{data_path}/LevelRecord-DownloadResponse/0", "w")
	f.write(response)
	f.close()