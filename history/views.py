from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Count, Min, Max, Q
from django.db.models.functions import Coalesce

from datetime import datetime

from .models import Level, LevelRecord, Song, SaveFile, ServerResponse, LevelString
from .forms import UploadFileForm, SearchForm
from . import ccUtils, serverUtils, tasks

import math

def index(request):
	all_levels = LevelRecord.objects.prefetch_related('level')
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

	level_records = all_levels.filter(level__online_id=online_id).prefetch_related('level').prefetch_related('level_string').annotate(oldest_created=Min('save_file__created'), real_date=Coalesce('oldest_created', 'server_response__created')).order_by('-real_date')

	#tasks.download_level_task.delay(online_id)

	if len(level_records) == 0:
		return render(request, 'error.html', {'error': 'Level not found in our database'})

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

	if request.method == 'GET' and form.is_valid():
		query = form.cleaned_data['q']
		page = form.cleaned_data['p'] if 'p' in form.cleaned_data and form.cleaned_data['p'] is not None and form.cleaned_data['p'] > 1 else 1

		results_per_page = 20

		start_offset = (page-1)*results_per_page
		end_offset = page*results_per_page

		query_filter = Q(cache_level_name__icontains=query) | Q(online_id=query) if query.isnumeric() else Q(cache_level_name__icontains=query)

		levels = Level.objects.filter(query_filter).filter(is_public=True)

		#TODO: better implement admin search filters
		if request.user.is_authenticated and query == 'admin:private' and request.user.is_superuser:
			levels = Level.objects.exclude(is_public=True)

		level_results = levels.order_by('-cache_downloads')[start_offset:end_offset]

		#TODO: figure out how to sort this without painfully slowing down the entire website
		#level_results = level_results.order_by('-downloads', '-oldest_created')

		level_count = levels.count()
		#level_records = LevelRecord.objects.filter(level__online_id=query).prefetch_related('level').prefetch_related('level_string').annotate(oldest_created=Min('save_file__created')).order_by('-oldest_created')

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