from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Min

from .models import Level, LevelRecord, Song, SaveFile, ServerResponse, LevelString
from .forms import UploadFileForm
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
	level_records = LevelRecord.objects.filter(level__online_id=online_id).prefetch_related('level').annotate(oldest_created=Min('save_file__created'))

	if len(level_records) == 0:
		return render(request, 'error.html', {'error': 'Level not found in our database'})

	context = {'level_records': level_records, 'level': level_records[0].level, 'online_id': online_id}

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
