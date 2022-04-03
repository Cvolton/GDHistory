from history.models import Level, LevelRecord, LevelRecordType
from history.constants import MiscConstants
import history.utils
import json
import math

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Creates a downloader task with undownloaded levels'

	def handle(self, *args, **options):
		print("starting")
		data_path = history.utils.get_data_path()
		levels = Level.objects.exclude(is_deleted=True)
		level_count = levels.count()
		levels_to_export = []
		batch_size = 2500
		batch_count = math.ceil(level_count/2500)
		for i in range(0,batch_count):
			print(f"fetching batch {i} / {batch_count}")
			levels_small = levels[i*batch_size:(i+1)*batch_size]
			for j,level in enumerate(levels_small):
				string_count = level.levelrecord_set.filter( Q(record_type=LevelRecordType.DOWNLOAD) | Q(record_type=LevelRecordType.GET) ).count()
				if string_count > 0:
					continue
				print(f"{(i*2500)+j} / {level_count} - {level.online_id} {string_count}")
				levels_to_export.append(level.online_id)

		task_json = {
			"endpoint": "downloadGJLevel22",
			"parameters": {
				"inc": 0,
				"extras": 1
			},
			"levelList": levels_to_export
		}

		f = open(f"{data_path}/Exports/LevelTask.json", "w")
		json.dump(task_json, f)
		f.close()

		print("Done")