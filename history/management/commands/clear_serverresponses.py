from history.models import ServerResponse

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Deletes all ServerResponses'

	def handle(self, *args, **options):
		print("Deleting")
		level_records = ServerResponse.objects.all().delete()
		print("Done")