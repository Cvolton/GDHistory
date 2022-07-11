from django.contrib import admin
from .models import HistoryUser, SaveFile, ServerResponse, Level, LevelRecord, Song, SongRecord, LevelString, GDUser, GDUserRecord, LevelDateEstimation

# Register your models here.
admin.site.register(HistoryUser)
admin.site.register(GDUser)
admin.site.register(GDUserRecord)
admin.site.register(SaveFile)
admin.site.register(ServerResponse)
admin.site.register(Level)
admin.site.register(LevelRecord)
admin.site.register(LevelString)
admin.site.register(Song)
admin.site.register(SongRecord)
admin.site.register(LevelDateEstimation)