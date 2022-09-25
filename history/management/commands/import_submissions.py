from history.models import HistoryUser
import history.utils
import history.jsonUtils
import json
import os

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Imports server responses from JSON'

	def handle(self, *args, **options):
		data_path = history.utils.get_data_path()
		imports_root = f"{data_path}/Imports"
		directory = f"{imports_root}/ManualSubmission/"
		files = os.listdir(directory)
		file_count = len(files)
		for i, filename in enumerate(files):
			export_path = f"{directory}/{filename}"
			if not os.path.exists(export_path):
				print("Submission {export_path} not found")
				continue
			print(f"{i} / {file_count} - Processing {filename}")
			f = open(export_path, "rb")
			if history.jsonUtils.upload_submission(f, HistoryUser.objects.get(user__username="Cvolton")) is not None:
				os.rename(export_path, f"{imports_root}/ManualSubmission-Processed/{filename}")

		history.utils.recalculate_counts()
		print("Done")