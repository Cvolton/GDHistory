from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Min

from .models import Level, LevelRecord
from .forms import UploadFileForm
from . import ccUtils, serverUtils

def index(request):
	return render(request, 'index.html')

def view_level(request, online_id=None):
	level_records = LevelRecord.objects.filter(level__online_id=online_id).prefetch_related('level').annotate(oldest_created=Min('save_file__created'))

	if len(level_records) == 0:
		return render(request, 'error.html', {'error': 'Level not found in our database'})

	context = {'level_records': level_records, 'level': level_records[0].level, 'online_id': online_id}

	serverUtils.download_level(online_id)

	return render(request, 'level.html', context)

def upload(request):
	form = UploadFileForm(request.POST or None, request.FILES or None)
	if request.method == 'POST':
		ccUtils.process_save_file(request.FILES['file'])
		return HttpResponse("good")
	else:
		return render(request, 'upload.html')
