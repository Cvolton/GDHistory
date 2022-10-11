import history.meili_utils

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'updates meilisearch stuff'

	def handle(self, *args, **options):
		history.meili_utils.index_queue()

		print("Done")