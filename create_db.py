#########################################
##### Name: Chao-Yuan Cheng         #####
##### Uniqname: crisscy             #####
#########################################
import json
import requests
import secrets 
from bs4 import BeautifulSoup
from apiclient.discovery import build
import sqlite3


#global variables
google_api_key = secrets.GOOGLE_API_KEY
musicmatch_api_key = secrets.MUSICMATCH_API_KEY
CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}
DB_NAME = 'country_song.sqlite'


def get_all_country():
	country_full_list = []
	country_abb_list = []
	country_dict = {}
	base_url_scrape = 'https://laendercode.net/en/2-letter-list.html'
	headers = {
		'User-Agent': 'UMSI 507 Course Final Project',
		'From': 'crisscy@umich.edu', 
		'Course-Info': 'https://si.umich.edu/programs/courses/507'
	}
	response = scrape_request(base_url_scrape, headers, CACHE_DICT)
	soup = BeautifulSoup(response, 'html.parser')
	tr = soup.find_all('tr')

	for i in tr[1:]:
		try:
			country_key = i.find_all('a')[1].text.strip().lower()
		except:
			pass
		try:
			country_abbre = i.find(class_='margin-clear').text.strip().lower()
		except:
			pass
		country_dict[country_key] = country_abbre
		country_full_list.append(country_key)
		country_abb_list.append(country_abbre)
	return country_full_list, country_abb_list, country_dict



def country_initialization():
	country_full_list = get_all_country()[0]
	country_full_abb_list = get_all_country()[1]
	country_full_dict = get_all_country()[2]
	return country_full_abb_list, country_full_dict


def get_country_charts(country_list):
	track_dict = {}

	for i in country_list:
		params = {
			'chart_name': 'top',
			'country': i,
			'page_size': 5,
			'page':1,
			'f_has_lyrics': 1
		}

		results = request_musixmatch('chart.tracks.get?', params, CACHE_DICT)
		results = json.loads(results)
		country_dict = {}

		for count, j in enumerate(results['message']['body']['track_list']):
			song_dict = {}
			song_dict['track_id'] = j['track']['track_id']
			song_dict['track_name'] = j['track']['track_name']
			song_dict['album_name'] = j['track']['album_name']
			song_dict['artist_name'] = j['track']['artist_name']
			country_dict['top_' + str(count+1)] = song_dict
			
		track_dict[i] = country_dict

	return track_dict

def get_lyrics(track_dict):
	for i, v in track_dict.items():
		for j, w in v.items():
			count = 0
			params = {
				'track_id': w['track_id']

			}
			results = request_musixmatch('track.lyrics.get?', params, CACHE_DICT)
			results = json.loads(results)
			lyrics = results['message']['body']['lyrics']['lyrics_body']
			try: 
				lyrics_language = results['message']['body']['lyrics']['lyrics_language']
			except:
				lyrics_language = 'not available'

			track_dict[i][j]['lyrics'] = lyrics
			track_dict[i][j]['lyrics_language'] = lyrics_language
	return track_dict	

def get_yt_id(track_dict):
	for i, v in track_dict.items():
		for j, w in v.items():
			track_name = w['track_name']
			artist_name = w['artist_name']
			searchq = track_name + ' ' + artist_name
			uni_id = "youtube_search_que_" + searchq
			results = request_youtube('get_id', searchq, uni_id, CACHE_DICT)
			results = json.loads(results)
			for k in results['items']:
				try:
					track_dict[i][j]['yt_videoID'] = k['id']['videoId']
				except:
					track_dict[i][j]['yt_videoID'] = None
				try:
					track_dict[i][j]['yt_videoTitle'] = k['snippet']['title']
				except:
					track_dict[i][j]['yt_videoTitle'] = None
				try:
					track_dict[i][j]['yt_url'] = 'https://www.youtube.com/watch?v='+ k['id']['videoId']
				except:
					track_dict[i][j]['yt_url'] = None

	return track_dict


def get_yt_stats(track_dict):
	for i, v in track_dict.items():
		for j, w in v.items():
			try:
				uni_id = w['yt_videoID'] 
				results = request_youtube('get_stats', w['yt_videoID'] , uni_id, CACHE_DICT)
				results = json.loads(results)
				track_dict[i][j]['yt_view_counts'] = results['items'][0]['statistics']['viewCount']
				track_dict[i][j]['yt_like_counts'] = results['items'][0]['statistics']['likeCount']
				track_dict[i][j]['yt_dislike_counts'] = results['items'][0]['statistics']['dislikeCount']
				track_dict[i][j]['yt_comment_counts'] = results['items'][0]['statistics']['commentCount']
			except:
				track_dict[i][j]['yt_view_counts'] = None
				track_dict[i][j]['yt_like_counts'] = None
				track_dict[i][j]['yt_dislike_counts'] = None
				track_dict[i][j]['yt_comment_counts'] = None
	return track_dict

def get_data_initializaton(top_country_abb_list):
	track_dict ={}
	track_dict = get_country_charts(top_country_abb_list)
	track_dict = get_lyrics(track_dict)
	track_dict = get_yt_id(track_dict)
	track_dict = get_yt_stats(track_dict)
	return track_dict


def request_youtube(method, params, uni_id, cache):
	if method == "get_id":
		if (uni_id in cache.keys()):
			print("Using cache")
			return cache[uni_id]
		else:
			print("Fetching")
			youtube = build('youtube','v3', developerKey = google_api_key)
			req = youtube.search().list(part='snippet', q=params, type='video', maxResults=1)
			res = req.execute()
			cache[uni_id] = json.dumps(res)
			save_cache(cache)
			return(cache[uni_id])
	elif method == "get_stats":
		if (uni_id in cache.keys()):
			print("Using cache")
			return cache[uni_id]
		else:
			print("Fetching")
			youtube = build('youtube','v3', developerKey = google_api_key)
			req = youtube.videos().list(part='snippet, statistics', id=params)
			res = req.execute()
			cache[uni_id] = json.dumps(res)
			save_cache(cache)
			return(cache[uni_id])

def request_musixmatch(method, params, cache):
	base_url_musixmatch = 'https://api.musixmatch.com/ws/1.1/' + method
	url_string = ""
	for i in params: 
		url_string += i + "=" +str(params[i]) + "&"

	url_musixmatch = base_url_musixmatch + url_string + "apikey=" + musicmatch_api_key

	if (url_musixmatch in cache.keys()):
		print("Using cache")
		return cache[url_musixmatch]
	else:
		print("Fetching")
		response = requests.get(url_musixmatch)
		cache[url_musixmatch] = response.text
		save_cache(cache)
		return cache[url_musixmatch]

def scrape_request(url, headers, cache):
	'''Making a url request. If the url is in cache dictionary, 
	then using the cache instead of making another url request.

	Parameters
	----------
	url: string
		a string that represents a url link
	cache: json
		a json file that stores the json data coming back from api and scraping

	Returns
	-------
	string
		a string that has the form of dictionary. 
	'''
	if (url in cache.keys()):
		print("Using cache")
		return cache[url]
	else:
		print("Fetching")
		response = requests.get(url, headers)
		cache[url] = response.text
		save_cache(cache)
		return cache[url]


def load_cache(): 
	'''called only once, when running the program
	
	Returns
	-------
	cache: dict
		A place to store the data we get back from making api calls.

	'''
	try:
		cache_file = open(CACHE_FILE_NAME, 'r') #open for reading
		cache_file_contents = cache_file.read()
		cache = json.loads(cache_file_contents)
		cache_file.close()
	except:
		cache = {}
	return cache

def save_cache(cache): 
	'''called whenever the cache is changed and save the file.
	
	Parameters
	----------
	cache: dict
		A place to store the data we get back from making api calls.

	Returns
	-------
	'''
	cache_file = open(CACHE_FILE_NAME, 'w') 
	contents_to_write = json.dumps(cache)
	cache_file.write(contents_to_write)
	cache_file.close()



def creat_db():
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

	drop_countries_sql = 'DROP TABLE IF EXISTS "Countries"'
	drop_videos_sql = 'DROP TABLE IF EXISTS "Videos"'

	create_countries_sql = '''
		CREATE TABLE IF NOT EXISTS "Countries" (
			'id' INTEGER PRIMARY KEY AUTOINCREMENT,
			'countries' TEXT NOT NULL,
			'alpha2' TEXT NOT NULL

		)
	'''
	create_videos_sql = '''
		CREATE TABLE IF NOT EXISTS "Videos"(
			'id' INTEGER PRIMARY KEY AUTOINCREMENT,
			'title' TEXT NOT NULL,
			'artist_name' TEXT NOT NULL,
			'album' TEXT NOT NULL,
			'countryId' INTEGER NOT NULL,
			'lyrics' TEXT NOT NULL,
			'url' TEXT,
			'views' INTEGER,
			'likes' INTEGER,
			'dislikes' INTEGER,
			'comment_count' INTEGER

		)
	'''
	cur.execute(drop_countries_sql)
	cur.execute(drop_videos_sql)
	cur.execute(create_countries_sql)
	cur.execute(create_videos_sql)
	conn.commit()
	conn.close()

def load_countries(country_dict):
	insert_sql = '''
	INSERT INTO Countries
	VALUES(NULL, ?, ?)
	'''
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

	for i, v in country_dict.items():
		cur.execute(insert_sql,
			[i, v]
			)
	conn.commit()
	conn.close()
	
def load_videos(track_dict):
	select_coutnry_id_sql = '''
	SELECT Id FROM Countries
	WHERE alpha2 = ?
	'''
	conn = sqlite3.connect(DB_NAME)
	cur = conn.cursor()

	insert_sql = '''
	INSERT INTO Videos
	VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	'''

	for i, v in track_dict.items():
		cur.execute(select_coutnry_id_sql, [i])
		res = cur.fetchone()
		country_location_id = None
		if res is not None:
			country_location_id = res[0]

		for j, w in v.items():
			try:
				cur.execute(insert_sql,
					[w['track_name'], w['artist_name'], w['album_name'], country_location_id, w['lyrics'], w['yt_url'], w['yt_view_counts'], w['yt_like_counts'], w['yt_dislike_counts'], w['yt_comment_counts']]
					)
			except:
				pass
	conn.commit()
	conn.close()



if __name__ == '__main__':  
	CACHE_DICT = load_cache()
	country_full_abb_list = country_initialization()[0]
	country_full_dict = country_initialization()[1]
	track_dict = get_data_initializaton(country_full_abb_list)
	creat_db()
	load_countries(country_full_dict)
	load_videos(track_dict)
	
	