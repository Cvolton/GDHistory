from celery import shared_task

from .serverUtils import download_level
from .ccUtils import process_save_file


@shared_task
def download_level_task(online_id):
	download_level(online_id)