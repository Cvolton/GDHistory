from celery import shared_task
import meilisearch
import math
import os
import time

from django.core.cache import cache

client = meilisearch.Client('http://127.0.0.1:7700', os.getenv('MEILI_KEY','ABCabc123'))

def get_level_index():
	index = client.index('levels')
	return index

def update_settings(force = False):
	index = get_level_index()

	index.update_settings({'distinctAttribute': 'online_id'})

	attribute_list = [
		'online_id',
		'is_deleted',
		'cache_level_name',
		'cache_submitted',
		'cache_submitted_timestamp',
		'cache_downloads',
		'cache_likes',
		'cache_stars',
		'cache_username',
		'cache_level_string_available',
		'cache_user_id',
		'cache_account_id',
		'cache_daily_id',
		'cache_needs_updating',
		'cache_available_versions',
		'cache_search_available',
		'cache_min_stars',
		'cache_max_stars',
		'cache_rating_changed',
		'cache_filter_difficulty',
		'cache_length',
		'cache_featured',
		'cache_max_featured',
		'cache_epic',
		'cache_max_epic',
		'cache_two_player',
		'cache_max_two_player',
		'cache_original',
		'cache_max_original',
		'cache_min_game_version',
		'cache_max_game_version',
		'cache_game_version',
		'cache_audiotrack',
		'cache_song_id',
		'cache_song_artist_id',
		'cache_needs_revalidation',
		'cache_file_size',
		'cache_decompressed_file_size',
		'cache_object_count',
	]
 
	searchable_attributes = [
		'online_id',
		'cache_level_name',
		'cache_username'
	]

	MAX_TOTAL_HITS = 999999
 
	if force or index.get_settings().get('filterableAttributes') != sorted(attribute_list):
		print("Updating Meili settings")
		index.update_filterable_attributes(attribute_list)
		index.update_sortable_attributes(attribute_list)
		index.update_pagination_settings({'maxTotalHits': MAX_TOTAL_HITS})
	else:
		print("Settings already up to date")
  
	if force or index.get_settings().get('searchableAttributes') != searchable_attributes:
		print("Updating searchable attributes")
		index.update_searchable_attributes(searchable_attributes)

	if force or index.get_settings().get('pagination') != {'maxTotalHits': MAX_TOTAL_HITS}:
		print("Updating pagination settings")
		index.update_pagination_settings({'maxTotalHits': MAX_TOTAL_HITS})

def index_levels():
	from .models import Level

	cache.set('indexing_levels', True, 14400)

	index = get_level_index()
	update_settings()

	#searchable_levels = Level.objects.filter(cache_search_available=True)

	max_id = Level.objects.all().order_by('-id')[:1][0].pk

	batch_size = 50000

	for i in range(0,math.ceil(max_id / batch_size)):
		level_list = Level.objects.filter(pk__gt=i*batch_size, pk__lt=(i+1)*batch_size, cache_search_available=True)
		levels_to_update = []
		lists_to_send = []
		for j,level in enumerate(level_list):
			print(f"{j+(i*batch_size)} / {max_id} - Updating {level.online_id}")
			level_dict = level.get_serialized_base_json()
			levels_to_update.append(level_dict)
			if len(levels_to_update) > 10000:
				lists_to_send.append(levels_to_update)
				levels_to_update = []
		if len(levels_to_update) > 0:
			index.add_documents(levels_to_update, 'online_id')
		for levels_to_update in lists_to_send:
			if len(levels_to_update) > 0: index.add_documents(levels_to_update)

def index_queue_positive():
	from .models import Level
	index = get_level_index()

	while True:
		levels_to_update = Level.objects.filter(cache_needs_search_update=True, cache_search_available=True, cache_needs_revalidation=False)[:10000]
		levels_dict = []
		for level in levels_to_update:
			levels_dict.append(level.get_serialized_base_json())
			level.cache_needs_search_update = False

		if len(levels_dict) == 0:
			print("positive queue empty")
			return

		index.add_documents(levels_dict, 'online_id')

		Level.objects.bulk_update(levels_to_update, ['cache_needs_search_update'], batch_size=1000)
		print("done 1")

		if len(levels_dict) < 10000:
			print("positive queue finished")
			return

def index_queue_negative():
	from .models import Level
	index = get_level_index()
	while True:
		levels_to_delete = []
		levels_to_update = Level.objects.filter(cache_needs_search_update=True, cache_search_available=False)[:50000]
		for level in levels_to_update:
			levels_to_delete.append(level.online_id)
			level.cache_needs_search_update = False

		if len(levels_to_delete) == 0:
			print("negative queue empty")
			return

		index.delete_documents(levels_to_delete)

		Level.objects.bulk_update(levels_to_update, ['cache_needs_search_update'], batch_size=1000)
		print("done 1 negative")

		if len(levels_to_delete) < 50000:
			print("negative queue finished")
			return

def index_queue():
	cache.set('indexing_levels', True, 14400)
	index_queue_positive()
	index_queue_negative()

@shared_task
def try_index_levels():
	if cache.get('indexing_levels'):
		print("Indexing timeout not reached")
		return
	stats = client.get_all_stats()
	if stats['indexes']['levels']['isIndexing']:
		print("Already indexing")
		return
	index_queue()

def admin_stats():
	processing_meili = client.get_tasks({'statuses': 'processing'})
	enqueued_meili = client.get_tasks({'statuses': 'enqueued'})
	return {
		'processing_meili': processing_meili.total,
		'enqueued_meili': enqueued_meili.total,
	}

def level_count_in_index():
	return client.get_all_stats()['indexes']['levels']['numberOfDocuments']