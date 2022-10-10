import meilisearch
import math
import os
import time

client = meilisearch.Client('http://127.0.0.1:7700', os.getenv('MEILI_KEY','ABCabc123'))

def get_level_index():
	index = client.index('levels')
	return index

def index_levels():
	from .models import Level

	index = get_level_index()

	index.update_settings({'distinctAttribute': 'online_id'})

	attribute_list = [
		'online_id',
		'comment',
		'is_deleted',
		'cache_level_name',
		'cache_submitted',
		'cache_submitted_timestamp',
		'cache_downloads',
		'cache_likes',
		'cache_rating_sum',
		'cache_rating',
		'cache_demon',
		'cache_auto',
		'cache_demon_type',
		'cache_stars',
		'cache_username',
		'cache_level_string_available',
		'cache_user_id',
		'cache_daily_id',
		'cache_needs_updating',
		'cache_available_versions',
		'cache_search_available',
		'cache_main_difficulty',
		'cache_max_stars',
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
		'cache_needs_revalidation',
	]

	index.update_filterable_attributes(attribute_list)
	index.update_sortable_attributes(attribute_list)
	index.update_pagination_settings({'maxTotalHits': 2147483647})

	searchable_levels = Level.objects.filter(cache_search_available=True)

	batch_size = 250000

	level_count = searchable_levels.count()
	for i in range(0,math.ceil(level_count / batch_size)):
		level_list = searchable_levels[i*batch_size:(i+1)*batch_size]
		levels_to_update = []
		lists_to_send = []
		for j,level in enumerate(level_list):
			print(f"{j+(i*batch_size)} / {level_count} - Updating {level.online_id}")
			level_dict = level.get_serialized_base_json()
			levels_to_update.append(level_dict)
			if len(levels_to_update) > 10000:
				lists_to_send.append(levels_to_update)
				levels_to_update = []
		index.add_documents(levels_to_update)
		for levels_to_update in lists_to_send:
			index.add_documents(levels_to_update)
