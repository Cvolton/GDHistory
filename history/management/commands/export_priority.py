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
		levels = Level.objects.filter(needs_priority_download=True)
		levels_small = levels[0:20]
		levels_to_export = []
		for i,level in enumerate(levels_small):
			print(f"{i} / 20 - {level.online_id}")
			levels_to_export.append(level.online_id)
			level.needs_priority_download = False
			level.save()

		print("Creating JSON")
		task_json = {
			"endpoint": "downloadGJLevel22",
			"parameters": {
				"inc": 0,
				"extras": 1
			},
			"levelList": levels_to_export
		}

		print("Saving JSON")
		f = open(f"{data_path}/Exports/LevelTaskPriority.json", "w")
		json.dump(task_json, f)
		f.close()

		print("Done")