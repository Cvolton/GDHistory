from history import jsonUtils

from django.core.management.base import BaseCommand

class Command(BaseCommand):
	help = 'Processes delayed manual submissions'

	def handle(self, *args, **options):
		jsonUtils.process_delayed_submissions()
		jsonUtils.delete_queued_submissions()