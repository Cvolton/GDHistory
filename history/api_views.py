from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Min, Max, Q
from django.db.models.functions import Coalesce
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import make_aware

from datetime import datetime, timedelta

from .models import LevelRecord, LevelDateEstimation, GDUserRecord
from . import ccUtils, serverUtils, tasks, utils, constants

import math
import plistlib

@csrf_exempt
def index_counts(request):
	counts = cache.get('counts')
	if counts is None:
		counts = utils.recalculate_counts()

	return JsonResponse(counts)

@csrf_exempt
def save_level(request, online_id=None):
	level = utils.get_level_object(online_id)
	if level.needs_priority_download: return JsonResponse({'success': False, 'fail_reason': constants.SaveFailReasons.ALREADY_QUEUED})

	level.needs_priority_download = True
	level.save()

	return JsonResponse({'success': True})

@csrf_exempt
def level_info(request, online_id=None, view_mode="normal"):
	all_levels = LevelRecord.objects.filter(level__is_public=True)
	#TODO: improve this
	if request.user.is_authenticated and request.user.is_superuser:
		all_levels = LevelRecord.objects.all()

	level_records = all_levels.filter(level__online_id=online_id).exclude(level_version=None).prefetch_related('level').prefetch_related('level_string').prefetch_related('real_user_record__user').prefetch_related('song').annotate(oldest_created=Min('save_file__created'), real_date=Coalesce('oldest_created', 'server_response__created', 'manual_submission__created')).order_by('-real_date')
	if view_mode == "brief":
		level_records = level_records[:1]
	if len(level_records) == 0:
		return JsonResponse({'success': False}, status=404)

	level = level_records[0].level

	response = level.get_serialized_base()

	level_strings = {}
	response['level_string_count'] = 0
	if view_mode != "brief":
		response['records'] = []
		for record in level_records:
			response['records'].append(record.get_serialized_full())

			if record.level_string is not None and record.level_string.pk not in level_strings:
				response['level_string_count'] += 1
				level_strings[record.level_string.pk] = True


	return JsonResponse(response)

@csrf_exempt
def user_info(request, online_id=None, view_mode="normal"):
	all_users = GDUserRecord.objects.all()

	user_records = all_users.filter(user__online_id=online_id).prefetch_related('user').order_by('-cache_created')
	if view_mode == "brief":
		user_records = user_records[:1]
	if len(user_records) == 0:
		return JsonResponse({'success': False}, status=404)

	user = user_records[0].user

	response = user.get_serialized_base()

	user_strings = {}
	if view_mode != "brief":
		response['records'] = []
		for record in user_records:
			response['records'].append(record.get_serialized_full())

	return JsonResponse(response)

@csrf_exempt
def level_date_estimation(request, online_id):
	online_id = int(online_id)

	low = LevelDateEstimation.objects.prefetch_related('level').filter(cache_online_id__lte=online_id).order_by('-cache_online_id', 'estimation')[:1]
	high = LevelDateEstimation.objects.prefetch_related('level').filter(cache_online_id__gte=online_id).order_by('cache_online_id', 'estimation')[:1]

	approx = None
	if low and high:
		date_difference = high[0].estimation - low[0].estimation
		id_difference = high[0].level.online_id - low[0].level.online_id
		requested_id_difference = online_id - low[0].level.online_id
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

	low = LevelDateEstimation.objects.prefetch_related('level').filter(estimation__lte=online_date).order_by('-estimation', 'cache_online_id')[:1]
	high = LevelDateEstimation.objects.prefetch_related('level').filter(estimation__gte=online_date).order_by('estimation', 'cache_online_id')[:1]

	approx = None
	if low and high and low[0].estimation != high[0].estimation:
		date_difference = high[0].estimation - low[0].estimation
		id_difference = high[0].level.online_id - low[0].level.online_id
		requested_date_difference = online_date - low[0].estimation
		percentage = requested_date_difference / date_difference
		new_id_difference = id_difference * percentage
		approx = {
			"estimation": online_date,
			"online_id": math.floor(low[0].level.online_id + new_id_difference)
		}

	response = {
		'low': low[0].get_serialized_base() if len(low) > 0 else None,
		'high': high[0].get_serialized_base()  if len(high) > 0 else None,
		'approx': approx
	}
	
	return JsonResponse(response)
