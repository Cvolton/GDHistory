from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Count, Min, Max, Q
from django.db.models.functions import Coalesce

from datetime import datetime

from .models import Level, LevelRecord, Song, SaveFile, ServerResponse, LevelString, HistoryUser
from .forms import UploadFileForm, SearchForm
from . import ccUtils, serverUtils, tasks

import math
import plistlib

def index(request):
	all_levels = LevelRecord.objects.prefetch_related('level').exclude(level_name=None)
	recently_added = all_levels.order_by('-level__pk').filter(level__is_public=True)[:5]
	recently_updated = all_levels.order_by('-pk').filter(cache_is_public=True)[:5]

	context = {
		'recently_added': recently_added,
		'recently_updated': recently_updated,
		'level_count': Level.objects.count(),
		'song_count': Song.objects.count(),
		'save_count': SaveFile.objects.count(),
		'request_count': ServerResponse.objects.count(),
		'level_string_count': LevelString.objects.count(),
	}

	return render(request, 'index.html', context)

def view_level(request, online_id=None):
	all_levels = LevelRecord.objects.filter(level__is_public=True)
	#TODO: improve this
	if request.user.is_authenticated and request.user.is_superuser:
		all_levels = LevelRecord.objects.all()

	level_records = all_levels.filter(level__online_id=online_id).exclude(level_version=None).prefetch_related('level').prefetch_related('level_string').annotate(oldest_created=Min('save_file__created'), real_date=Coalesce('oldest_created', 'server_response__created')).order_by('-real_date')

	#tasks.download_level_task.delay(online_id)

	records = {}
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

	if len(records) == 0:
		return render(request, 'error.html', {'error': 'Level not found in our database'})

	years = []
	for i in range(min(records), max(records)+1):
		years.append(i)

	context = {'level_records': records, 'first_record': level_records[0], 'online_id': online_id, 'years': years, 'records_count': level_records.count(), 'level_string_count': level_string_count}

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
		if not form.is_valid():
			form.cleaned_data = {'p': 1, 'q': ''}

		query = form.cleaned_data['q']
		page = form.cleaned_data['p'] if form.cleaned_data['p'] is not None and form.cleaned_data['p'] > 1 else 1

		del form.cleaned_data['p']

		results_per_page = 20

		start_offset = (page-1)*results_per_page
		end_offset = page*results_per_page

		query_filter = Q(cache_level_name__icontains=query) | Q(online_id=query) if query.isnumeric() else Q(cache_level_name__icontains=query)

		levels = Level.objects.filter(query_filter).filter(is_public=True)

		#TODO: better implement admin search filters
		if request.user.is_authenticated and query == 'admin:private' and request.user.is_superuser:
			levels = Level.objects.exclude(is_public=True)

		if 'userID' in form.cleaned_data and form.cleaned_data['userID'] is not None:
			levels = levels.filter(cache_user_id=form.cleaned_data['userID'])
			query += f" (userID {form.cleaned_data['userID']})"

		if 'deleted' in form.cleaned_data and form.cleaned_data['deleted'] is True:
			levels = levels.filter(is_deleted=True)
			query += f" (deleted only)"

		if 'playable' in form.cleaned_data and form.cleaned_data['playable'] is True:
			levels = levels.filter(cache_level_string_available=True)
			query += f" (playable only)"

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
			}

			if order in allowed_sorts:
				levels = levels.order_by(f"{'-' if reverse_sort else ''}{allowed_sorts[order]}","-cache_downloads")

		level_results = levels[start_offset:end_offset]

		level_count = levels.count()

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
		}
		return render(request, 'search.html', context)
	else:
		return render(request, 'error.html', {'error': 'Invalid search query'})

def login_page_placeholder(request):
		return render(request, 'error.html', {'error': 'This feature is not available yet.'})

def download_record(request, record_id=None, online_id=None):
	if record_id == None:
		return render(request, 'error.html', {'error': 'Invalid record ID'})
	try: record = LevelRecord.objects.get(pk=record_id)
	except: return render(request, 'error.html', {'error': 'Record not found in our database'})
	if record.level.is_public is not True:
		return render(request, 'error.html', {'error': 'You do not have the rights to download this record'})
	data = ccUtils.create_data_from_level_record(record)
	if 'k4' not in data:
		return render(request, 'error.html', {'error': 'This record does not contain any level data. If you have reached this page using a link claiming that the data is available, please report this bug immediately.'})

	data = plistlib.dumps(data)
	data = ccUtils.consolidate_plist(data)
	data = ccUtils.plist_to_robtop_plist(data)
	response = HttpResponse(data)
	response['Content-Disposition'] = f'attachment; filename={online_id}.gmd'
	return response

@login_required
def my_submissions(request):
	#TODO: optimize this
	user = HistoryUser.objects.get(user=request.user)
	submissions = SaveFile.objects.filter(author=user).annotate(num_levels=Count('levelrecord')).order_by('created')

	context = {
		'submissions': submissions
	}

	return render(request, 'my_submissions.html', context)