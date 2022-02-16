from history.models import ServerResponse
import history.utils
import history.serverUtils
import json
import os

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def handle(self, *args, **options):
		data_path = history.utils.get_data_path()
		imports_root = f"{data_path}/Imports"
		directory = f"{imports_root}/ServerResponse/"
		files = os.listdir(directory)
		file_count = len(files)
		i = 1
		for filename in files:
			export_path = f"{directory}/{filename}"
			if not os.path.exists(export_path):
				print("Save file {export_path} not found")
				continue
			print(f"{i} / {file_count} - Processing {export_path}")
			f = open(export_path, "rb")
			if history.serverUtils.import_json(f) is not False:
				os.rename(export_path, f"{imports_root}/ServerResponse-Processed/{filename}")
			i += 1

		print("Done")