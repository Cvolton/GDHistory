from history.models import ServerResponse
import history.utils
import history.serverUtils
import json
import os

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Imports server responses from JSON'

	def imports_root(self):
		data_path = history.utils.get_data_path()
		imports_root = f"{data_path}/Imports"
		return imports_root

	def add_arguments(self, parser):
		imports_root = self.imports_root()

		parser.add_argument('directory',  nargs='?', type=str, help='Path to the import files', default=f"{imports_root}/ServerResponse/")

		parser.add_argument(
			'--skip-recalc',
			action='store_true',
			help='Skips the recalculation at the end of the import',
		)

	def handle(self, *args, **options):
		imports_root = self.imports_root()
		directory = options['directory']
		files = os.listdir(directory)
		file_count = len(files)
		for i, filename in enumerate(files):
			export_path = f"{directory}/{filename}"
			if not os.path.exists(export_path):
				print(f"File {export_path} not found")
				continue
			print(f"{i} / {file_count} - Processing {filename}")
			f = open(export_path, "rb")
			if history.serverUtils.import_json(f) is not None:
				os.rename(export_path, f"{imports_root}/ServerResponse-Processed/{filename}")

		if not options['skip_recalc']:
			print("Recalculating")
			history.utils.recalculate_everything()
		print("Done")