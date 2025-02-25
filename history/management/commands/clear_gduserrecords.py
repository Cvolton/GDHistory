from history.models import GDUserRecord

from django.core.management.base import BaseCommand

class Command(BaseCommand):
	help = 'Deletes all GDUserRecords'

	def handle(self, *args, **options):
		i = 0
		while GDUserRecord.objects.all()[:1].count() > 0:
			record_count = 100000
			print(f"Deleting {record_count} records, iteration {i}")
			level_records = GDUserRecord.objects.filter(pk__lt=GDUserRecord.objects.first().pk + record_count).delete()