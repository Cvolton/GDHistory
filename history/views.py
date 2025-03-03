import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse

from datetime import datetime

from history import jsonUtils

from .models import Level, LevelRecord, SaveFile, HistoryUser, ManualSubmission
from .forms import UploadFileForm, SearchForm, UploadSubmissionForm
from . import ccUtils, tasks, utils, meili_utils

import math
import plistlib
import meilisearch
import random
from os import sys


def index(request):
	def main_placeholder():
		placeholders = []
		for i in range(0,5):
			placeholders.append({
				"online_id": "█" * 9,
				"level_name": "█" * random.randint(5, 10)
			})
		return placeholders

	context = {
		'recently_added': main_placeholder(),
		'recently_updated': main_placeholder()
	}

	return render(request, 'index.html', context)

def view_level(request, online_id=None, record_id=None):
	level = utils.get_level_object(online_id, True)
	if level is None or (not (request.user.is_authenticated and request.user.is_superuser) and not (level.is_public or int(online_id) < utils.get_level_id_within_window())):
		return render(request, 'error.html', {'error': 'Level not found in our database'}, status=404)

	if record_id is not None:
		try:
			first_record = LevelRecord.objects.get(pk=record_id)
			if first_record.level != level: raise Exception
		except:
			return render(request, 'error.html', {'error': 'Level record does not belong to this level'}, status=403)
	else:
		first_record = level.get_best_record()
		if not first_record:
			return render(request, 'error.html', {'error': 'Level not found in our database'}, status=404)

	if level.cache_needs_revalidation:
		tasks.revalidate_cache_level.delay(level.online_id)

	context = {'online_id': online_id, 'record_id': record_id, 'first_record': first_record, 'comment': level.comment, 'pk': level.pk, 'records_count': level.levelrecord_set.count(), 'level_string_count': level.cache_available_versions}

	return render(request, 'level.html', context)

@login_required
def upload(request):
	form = UploadFileForm(request.POST or None, request.FILES or None)
	if request.method == 'POST' and form.is_valid():
		ccUtils.upload_save_file(request.FILES['file'], datetime.strptime(form.cleaned_data['time'], '%Y-%m-%d'), request.user)
		return render(request, 'error_success.html', {'error': 'good'})
	else:
		return render(request, 'upload.html')

@login_required
def upload_submission(request):
	form = UploadSubmissionForm(request.POST or None, request.FILES or None)
	if request.method == 'POST' and form.is_valid():
		jsonUtils.upload_submission_delayed(request.FILES['file'], HistoryUser.get_user(request.user))
		return render(request, 'error_success.html', {'error': "good but it'll take a few minutes before it shows up in the list"})
	else:
		return render(request, 'upload_submission.html')

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
			visible_query += f" (deleted)"

		if 'undeleted' in form.cleaned_data and form.cleaned_data['undeleted'] is True:
			filters.append("is_deleted != true")
			visible_query += f" (not deleted)"

		if 'playable' in form.cleaned_data and form.cleaned_data['playable'] is True:
			filters.append("cache_level_string_available = true")
			visible_query += f" (level data available)"

		if 'unplayable' in form.cleaned_data and form.cleaned_data['unplayable'] is True:
			filters.append("cache_level_string_available != true")
			visible_query += f" (level data unavailable)"

		if 'rated' in form.cleaned_data and form.cleaned_data['rated'] is True:
			filters.append("cache_stars > 0")
			visible_query += f" (rated)"

		if 'unrated' in form.cleaned_data and form.cleaned_data['unrated'] is True:
			filters.append("cache_stars = 0")
			visible_query += f" (unrated)"

		if 'wasrated' in form.cleaned_data and form.cleaned_data['wasrated'] is True:
			filters.append("cache_max_stars > 0")
			visible_query += f" (was rated)"

		if 'rerated' in form.cleaned_data and form.cleaned_data['rerated'] is True:
			filters.append("cache_rating_changed = true")
			visible_query += f" (rating changed)"

		if 'wasnotrated' in form.cleaned_data and form.cleaned_data['wasnotrated'] is True:
			filters.append("cache_max_stars = 0")
			visible_query += f" (was never rated)"

		if 'featured' in form.cleaned_data and form.cleaned_data['featured'] is True:
			filters.append("cache_featured > 0")
			visible_query += f" (featured)"

		if 'unfeatured' in form.cleaned_data and form.cleaned_data['unfeatured'] is True:
			filters.append("cache_featured <= 0")
			visible_query += f" (not featured)"

		if 'negativefeatured' in form.cleaned_data and form.cleaned_data['negativefeatured'] is True:
			filters.append("cache_featured < 0")
			visible_query += f" (negative featured)"

		if 'twoPlayer' in form.cleaned_data and form.cleaned_data['twoPlayer'] is True:
			filters.append("cache_two_player = true")
			visible_query += f" (two player)"

		if 'daily' in form.cleaned_data and form.cleaned_data['daily'] is True:
			filters.append("cache_daily_id > 0")
			visible_query += f" (was daily)"

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

		if 'minGameVersion' in form.cleaned_data and form.cleaned_data['minGameVersion'] is not None:
			filters.append(f"cache_min_game_version = {form.cleaned_data['minGameVersion']}")
			visible_query += f" (minGameVersion {form.cleaned_data['minGameVersion']})"

		if 'maxGameVersion' in form.cleaned_data and form.cleaned_data['maxGameVersion'] is not None:
			filters.append(f"cache_max_game_version = {form.cleaned_data['maxGameVersion']}")
			visible_query += f" (maxGameVersion {form.cleaned_data['maxGameVersion']})"

		if 'gameVersion' in form.cleaned_data and form.cleaned_data['gameVersion'] is not None:
			filters.append(f"cache_game_version = {form.cleaned_data['gameVersion']}")
			visible_query += f" (gameVersion {form.cleaned_data['gameVersion']})"

		if 'audioTrack' in form.cleaned_data and form.cleaned_data['audioTrack'] is not None:
			filters.append(f"cache_audiotrack = {form.cleaned_data['audioTrack']}")
			visible_query += f" (audioTrack {form.cleaned_data['audioTrack']})"

		if 'songID' in form.cleaned_data and form.cleaned_data['songID'] is not None:
			filters.append(f"cache_song_id = {form.cleaned_data['songID']}")
			visible_query += f" (songID {form.cleaned_data['songID']})"

		if 'songArtistID' in form.cleaned_data and form.cleaned_data['songArtistID'] is not None:
			filters.append(f"cache_song_artist_id = {form.cleaned_data['songArtistID']}")
			visible_query += f" (songArtistID {form.cleaned_data['songArtistID']})"

		if 'exactName' in form.cleaned_data and form.cleaned_data['exactName'] is not None:
			filters.append(f"cache_level_name = {form.cleaned_data['exactName']}")
			visible_query += f" (exactName {form.cleaned_data['exactName']})"

		if 'length' in form.cleaned_data and form.cleaned_data['length'] is not None:
			visible_query += f" (length filter)"
			length = form.cleaned_data['length']
			if length == -1: length = 0
			if length <= 5:
				filters.append(f"(cache_length = {length})")
			else:
				filters.append(f"(cache_length > 5)")

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
				'difficulty': 'cache_stars',
				'username': 'cache_username',
				'user_id': 'cache_user_id',
				'max_stars': 'cache_max_stars',
				'versions': 'cache_available_versions',
				'min_game_version': 'cache_min_game_version',
				'max_game_version': 'cache_max_game_version',
				'game_version': 'cache_game_version',
				'audiotrack': 'cache_audiotrack',
				'song_id': 'cache_song_id',
				'song_artist_id': 'cache_song_artist_id',
			}

			unique_sorts = ['id', 'likes']

			order_marker = f"{':desc' if reverse_sort else ':asc'}"

			if order == 'difficulty':
				sort = [f"cache_stars{order_marker}", f"cache_filter_difficulty{order_marker}", "cache_downloads:desc"]
			elif order in allowed_sorts:
				primary_parameter = f"{allowed_sorts[order]}{order_marker}"
				sort = [primary_parameter]
				if not primary_parameter.startswith("cache_downloads"):
					sort.append("cache_downloads:desc")

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
		except meilisearch.errors.MeilisearchCommunicationError:
			return render(request, 'error.html', {'error': 'Unable to connect to the search system. Please report this if the issue persists.'}, status=500)
		except:
			print(sys.exc_info())
			return render(request, 'error.html', {'error': 'An error with the search system has occured. Please report this if the issue persists.'}, status=500)

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
	return render(request, 'daily.html')

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
		user = HistoryUser.get_user(request.user)
		submissions = submissions.filter(author=user)

	context = {
		'submissions': submissions,
		'show_all': show_all
	}

	return render(request, 'my_submissions.html', context)

@login_required
def my_manuals(request, show_all=None):
	submissions = ManualSubmission.objects.order_by('created').prefetch_related("author").filter(parent__id=None)
	if not (show_all):# and request.user.is_superuser):
		user = HistoryUser.get_user(request.user)
		submissions = submissions.filter(author=user)

	context = {
		'submissions': submissions,
		'show_all': show_all
	}

	return render(request, 'my_manuals.html', context)

@login_required
def view_manual(request, manual_id=None):
	try:
		manual = ManualSubmission.objects.get(pk=manual_id)
	except:
		return render(request, 'error.html', {'error': 'Submission not found in our database'})

	context = {
		'manual': manual
	}

	return render(request, 'manual_details.html', context)

def view_submission(request, save_id=None, page=1):
	results_per_page = 500

	try:
		page = int(page)
		save_file = SaveFile.objects.get(pk=save_id)
	except:
		return render(request, 'error.html', {'error': 'Submission not found in our database'})
	
	if not save_file.is_browsable and not request.user.is_authenticated:
		return render(request, 'error.html', {'error': 'This submission is not available for public viewing'})

	level_records = save_file.levelrecord_set.prefetch_related('real_user_record').prefetch_related('level').prefetch_related('level_string').order_by('level__online_id')
	level_record_count = level_records.count()
	level_records = level_records[(page-1)*results_per_page:page*results_per_page]

	minimum_page_button = page-3
	if minimum_page_button < 1:
		minimum_page_button = 1

	maximum_page_button = minimum_page_button+6
	if maximum_page_button*results_per_page > level_record_count:
		maximum_page_button = math.ceil(level_record_count/results_per_page)

	page_buttons = range(minimum_page_button, maximum_page_button+1)

	context = {
		'save_file': save_file,
		'level_records': level_records,
		'page': page,
		'minimum_page_button': minimum_page_button,
		'maximum_page_button': maximum_page_button,
		'page_buttons': page_buttons
	}

	return render(request, 'save_details.html', context)

def api_documentation(request):
	return render(request, 'api.html')

def date_estimator(request):
	return render(request, 'date_estimator.html')