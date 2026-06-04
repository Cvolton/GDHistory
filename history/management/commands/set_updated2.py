from history.models import Level
import history.utils
import json
import math

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Min
from django.db.models.functions import Coalesce


class Command(BaseCommand):
	help = 'set updated2'

	def handle(self, *args, **options):

		last_id = 0

		while True:
			print('getting levels')
			objects = Level.objects.filter(is_deleted=True, cache_needs_updating=True)

			if last_id > 0:
				objects = objects.filter(id__gt=last_id)

			objects = objects[:10000]

			for object in objects:
				object.cache_needs_updating = False
				object.cache_needs_updating2 = True

			print('updating levels')
			Level.objects.bulk_update(objects, ['cache_needs_updating', 'cache_needs_updating2'], batch_size=1000)

			if len(objects) > 0:
				last_id = objects[len(objects) - 1].id

			if len(objects) < 10000:
				print('done')
				break
		
