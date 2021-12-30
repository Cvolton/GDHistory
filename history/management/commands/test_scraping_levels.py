import history.serverUtils
from history.constants import GetLevelTypes

import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Test command'

	def handle(self, *args, **options):
		history.serverUtils.get_first_level_pages(GetLevelTypes.LIKED, 10)
		history.serverUtils.get_first_level_pages(GetLevelTypes.DOWNLOADED, 10)
		history.serverUtils.get_first_level_pages(GetLevelTypes.TRENDING, 10)
		history.serverUtils.get_first_level_pages(GetLevelTypes.MAGIC, 10)
		history.serverUtils.get_first_level_pages(GetLevelTypes.RECENT, 10)
		history.serverUtils.get_first_level_pages(GetLevelTypes.AWARDED, 10)

		#history.serverUtils.get_level_pages_from(GetLevelTypes.AWARDED, 1043)