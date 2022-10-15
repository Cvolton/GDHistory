import history.maintenance_utils

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def handle(self, *args, **options):

		history.maintenance_utils.update_is_public()

		print("Done")