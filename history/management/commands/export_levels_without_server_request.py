from history.models import Level, LevelRecord, LevelRecordType
from history.constants import MiscConstants
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Creates a downloader task with undownloaded levels'

	def handle(self, *args, **options):
		data_path = history.utils.get_data_path()
		levels = Level.objects.exclude(is_deleted=True).prefetch_related('levelrecord_set')
		level_count = levels.count()
		levels_to_export = []
		for i in range(0,level_count):
			level = levels[i:i+1]
			level = level[0]
			string_count = level.levelrecord_set.filter( Q(record_type=LevelRecordType.DOWNLOAD) | Q(record_type=LevelRecordType.GET) ).count()
			if string_count > 0:
				continue
			print(f"{i} / {level_count} - {level.online_id} {string_count}")
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