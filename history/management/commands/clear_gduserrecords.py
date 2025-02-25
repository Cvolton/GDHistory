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
			wip_pk = GDUserRecord.objects.first().pk
			print(f"Deleting {record_count} records, iteration {i}, id {wip_pk}")
			level_records = GDUserRecord.objects.filter(pk__lt=wip_pk + record_count).delete()
			i += 1