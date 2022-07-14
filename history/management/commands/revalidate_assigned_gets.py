from history.models import ServerResponse

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

import math

class Command(BaseCommand):
	help = 'Revalidates level cache'

	def handle(self, *args, **options):
		responses = ServerResponse.objects.filter(endpoint__startswith='getGJLevel')
		responses_count = responses.count()
		batch_size = 2500
		batch_count = math.ceil(responses_count/batch_size)
		for i in range(0,batch_count):
			responses_small = responses[i*batch_size:(i+1)*batch_size]
			for response in responses_small:
				print(f"{i} / {batch_count} - {response.pk}")
				response.assign_get()

		print("Done")