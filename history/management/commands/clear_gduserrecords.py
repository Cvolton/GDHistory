from history.models import GDUserRecord

from django.core.management.base import BaseCommand

class Command(BaseCommand):
	help = 'Deletes all GDUserRecords'

	def add_arguments(self, parser):
		parser.add_argument('levels', type=int)

	def handle(self, *args, **options):
		record_count = options['levels']
		i = 0
		while GDUserRecord.objects.all()[:1].count() > 0:
			print(f"Deleting {record_count} records, iteration {i}")
			level_records = GDUserRecord.objects.filter(pk__lt=GDUserRecord.objects.first().pk + record_count).delete()
			i += 1