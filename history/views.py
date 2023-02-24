from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Count, Min, Max, Q
from django.db.models.functions import Coalesce

from datetime import datetime

from .models import Level, LevelRecord, Song, SaveFile, ServerResponse, LevelString, HistoryUser
from .forms import UploadFileForm, SearchForm, LevelForm
from . import ccUtils, serverUtils, tasks, utils, meili_utils

import math
import plistlib
import meilisearch

def index(request):
	all_levels = LevelRecord.objects.prefetch_related('level').exclude(level_name=None)
	recently_added = Level.objects.order_by('-pk').filter(cache_search_available=True)[:6]
	recently_updated = all_levels.order_by('-pk').filter(cache_is_public=True)[:6]

	context = {
		'recently_added': recently_added,
		'recently_updated': recently_updated
	}

	return render(request, 'index.html', context)

def view_level(request, online_id=None, record_id=None):
	level = utils.get_level_object(online_id)
	if (not (request.user.is_authenticated and request.user.is_superuser) and not (level.is_public or int(online_id) < utils.get_level_id_within_window())) or level.levelrecord_set.count() == 0:
		return render(request, 'error.html', {'error': 'Level not found in our database'})

	form = LevelForm(request.GET or None)

	all_levels = level.levelrecord_set

	level_records_unfiltered = utils.annotate_record_set_with_date(all_levels.filter(level__online_id=online_id).prefetch_related('manual_submission').prefetch_related('server_response').prefetch_related('level').prefetch_related('level_string').prefetch_related('real_user_record__user')).order_by('-real_date')

	if request.method == 'GET' and form.is_valid() and form.cleaned_data['blanks']:
		level_records = level_records_unfiltered
	else:
		level_records = level_records_unfiltered.exclude(level_version=None, game_version=None, level_name=None, downloads=None)

	if request.method == 'GET' and form.is_valid() and form.cleaned_data['dupes']:
		dupes_shown = True
		dupes_present = True
		level_records = level_records
	else:
		dupes_shown = False
		dupes_present = level.levelrecord_set.filter(cache_is_dupe=True)[:1].count()
		level_records = level_records.filter(cache_is_dupe=False)

	#tasks.download_level_task.delay(online_id)

	record_belongs = False
	first_record = None

	records = {}
	distinct_records = []
	level_strings = {}
	level_string_count = 0
	for record in level_records:
		if record.real_date is None:
			continue
		if record.real_date.year not in records:
			records[record.real_date.year] = []
		records[record.real_date.year].append(record)

		if record.level_string is not None and record.level_string.get_decompressed_sha256() not in level_strings:
			level_string_count += 1
			level_strings[record.level_string.get_decompressed_sha256()] = True
			distinct_records.append(record)

		if str(record.pk) == str(record_id):
			record_belongs = True
			first_record = record

	if len(records) == 0 and level_records_unfiltered.count() > 0:
			return render(request, 'error_blanks.html')

	if first_record is None:
		first_record = level_records[0]

	if not first_record.real_user_record:
		first_record.create_user()

	if level.cache_needs_revalidation:
		tasks.revalidate_cache_level.delay(level.online_id)
	
	if record_id is not None and not record_belongs:
		return render(request, 'error.html', {'error': 'Level record does not belong to this level'})

	years = []
	for i in range(min(records), max(records)+1):
		years.append(i)

	if distinct_records:
		years.insert(0, -1)
		records[-1] = distinct_records

	context = {'level_records': records, 'record_id': record_id, 'first_record': first_record, 'online_id': online_id, 'years': years, 'records_count': level_records.count(), 'level_string_count': level_string_count, 'dupes_shown': dupes_shown, 'dupes_present': dupes_present, 'filters': form.cleaned_data if form.is_valid() else []}

	return render(request, 'level.html', context)

@login_required
def upload(request):
	form = UploadFileForm(request.POST or None, request.FILES or None)
	if request.method == 'POST' and form.is_valid():
		ccUtils.upload_save_file(request.FILES['file'], datetime.strptime(form.cleaned_data['time'], '%Y-%m-%d'), request.user)
		return render(request, 'error_success.html', {'error': 'good'})
	else:
		return render(request, 'upload.html')

def debug(request, online_id):
	Level.objects.get(online_id=online_id).revalidate_cache()
	return render(request, 'error.html', {'error': 'good'})

def search(request):
	form = SearchForm(request.GET or None)

	if request.method == 'GET':
		#needs_revalidation = Level.objects.filter(cache_needs_revalidation=True)[:1000].count()
		needs_revalidation = 0

		index = meili_utils.get_level_index()

		if not form.is_valid():
			form.cleaned_data = {'p': 1, 'q': ''}

		query = form.cleaned_data['q']
		page = form.cleaned_data['p'] if form.cleaned_data['p'] is not None and form.cleaned_data['p'] > 1 else 1

		del form.cleaned_data['p']

		results_per_page = 20

		start_offset = (page-1)*results_per_page
		end_offset = page*results_per_page

		visible_query = query

		filters = []


		if 'userID' in form.cleaned_data and form.cleaned_data['userID'] is not None:
			filters.append(f"cache_user_id = {form.cleaned_data['userID']}")
			visible_query += f" (userID {form.cleaned_data['userID']})"

		if 'deleted' in form.cleaned_data and form.cleaned_data['deleted'] is True:
			filters.append("is_deleted = true")
			visible_query += f" (deleted only)"

		if 'undeleted' in form.cleaned_data and form.cleaned_data['undeleted'] is True:
			filters.append("is_deleted != true")
			visible_query += f" (undeleted only)"

		if 'playable' in form.cleaned_data and form.cleaned_data['playable'] is True:
			filters.append("cache_level_string_available = true")
			visible_query += f" (playable only)"

		if 'unplayable' in form.cleaned_data and form.cleaned_data['unplayable'] is True:
			filters.append("cache_level_string_available != true")
			visible_query += f" (unplayable only)"

		if 'rated' in form.cleaned_data and form.cleaned_data['rated'] is True:
			filters.append("cache_stars > 0")
			visible_query += f" (rated only)"

		if 'unrated' in form.cleaned_data and form.cleaned_data['unrated'] is True:
			filters.append("cache_stars = 0")
			visible_query += f" (unrated only)"

		if 'wasrated' in form.cleaned_data and form.cleaned_data['wasrated'] is True:
			filters.append("cache_max_stars > 0")
			visible_query += f" (was rated)"

		if 'wasnotrated' in form.cleaned_data and form.cleaned_data['wasnotrated'] is True:
			filters.append("cache_max_stars = 0")
			visible_query += f" (was not rated)"

		if 'featured' in form.cleaned_data and form.cleaned_data['featured'] is True:
			filters.append("cache_featured > 0")
			visible_query += f" (featured)"

		if 'unfeatured' in form.cleaned_data and form.cleaned_data['unfeatured'] is True:
			filters.append("cache_featured <= 0")
			visible_query += f" (not featured)"

		if 'negativefeatured' in form.cleaned_data and form.cleaned_data['negativefeatured'] is True:
			filters.append("cache_featured < 0")
			visible_query += f" (negative featured)"

		if 'original' in form.cleaned_data and form.cleaned_data['original'] is not None:
			original_id = form.cleaned_data['original']
			filters.append(f"(cache_original = {original_id} OR cache_max_original = {original_id})")
			visible_query += f" (original {original_id})"

		if 'difficulty' in form.cleaned_data and form.cleaned_data['difficulty'] is not None:
			visible_query += f" (difficulty filter)"
			if form.cleaned_data['difficulty'] == 7: #demon filter
				filters.append(f"(cache_filter_difficulty > 7)")
			else: #other filters
				filters.append(f"(cache_filter_difficulty = {form.cleaned_data['difficulty']})")

		sort = ['cache_downloads:desc']
		if 's' in form.cleaned_data:
			reverse_sort = False
			order = form.cleaned_data['s']
			if order[:1] == '-':
				reverse_sort = True
				order = order[1:]

			allowed_sorts = {
				'id': 'online_id',
				'name': 'cache_level_name',
				'last_seen': 'cache_submitted_timestamp',
				'downloads': 'cache_downloads',
				'likes': 'cache_likes',
				'difficulty': 'cache_stars', #TODO: sort demons
				'username': 'cache_username',
				'user_id': 'cache_user_id',
				'versions': 'cache_available_versions',
			}

			unique_sorts = ['id', 'likes']

			order_marker = f"{':desc' if reverse_sort else ':asc'}"

			if order == 'difficulty':
				sort = [f"cache_stars{order_marker}", f"cache_filter_difficulty{order_marker}", "cache_downloads:desc"]
			elif order in allowed_sorts:
				primary_parameter = f"{allowed_sorts[order]}{order_marker}"
				sort = [primary_parameter, "cache_downloads:desc"]

		#level_results = levels[start_offset:end_offset]

		try:
			search_result = index.search(query, {
				'limit': results_per_page,
				'offset': start_offset,
				'sort': sort,
				'filter': " AND ".join(filters)
				})
			level_results = search_result['hits']
			level_count = search_result['estimatedTotalHits']
		except meilisearch.errors.MeiliSearchCommunicationError:
			return render(request, 'error.html', {'error': 'Unable to connect to the search system. Please report this if the issue persists.'})
		except:
			print(sys.exc_info())
			return render(request, 'error.html', {'error': 'An error with the search system has occured. Please report this if the issue persists.'})

		print(level_results)
		if len(level_results) < 1:
			return render(request, 'error.html', {'error': 'No results found'})

		minimum_page_button = page-3
		if minimum_page_button < 1:
			minimum_page_button = 1

		maximum_page_button = minimum_page_button+6
		if maximum_page_button*results_per_page > level_count:
			maximum_page_button = math.ceil(level_count/results_per_page)

		page_buttons = range(minimum_page_button, maximum_page_button+1)

		context = {
			'query': visible_query,
			'level_records': level_results,
			'count': level_count,
			'page': page,
			'filters': form.cleaned_data,
			'start_offset': start_offset,
			'end_offset': end_offset,
			'page_buttons': page_buttons,
			'minimum_page_button': minimum_page_button,
			'maximum_page_button': maximum_page_button,
			'needs_revalidation': needs_revalidation
		}
		return render(request, 'search.html', context)
	else:
		return render(request, 'error.html', {'error': 'Invalid search query'})

def daily(request):
	records = utils.get_daily_records()

	context = {
		'level_records': records,
		'reversed_records': reversed(records)
	}
	return render(request, 'daily.html', context)

def login_page_placeholder(request):
		return render(request, 'error.html', {'error': 'This feature is not available yet.'})

def download_record(request, record_id=None, online_id=None):
	if record_id == None:
		return render(request, 'error.html', {'error': 'Invalid record ID'})
	try: record = LevelRecord.objects.get(pk=record_id)
	except: return render(request, 'error.html', {'error': 'Record not found in our database'})
	if record.level.is_public is not True:
		return render(request, 'error.html', {'error': 'You do not have the rights to download this record'})
	data = ccUtils.create_data_from_level_record(record, True, False) #gdshare b64s the b64d desc already, so this is required
	if 'k4' not in data:
		return render(request, 'error.html', {'error': 'This record does not contain any level data. If you have reached this page using a link claiming that the data is available, please report this bug immediately.'})

	try:
		data = plistlib.dumps(data)
	except ValueError:
		return render(request, 'error.html', {'error': 'This record contains data not supported by the GDHistory .gmd exporter.'})

	data = ccUtils.consolidate_plist(data)
	data = ccUtils.plist_to_robtop_plist(data)
	response = HttpResponse(data)
	response['Content-Disposition'] = f'attachment; filename={online_id}.gmd'
	return response

@login_required
def my_submissions(request, show_all=None):
	#TODO: optimize this
	submissions = SaveFile.objects.order_by('created').prefetch_related("author")
	if not (show_all):# and request.user.is_superuser):
		user = HistoryUser.objects.get(user=request.user)
		submissions = submissions.filter(author=user)

	context = {
		'submissions': submissions,
		'show_all': show_all
	}

	return render(request, 'my_submissions.html', context)

def api_documentation(request):
	return render(request, 'api.html')

def date_estimator(request):
	return render(request, 'date_estimator.html')