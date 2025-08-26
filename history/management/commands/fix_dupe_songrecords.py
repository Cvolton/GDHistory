import math
from history.models import Level, Song
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
    help = 'Fixes duplicate song records'

    def handle(self, *args, **options):
        max_song_id = Song.objects.order_by('-pk').first().pk if Song.objects.exists() else 0
        batch_size = 100000
        for i in range(0, math.ceil(max_song_id / batch_size)):
            start = i * batch_size
            end = (i + 1) * batch_size
            songs = Song.objects.filter(pk__gte=start, pk__lt=end)
            for song in songs:
                #print(f"song record count: {song.songrecord_set.count()}")
                all_records = {}
                """
                song=song_object,
                song_name = assign_key_no_pop(data, 2),
                artist_id = assign_key_no_pop(data, 3),
                artist_name = assign_key_no_pop(data, 4),
                size = assign_key_no_pop(data, 5),
                youtube_id = assign_key_no_pop(data, 6),
                youtube_channel = assign_key_no_pop(data, 7),
                is_verified = assign_key_no_pop(data, 8),
                link = link,
                record_type = record_type
                """
                for record in song.songrecord_set.all():
                    song_record_string = f"{song.online_id}::{record.song_name}::{record.artist_name}::{record.size}::{record.youtube_id}::{record.youtube_channel}::{record.is_verified}::{record.link}::{record.record_type}"
                    #print(song_record_string)
                    if song_record_string not in all_records:
                        all_records[song_record_string] = []
                    all_records[song_record_string].append(record)
                for record_string, records in all_records.items():
                    if len(records) > 1:
                        print(f"Duplicate found ({len(records)} entries): {record_string}")
                        dupes_to_delete = records[1:]
                        main_record = records[0]
                        all_saves = []
                        all_server_responses = []
                        for record in dupes_to_delete:
                            all_saves.extend(record.save_file.all())
                            all_server_responses.extend(record.server_response.all())
                        main_record.save_file.add(*all_saves)
                        main_record.server_response.add(*all_server_responses)
                        for record in dupes_to_delete:
                            record.delete()