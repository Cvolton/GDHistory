from celery import shared_task

from .serverUtils import download_level


@shared_task
def download_level_task(online_id):
	download_level(online_id)