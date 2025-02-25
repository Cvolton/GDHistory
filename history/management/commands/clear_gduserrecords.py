from history.models import GDUserRecord

from django.core.management.base import BaseCommand

class Command(BaseCommand):
	help = 'Deletes all GDUserRecords'

	def handle(self, *args, **options):
		i = 0
		while GDUserRecord.objects.all()[:1].count() > 0:
			print(f"Deleting 100000 records, iteration {i}")
			level_records = GDUserRecord.objects.all()[:100000]
			for record in level_records:
				record.delete()