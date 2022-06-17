from history.models import LevelRecord
import history.utils
import json
import math

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Min
from django.db.models.functions import Coalesce


class Command(BaseCommand):
	help = 'Creates user objects for levels'

	def handle(self, *args, **options):

		records = LevelRecord.objects.exclude(user_id=None).filter(real_user_record=None).annotate(oldest_created=Min('save_file__created'), real_date=Coalesce('oldest_created', 'server_response__created')).order_by('-real_date')
		records_count = records.count()
		batch_size = 2500
		batch_count = math.ceil(records_count/2500)
		for i in range(0,batch_count):
			records_small = records[0:batch_size]
			for record in records_small:
				print(f"{i} / {batch_count} - {record.pk}")
				record.create_user()
				user_object.revalidate_cache()
				


		print("Done")