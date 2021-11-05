from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Min, Max, Q

from .models import Level, LevelRecord, Song, SaveFile, ServerResponse, LevelString
from .forms import UploadFileForm, SearchForm
from . import ccUtils, serverUtils

def index(request):
	recently_added = LevelRecord.objects.all().prefetch_related('level').order_by('-level__pk')[:5]
	recently_updated = LevelRecord.objects.all().prefetch_related('level').order_by('-pk')[:5]

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
	level_records = LevelRecord.objects.filter(level__online_id=online_id).prefetch_related('level').prefetch_related('level_string').annotate(oldest_created=Min('save_file__created')).order_by('-oldest_created')

	if len(level_records) == 0:
		return render(request, 'error.html', {'error': 'Level not found in our database'})

	context = {'level_records': level_records, 'level': level_records[0].level, 'online_id': online_id, 'years': [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]}

	serverUtils.download_level(online_id)

	return render(request, 'level.html', context)

@login_required
def upload(request):
	form = UploadFileForm(request.POST or None, request.FILES or None)
	if request.method == 'POST' and form.is_valid():
		ccUtils.process_save_file(request.FILES['file'], form.cleaned_data['time'])
		return HttpResponse("good")
	else:
		return render(request, 'upload.html')

def search(request):
	form = SearchForm(request.GET or None)

	if request.method == 'GET' and form.is_valid():
		query = form.cleaned_data['q']

		query_filter = Q(levelrecord__level_name__icontains=query) | Q(online_id=query) if query.isnumeric() else Q(levelrecord__level_name__icontains=query)

		levels = Level.objects.filter(query_filter).annotate(
			oldest_created=Max('levelrecord__save_file__created'),
			downloads=Max('levelrecord__downloads'),
			likes=Max('levelrecord__likes'),
			rating_sum=Max('levelrecord__rating_sum'),
			rating=Max('levelrecord__rating'),
			stars=Max('levelrecord__stars'),
			demon=Max('levelrecord__demon'),
			auto=Max('levelrecord__auto'),
			level_string=Max('levelrecord__level_string__pk'),
			).order_by('-oldest_created').order_by('-downloads').distinct().prefetch_related('levelrecord_set__save_file').prefetch_related('levelrecord_set__level_string')
		#level_records = LevelRecord.objects.filter(level__online_id=query).prefetch_related('level').prefetch_related('level_string').annotate(oldest_created=Min('save_file__created')).order_by('-oldest_created')

		if len(levels) < 1:
			return render(request, 'error.html', {'error': 'No results found'})

		context = {
			'query': query,
			'level_records': levels,
		}
		return render(request, 'search.html', context)
	else:
		return render(request, 'error.html', {'error': 'Invalid search query'})