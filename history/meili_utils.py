import meilisearch
import math

client = meilisearch.Client('http://127.0.0.1:7700', 'testkey') #TODO: move key to env variable

def index_levels():
	from .models import Level

	index = client.index('levels')

	searchable_levels = Level.objects.filter(cache_search_available=True)

	batch_size = 2500

	level_count = searchable_levels.count()
	for i in range(0,math.ceil(level_count / batch_size)):
		level_list = searchable_levels[i*batch_size:(i+1)*batch_size]
		levels_to_update = []
		for j,level in enumerate(level_list):
			print(f"{j+(i*batch_size)} / {level_count} - Updating {level.online_id}")
			level_dict = level.get_serialized_base()
			level_dict['cache_submitted'] = str(level_dict['cache_submitted'])
			levels_to_update.append(level_dict)
		index.add_documents(levels_to_update)

