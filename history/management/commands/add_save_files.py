import history.ccUtils
from history.models import SaveFile

import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Adds save files from a pre-defined directory'

	def handle(self, *args, **options):
		directory = '/run/media/cvolton/DATA/testdata/save_import/'
		for filename in os.listdir(directory):
			game_manager_path = f"{directory}/{filename}/CCGameManager.dat"
			if not os.path.exists(game_manager_path):
				print("Save file {game_manager_path} not found")
				continue
			f = open(game_manager_path, "rb")
			parsed_date = datetime.strptime(filename, '%d.%m.%Y')
			print(parsed_date)
			if SaveFile.objects.filter(created=parsed_date).exists():
				print(f"{parsed_date} already exists")
			else:
				history.ccUtils.process_save_file(f, parsed_date)
			f.close()