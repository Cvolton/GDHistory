from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import make_aware
from django.db.models import Min, Max, Q

from datetime import datetime, UTC

from .models import LevelRecord, LevelDateEstimation, GDUserRecord, GDUser, ManualSubmission, Level
from . import utils, constants, meili_utils
from .forms import AdvancedSearchForm, ApiLevelForm

import math
import meilisearch
import sys

@csrf_exempt
def index_counts(request):
	counts = cache.get('counts')
	if counts is None:
		counts = utils.recalculate_counts()

	return JsonResponse(counts)

@csrf_exempt
def index_levels(request):
	all_levels = LevelRecord.objects.prefetch_related('level').exclude(level_name=None)
	recently_added = Level.objects.order_by('-pk').filter(cache_search_available=True)[:6]
	recently_updated = all_levels.order_by('-pk').filter(cache_is_public=True)[:6]

	return JsonResponse({
		'recently_added': [level.get_serialized_base() for level in recently_added],
		'recently_updated': [{'level': level.level.get_serialized_base(), 'record': level.get_serialized_base()} for level in recently_updated]
	})

@csrf_exempt
def save_level(request, online_id=None):
	level = utils.get_level_object(online_id)
	if level.needs_priority_download: return JsonResponse({'success': False, 'fail_reason': constants.SaveFailReasons.ALREADY_QUEUED})

	level.needs_priority_download = True
	level.save()

	return JsonResponse({'success': True})

@csrf_exempt
def level_info(request, online_id=None, view_mode="normal"):
	level = utils.get_level_object(online_id, True)
	if level is None or (not (request.user.is_authenticated and request.user.is_superuser) and not (level.is_public or int(online_id) < utils.get_level_id_within_window())) or level.levelrecord_set.count() == 0 or level.cache_user_id in utils.get_blacklisted_userids():
		return JsonResponse({'success': False}, status=404)

	print(utils.get_blacklisted_userids())

	all_levels = level.levelrecord_set.filter(is_invalid=False)

	response = level.get_serialized_base()

	if view_mode != "brief":
		response['dupes_shown'] = view_mode == "dupes"
		if view_mode == "dupes_only":
			all_levels = all_levels.filter(cache_is_dupe=True)
		elif view_mode != "dupes":
			response['dupes_present'] = all_levels.filter(cache_is_dupe=True)[:1].count() > 0
			all_levels = all_levels.filter(cache_is_dupe=False)

		#level_records = utils.annotate_record_set_with_date(all_levels.prefetch_related('manual_submission').prefetch_related('server_response').prefetch_related('level').prefetch_related('level_string').prefetch_related('real_user_record__user')).order_by('pk')
		level_records = all_levels.prefetch_related('manual_submission').prefetch_related('server_response').prefetch_related('level').prefetch_related('level_string').prefetch_related('real_user_record__user').prefetch_related('song').order_by('pk')
		
		form = ApiLevelForm(request.GET or None)
		if form.is_valid():
			start_from = form.cleaned_data['start_from']
			count = form.cleaned_data['count']
			if start_from is not None:
				level_records = level_records.filter(pk__gt=start_from)
			if count is not None:
				level_records = level_records[:count]

		level_strings = {}
		response['level_string_count'] = 0
		response['records'] = []
		for record in level_records:
			record.upgrade_data()
			response['records'].append(record.get_serialized_full())

			if record.level_string is not None and record.level_string.pk not in level_strings:
				response['level_string_count'] += 1
				level_strings[record.level_string.pk] = True


	return JsonResponse(response)

@csrf_exempt
def level_record(request, online_id=None, record_id=None):
	try:
		level = utils.get_level_object(online_id, True)
		if not level.is_public and not (request.user.is_authenticated and request.user.is_superuser): raise Exception

		record = level.levelrecord_set.get(pk=record_id) if record_id is not None else level.get_best_record()
		if record is None: raise Exception
		return JsonResponse(record.get_serialized_full())
	except:
		return JsonResponse({'success': False}, status=404)

@csrf_exempt
def user_info(request, online_id=None, view_mode="normal"):
	all_users = GDUserRecord.objects.all()

	try:
		online_id = int(online_id.strip())
		if online_id in utils.get_blacklisted_userids():
			raise Exception
		user = GDUser.objects.get(online_id=online_id)
	except:
		return JsonResponse({'success': False}, status=404)

	if view_mode != "brief":
		user_records = all_users.filter(user_id=user.pk).order_by('-cache_created')
		if len(user_records) == 0:
			return JsonResponse({'success': False}, status=404)

	response = user.get_serialized_base()

	user_strings = {}
	if view_mode != "brief":
		response['records'] = []
		for record in user_records:
			response['records'].append(record.get_serialized_full())

	return JsonResponse(response)

@csrf_exempt
def manual_info(request, pk=None):
	manual = ManualSubmission.objects.get(pk=pk)
	try:
		manual = ManualSubmission.objects.get(pk=pk)
	except:
		return JsonResponse({'success': False}, status=404)

	return JsonResponse(manual.get_serialized_base())

@csrf_exempt
def level_date_estimation(request, online_id):
	online_id = int(online_id)

	low = LevelDateEstimation.objects.filter(cache_online_id__lte=online_id).order_by('-cache_online_id')[:1]
	high = LevelDateEstimation.objects.filter(cache_online_id__gte=online_id).order_by('cache_online_id')[:1]

	if low: low = LevelDateEstimation.objects.filter(cache_online_id=low[0].cache_online_id).order_by('estimation')
	if high: high = LevelDateEstimation.objects.filter(cache_online_id=high[0].cache_online_id).order_by('estimation')
	
	approx = None
	if low and high:

		date_difference = high[0].estimation - low[0].estimation
		id_difference = high[0].cache_online_id - low[0].cache_online_id
		requested_id_difference = online_id - low[0].cache_online_id
		percentage = 0 if id_difference == 0 else requested_id_difference / id_difference
		new_date_difference = date_difference * percentage
		approx = {
			"estimation": low[0].estimation + new_date_difference,
			"online_id": online_id
		}

	response = {
		'low': low[0].get_serialized_base() if len(low) > 0 else None,
		'high': high[0].get_serialized_base()  if len(high) > 0 else None,
		'approx': approx
	}
	
	return JsonResponse(response)

@csrf_exempt
def level_date_to_id_estimation(request, online_date):
	online_date = make_aware(datetime.strptime(online_date, '%Y-%m-%d'))

	return time_to_id_estimation(online_date)

@csrf_exempt
def level_timestamp_to_id_estimation(request, online_timestamp):
	online_timestamp = datetime.fromtimestamp(int(online_timestamp), UTC)

	return time_to_id_estimation(online_timestamp)

def time_to_id_estimation(aware_date):
	low = LevelDateEstimation.objects.filter(estimation__lte=aware_date).order_by('-estimation')[:1]
	high = LevelDateEstimation.objects.filter(estimation__gte=aware_date).order_by('estimation')[:1]

	approx = None
	if low and high and low[0].estimation != high[0].estimation:
		date_difference = high[0].estimation - low[0].estimation
		id_difference = high[0].cache_online_id - low[0].cache_online_id
		requested_date_difference = aware_date - low[0].estimation
		percentage = requested_date_difference / date_difference
		new_id_difference = id_difference * percentage
		approx = {
			"estimation": aware_date,
			"online_id": math.floor(low[0].cache_online_id + new_id_difference)
		}

	response = {
		'low': low[0].get_serialized_base() if len(low) > 0 else None,
		'high': high[0].get_serialized_base()  if len(high) > 0 else None,
		'approx': approx
	}
	
	return JsonResponse(response)

@csrf_exempt
def user_to_level_estimation(request, online_id):
	low = GDUser.objects.filter(online_id__lte=online_id).order_by('-online_id')[:1000].values_list('online_id', flat=True)
	high = GDUser.objects.filter(online_id__gte=online_id).order_by('online_id')[:len(low)].values_list('online_id', flat=True)
 
	all_ids = list(low) + list(high)
	min_level_ids = Level.objects.filter(cache_user_id__in=all_ids).values('cache_user_id').annotate(Min('online_id')).values_list('online_id__min', flat=True)
	min_level_ids = sorted(min_level_ids)
	median_level_id = min_level_ids[int(len(min_level_ids) / 2)] if len(min_level_ids) > 0 else None
	return JsonResponse({
		'level_id': median_level_id
	})

@csrf_exempt
def level_search(request):
	def sort_filter(value):
		return ":asc" in value or ":desc" in value

	form = AdvancedSearchForm(request.GET or None)

	#initial data gathering
	if form.is_valid():
		query = form.cleaned_data['query']
		limit = form.cleaned_data['limit'] or 10
		offset = form.cleaned_data['offset'] or 0
		sort = list(filter(sort_filter, (form.cleaned_data['sort']).split(",")))
		search_filter = form.cleaned_data['filter']
	else:
		query = ""
		offset = 0
		limit = 10
		sort = []
		search_filter = None

	#data sanitization
	if "cache_downloads:asc" not in sort and "cache_downloads:desc" not in sort:
		sort.append("cache_downloads:desc")

	if limit > 1000: limit = 1000

	try:
		index = meili_utils.get_level_index()
		search_result = index.search(query, {
			'limit': limit,
			'offset': offset,
			'sort': sort,
			'filter': search_filter
		})

		return JsonResponse(search_result)
	except meilisearch.errors.MeilisearchCommunicationError:
		return JsonResponse({'success': False, 'error': 'MeilisearchCommunicationError'}, status=500)
	except:
		print(sys.exc_info())
		return JsonResponse({'success': False, 'error': 'generic'}, status=500)
	
@csrf_exempt
def daily(request):
	return JsonResponse(utils.get_daily_records())

@csrf_exempt
def daily_current_year(request):
	return JsonResponse(utils.get_daily_records_current_year())