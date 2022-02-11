import history.ccUtils
from history.models import SaveFile

import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
	help = 'Adds save files from a pre-defined directory'

	def handle(self, *args, **options):
		data_path = history.utils.get_data_path()
		directory = f"{data_path}/Imports/SaveFile/"
		for filename in os.listdir(directory):
			game_manager_path = f"{directory}/{filename}/CCGameManager.dat"
			if not os.path.exists(game_manager_path):
				print("Save file {game_manager_path} not found")
				continue
			f = open(game_manager_path, "rb")
			parsed_date = datetime.strptime(filename, '%Y-%m-%d')
			print(parsed_date)
			history.ccUtils.upload_save_file(f, parsed_date, settings.AUTH_USER_MODEL.objects.get(username="Cvolton"))
			f.close()
