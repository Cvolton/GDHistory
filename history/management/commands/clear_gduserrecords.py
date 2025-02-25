from history.models import GDUserRecord

from django.core.management.base import BaseCommand

class Command(BaseCommand):
	help = 'Deletes all GDUserRecords'

	def handle(self, *args, **options):
		while GDUserRecord.objects.all()[:1].count() > 0:
			level_records = GDUserRecord.objects.all()[:100000]
			for record in level_records:
				record.delete()