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
	form = LevelForm(request.GET or None)

	all_levels = LevelRecord.objects.filter(level__is_public=True)
	#TODO: improve this
	if request.user.is_authenticated and request.user.is_superuser:
		all_levels = LevelRecord.objects.all()

	level_records_unfiltered = all_levels.filter(level__online_id=online_id).prefetch_related('manual_submission').prefetch_related('level').prefetch_related('level_string').prefetch_related('real_user_record__user').annotate(oldest_created=Min('save_file__created'), real_date=Coalesce('oldest_created', 'server_response__created', 'manual_submission__created')).order_by('-real_date')

	if request.method == 'GET' and form.is_valid() and form.cleaned_data['blanks']:
		level_records = level_records_unfiltered
	else:
		level_records = level_records_unfiltered.exclude(level_version=None, game_version=None, level_name=None, downloads=None)

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

		if record.level_string is not None and record.level_string.pk not in level_strings:
			level_string_count += 1
			level_strings[record.level_string.pk] = True
			distinct_records.append(record)

		print(f"{record.pk} {record_id}")
		if str(record.pk) == str(record_id):
			record_belongs = True
			first_record = record

	if len(records) == 0:
		utils.get_level_object(online_id)
		if level_records_unfiltered.count() > 0:
			return render(request, 'error_blanks.html')
		else:
			return render(request, 'error.html', {'error': 'Level not found in our database'})

	if first_record is None:
		first_record = level_records[0]
	
	if record_id is not None and not record_belongs:
		return render(request, 'error.html', {'error': 'Level record does not belong to this level'})

	years = []
	for i in range(min(records), max(records)+1):
		years.append(i)

	if distinct_records:
		years.insert(0, -1)
		records[-1] = distinct_records

	context = {'level_records': records, 'record_id': record_id, 'first_record': first_record, 'online_id': online_id, 'years': years, 'records_count': level_records.count(), 'level_string_count': level_string_count}

	return render(request, 'level.html', context)

@login_required
def upload(request):
	form = UploadFileForm(request.POST or None, request.FILES or None)
	if request.method == 'POST' and form.is_valid():
		ccUtils.upload_save_file(request.FILES['file'], datetime.strptime(form.cleaned_data['time'], '%Y-%m-%d'), request.user)
		return HttpResponse("good")
	else:
		return render(request, 'upload.html')

def search(request):
	form = SearchForm(request.GET or None)

	if request.method == 'GET':
		needs_revalidation = Level.objects.filter(cache_needs_revalidation=True)[:1].count()

		index = meili_utils.get_level_index()

		if not form.is_valid():
			form.cleaned_data = {'p': 1, 'q': ''}

		query = form.cleaned_data['q']
		page = form.cleaned_data['p'] if form.cleaned_data['p'] is not None and form.cleaned_data['p'] > 1 else 1

		del form.cleaned_data['p']

		results_per_page = 20

		start_offset = (page-1)*results_per_page
		end_offset = page*results_per_page

		level_results = index.search(query, {
			'limit': results_per_page,
			'offset': start_offset
			})['hits']
		level_count = 69

		print(level_results)

		#levels = Level.objects.all()
		#levels = Level.objects.filter(hide_from_search=False, is_public=True, cache_blank_name=False)"""

		"""if query != '':
			#query_filter = Q(cache_level_name__icontains=query) | Q(online_id=query) if query.isnumeric() else Q(cache_level_name__icontains=query)
			query_filter = Q(cache_level_name__istartswith=query) | Q(online_id=query) if query.isnumeric() else Q(cache_level_name__istartswith=query)
			levels = levels.filter(query_filter)"""

		#TODO: better implement admin search filters
		"""
		if request.user.is_authenticated and query == 'admin:private' and request.user.is_superuser:
			levels = Level.objects.exclude(is_public=True)

		if request.user.is_authenticated and query == 'admin:hidden' and request.user.is_superuser:
			levels = Level.objects.exclude(cache_search_available=True)

		if 'userID' in form.cleaned_data and form.cleaned_data['userID'] is not None:
			levels = levels.filter(cache_user_id=form.cleaned_data['userID'])
			query += f" (userID {form.cleaned_data['userID']})"

		if 'deleted' in form.cleaned_data and form.cleaned_data['deleted'] is True:
			levels = levels.filter(is_deleted=True)
			query += f" (deleted only)"

		if 'undeleted' in form.cleaned_data and form.cleaned_data['undeleted'] is True:
			levels = levels.exclude(is_deleted=True)
			query += f" (undeleted only)"

		if 'playable' in form.cleaned_data and form.cleaned_data['playable'] is True:
			levels = levels.filter(cache_level_string_available=True)
			query += f" (playable only)"

		if 'unplayable' in form.cleaned_data and form.cleaned_data['unplayable'] is True:
			levels = levels.exclude(cache_level_string_available=True)
			query += f" (unplayable only)"

		if 'rated' in form.cleaned_data and form.cleaned_data['rated'] is True:
			levels = levels.filter(cache_stars__gt=0)
			query += f" (rated only)"

		if 'unrated' in form.cleaned_data and form.cleaned_data['unrated'] is True:
			levels = levels.filter(cache_stars=0)
			query += f" (unrated only)"

		if 'wasrated' in form.cleaned_data and form.cleaned_data['wasrated'] is True:
			levels = levels.filter(cache_max_stars__gt=0)
			query += f" (was rated)"

		if 'wasnotrated' in form.cleaned_data and form.cleaned_data['wasnotrated'] is True:
			levels = levels.filter(cache_max_stars=0)
			query += f" (was not rated)"

		if 'featured' in form.cleaned_data and form.cleaned_data['featured'] is True:
			levels = levels.filter(cache_featured__gt=0)
			query += f" (featured)"

		if 'unfeatured' in form.cleaned_data and form.cleaned_data['unfeatured'] is True:
			levels = levels.exclude(cache_featured__gt=0)
			query += f" (not featured)"

		if 'original' in form.cleaned_data and form.cleaned_data['original'] is not None:
			original_id = form.cleaned_data['original']
			levels = levels.filter( Q(cache_original=original_id) | Q(cache_max_original=original_id) )
			query += f" (original {original_id})"

		if 'difficulty' in form.cleaned_data and form.cleaned_data['difficulty'] is not None:
			if form.cleaned_data['difficulty'] >= 7: #level is demon
				levels = levels.filter(cache_demon=True)
				demon_difficulty = form.cleaned_data['difficulty'] - 7
				if demon_difficulty == 3:
					levels = levels.filter(cache_demon_type__lte=2)
				elif demon_difficulty != 0:
					if demon_difficulty > 3:
						demon_difficulty = demon_difficulty - 1
					demon_difficulty = demon_difficulty + 2
					levels = levels.filter(cache_demon_type=demon_difficulty)
			elif form.cleaned_data['difficulty'] == 1:
				levels = levels.filter(cache_auto=True)
			else:
				main_difficulty = form.cleaned_data['difficulty'] - 1 if form.cleaned_data['difficulty'] > 0 else 0
				levels = levels.filter(cache_main_difficulty=main_difficulty, cache_demon=False, cache_auto=False)

			query += f" (difficulty filter)"
		"""

		"""levels = levels.filter(cache_search_available=True)

		level_count = levels[:end_offset+41].count()
		levels = levels.order_by('-cache_downloads')
		if 's' in form.cleaned_data:
			reverse_sort = False
			order = form.cleaned_data['s']
			if order[:1] == '-':
				reverse_sort = True
				order = order[1:]

			allowed_sorts = {
				'id': 'online_id',
				'name': 'cache_level_name',
				'last_seen': 'cache_submitted',
				'downloads': 'cache_downloads',
				'likes': 'cache_likes',
				'difficulty': 'cache_stars', #TODO: sort demons
				'username': 'cache_username',
				'user_id': 'cache_user_id',
				'versions': 'cache_available_versions',
			}

			unique_sorts = ['id', 'likes']

			if order in allowed_sorts:
				primary_parameter = f"{'-' if reverse_sort else ''}{allowed_sorts[order]}"
				if order not in unique_sorts and reverse_sort:
					levels = levels.order_by(primary_parameter, "-cache_downloads")
				else: 
					levels = levels.order_by(primary_parameter)

		level_results = levels[start_offset:end_offset]


		if len(level_results) < 1:
			return render(request, 'error.html', {'error': 'No results found'})
		"""
		minimum_page_button = page-3
		if minimum_page_button < 1:
			minimum_page_button = 1

		maximum_page_button = minimum_page_button+6
		if maximum_page_button*results_per_page > level_count:
			maximum_page_button = math.ceil(level_count/results_per_page)

		page_buttons = range(minimum_page_button, maximum_page_button+1)

		context = {
			'query': query,
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
	levels = Level.objects.filter(cache_search_available=True, cache_daily_id__gt=0).order_by('cache_daily_id')

	if len(levels) < 1:
		return render(request, 'error.html', {'error': 'No results found'})

	records = {}

	records["Weekly"] = []
	#TODO: do not hardcode years
	for i in range(2016, 2023):
		records[i] = []
		#records[f"Weekly {i}"] = []

	#TODO: read year from level if possible
	for record in levels:
		if record.cache_daily_id is None: continue
		if record.cache_daily_id < 100000:
			if record.cache_daily_id < 12: records[2016].append(record)
			elif record.cache_daily_id < 385: records[2017].append(record)
			elif record.cache_daily_id < 752: records[2018].append(record) #estimated - 2019 start: Code by Anubis + 5
			elif record.cache_daily_id < 1124: records[2019].append(record) #estimated - Both Suiteki and True Damage are off by 18 on this list: https://geometry-dash.fandom.com/es/wiki/Daily_Level/Niveles_1101_-_1200, therefore Overdoze's ID should be 1106+1
			elif record.cache_daily_id < 1493: records[2020].append(record) #estimated - unable to determine if off by 20 or 21 from said list, assuming 20; this was wrong, it's 21
			elif record.cache_daily_id < 1858: records[2021].append(record)
			else: records[2022].append(record)
		else: records["Weekly"].append(record)	

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
	data = ccUtils.create_data_from_level_record(record, True) #gdshare b64s the b64d desc already, so this is required
	if 'k4' not in data:
		return render(request, 'error.html', {'error': 'This record does not contain any level data. If you have reached this page using a link claiming that the data is available, please report this bug immediately.'})

	data = plistlib.dumps(data)
	data = ccUtils.consolidate_plist(data)
	data = ccUtils.plist_to_robtop_plist(data)
	response = HttpResponse(data)
	response['Content-Disposition'] = f'attachment; filename={online_id}.gmd'
	return response

@login_required
def my_submissions(request, show_all=None):
	#TODO: optimize this
	submissions = SaveFile.objects.annotate(num_levels=Count('levelrecord')).order_by('created').prefetch_related("author")
	if not (show_all and request.user.is_superuser):
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