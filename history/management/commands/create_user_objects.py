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

		records = LevelRecord.objects.exclude(user_id=None).filter(real_user_record=None)[:50000]
		for i in range(0,len(records)):
			record = records[i]
			print(f"{i} / {len(records)} - {record.pk}")
			record.create_user()
				
		print("Done")
