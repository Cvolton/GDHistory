import datetime
import base64
from django import template
from django.utils.safestring import mark_safe
from django.utils.http import urlencode
from django.utils.timezone import make_aware

from history.constants import MiscConstants, SongNames

register = template.Library()

@register.simple_tag
def user_record_to_username(record):
	if record.username:
		return record.username
	elif record.user.cache_non_player_username:
		return record.user.cache_non_player_username
	elif record.user.cache_username:
		return record.user.cache_username
	else:
		return "Unknown"

@register.simple_tag
def timestamp_to_printable_date(timestamp):
	date_time = make_aware(datetime.datetime.fromtimestamp(timestamp))
	return date_time.strftime("%b %d, %Y")

@register.simple_tag
def print_filters(filters):
	new_dict = {}
	for filter_string in filters:
		if filters[filter_string]:
			new_dict[filter_string] = filters[filter_string]
	return mark_safe(f"&{urlencode(new_dict)}")

@register.simple_tag
def print_filters_toggled(filters, to_toggle):
	filter_list = filters.copy()
	if to_toggle in filter_list: filter_list[to_toggle] = not filter_list[to_toggle]
	else: filter_list[to_toggle] = True
	return print_filters(filter_list)

@register.simple_tag
def print_filters_without(filters, to_delete):
	filter_list = filters.copy()
	if to_delete in filter_list: del filter_list[to_delete]
	return print_filters(filter_list)

@register.simple_tag
def print_search_th(filters, sort, default_desc, human_readable, default_arrow=False):
	filters_without = print_filters_without(filters, 's')
	sort_mark = ""
	if 's' in filters and filters['s'] == sort:
		default_desc = True
		sort_mark = " &#9650;"
	elif ('s' in filters and filters['s'] == f"-{sort}") or (default_arrow and not ('s' in filters and filters['s'])):
		default_desc = False
		sort_mark = " &#9660;"

	if default_desc == True:
		sort = f"-{sort}"

	return mark_safe(f'<a href="?p=1{filters_without}&s={sort}">{human_readable}{sort_mark}</a>')

@register.simple_tag
def level_password(password):
	if password == 0 or password is None:
		return "Not copyable"
	if password == 1:
		return "Free copy"
	return str(password)[1:]

@register.simple_tag
def song_name(song_id, game_version):
	if song_id is None:
		return SongNames.MAIN[0]

	if game_version is not None and game_version < 21:
		full_song_array = SongNames.PRACTICE + SongNames.MAIN[:20] + SongNames.MELTDOWN
	else:
		full_song_array = SongNames.PRACTICE + SongNames.MAIN + SongNames.MELTDOWN + SongNames.CHALLENGE + SongNames.WORLD + SongNames.SUBZERO

	song_id = song_id + 1
	if song_id < 0 or song_id > len(full_song_array):
		return "Unknown by DJVI"
	return full_song_array[song_id]

@register.simple_tag
def length(length_number):
	strings = ["Tiny","Short","Medium","Long","XL","Plat."]
	if length_number is None:
		return strings[0]

	if length_number >= 0 and length_number <= 5:
		return strings[length_number]

	return f"Unknown ({length_number})"

@register.simple_tag
def empty_none(content):
	if content is not None:
		return content
	return ""

@register.simple_tag
def display_number(number):
	if number is None:
		return 0
	return number

@register.simple_tag
def demon_type(demon_type_number):
	if demon_type_number is None:
		return ""
	if demon_type_number < 3:
		return "Hard"
	if demon_type_number < 7:
		type_list = ["Easy", "Medium", "Insane", "Extreme"]
		return type_list[demon_type_number - 3]
	
	return f"Hard ({demon_type})"

@register.simple_tag
def difficulty(rating_sum, rating, demon, auto, demon_type_number):
	if auto:
		return "Auto"

	if demon:
		return f"{demon_type(demon_type_number)} Demon"

	if rating == 0 or rating is None or rating_sum == 0 or rating_sum is None:
		return "N/A"

	diff = rating_sum / rating

	if diff < 0:
		return "N/A"

	if diff < 1.5:
		return "Easy"

	if diff < 2.5:
		return "Normal"

	if diff < 3.5:
		return "Hard"

	if diff < 4.5:
		return "Harder"

	if diff < 5.5:
		return "Insane"

@register.simple_tag
def game_version(number):
	if number is None:
		return None
	if number > 17:
		return "%.1f" % (number / 10)
	if number == 11:
		return "1.8"
	if number == 10:
		return "1.7"
	number -= 1
	return f"1.{number}"


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)