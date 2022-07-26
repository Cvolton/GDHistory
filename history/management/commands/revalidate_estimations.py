from history.models import LevelDateEstimation

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

import math

class Command(BaseCommand):
	help = 'Revalidates level cache'

	def handle(self, *args, **options):
		estimations = LevelDateEstimation.objects.all()
		estimations_count = estimations.count()
		batch_size = 2500
		batch_count = math.ceil(estimations_count/batch_size)
		for i in range(0,batch_count):
			estimations_small = estimations[i*batch_size:(i+1)*batch_size]
			for estimation in estimations_small:
				print(f"{i} / {batch_count} - {estimation.pk}")
				estimation.calculate()

		print("Done")