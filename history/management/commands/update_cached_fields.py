import history.maintenance_utils

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def handle(self, *args, **options):

		history.maintenance_utils.update_cached_fields()

		print("Done")