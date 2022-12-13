from history.models import Level
from history.constants import MiscConstants
import history.utils
import json
import math

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Creates a downloader task with undownloaded levels'

	def handle(self, *args, **options):
		data_path = history.utils.get_data_path()
		levels = Level.objects.exclude(is_deleted=True).filter(cache_stars__gt=0)
		level_count = levels.count()
		levels_to_export = []
		batch_size = 2500
		batch_count = math.ceil(level_count/2500)
		for i in range(0,batch_count):
			levels_to_export = [] 
			levels_small = levels[i*batch_size:(i+1)*batch_size]
			for level in levels_small:
				print(f"{i} / {batch_count} - {level.online_id}")
				levels_to_export.append(str(level.online_id))
			print("Creating JSON")
			task_json = {
				"endpoint": "getGJLevels21",
				"parameters": {
					"type": 10,
					"str": ",".join(levels_to_export)
				}
			}
			print("Saving JSON")
			f = open(f"{data_path}/Exports/RatedRefreshTask_{i}.json", "w")
			json.dump(task_json, f)
			f.close()



		print("Done")