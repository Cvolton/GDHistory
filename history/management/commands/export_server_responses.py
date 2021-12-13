from history.models import ServerResponse
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Deletes all SongRecords'

	def handle(self, *args, **options):
		data_path = history.utils.get_data_path()
		responses = ServerResponse.objects.all()
		for response in responses:
			try:
				f = open(f"{data_path}/ServerResponse/{response.pk}", "r")
				response_json = {
					"created": str(response.created),
					"unprocessed_post_parameters": response.unprocessed_post_parameters,
					"endpoint": response.endpoint,
					"raw_output": f.read()
				}
				f.close()

				f = open(f"{data_path}/Exports/ServerResponse/{response.pk}", "w")
				json.dump(response_json, f)
				f.close()
			except:
				print(f"{response.pk} failed")

		print("Done")