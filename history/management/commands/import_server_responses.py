from history.models import ServerResponse
import history.utils
import history.serverUtils
from concurrent.futures import ThreadPoolExecutor
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

		def process_file(item):
			i, filename = item
			export_path = f"{directory}/{filename}"
			if not os.path.exists(export_path):
				print(f"File {export_path} not found")
				return
			print(f"{i} / {file_count} - Processing {filename}")
			with open(export_path, "rb") as file_handle:
				if history.serverUtils.import_json(file_handle) is not None:
					os.rename(export_path, f"{imports_root}/ServerResponse-Processed/{filename}")

		#worker_count = (os.cpu_count() or 1) * 2
		worker_count = 50
		with ThreadPoolExecutor(max_workers=worker_count) as executor:
			list(executor.map(process_file, enumerate(files)))

		if not options['skip_recalc']:
			print("Recalculating")
			history.utils.recalculate_everything()
		print("Done")