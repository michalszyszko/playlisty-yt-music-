# TO DO
# add a function to clear a playlist, connect to spotify API, transfer playlist, sort by albums and album position
import os
import requests
import urllib.parse
import pickle
import re
import json
from pprint import pprint
from datetime import datetime
from datetime import timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from googleapiclient.errors import HttpError


class reversor:
    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        return other.obj == self.obj

    def __lt__(self, other):
           return other.obj < self.obj
    
def authenticate(scopes):
    current_dir = os.path.dirname(os.path.join(os.path.realpath(__file__)))
    with open(os.path.join(current_dir, 'api_key'), 'r') as file:
        api_key = file.read()

    # print(api_key)
    credentials = None
    if os.path.exists(os.path.join(current_dir, 'token.pickle')):
        print('Loading Credentials From File...')
        with open(os.path.join(current_dir, 'token.pickle'), 'rb') as token:
            credentials = pickle.load(token)

    # If there are no valid credentials available, then either refresh the token or log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print('Refreshing Access Token...')
            credentials.refresh(Request())
        else:
            print('Fetching New Tokens...')
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(current_dir, 'client_secrets.json'),
                scopes=scopes
            )

            flow.run_local_server(port=8080, prompt='consent',
                                authorization_prompt_message='')
            credentials = flow.credentials

            # Save the credentials for the next run
            with open(os.path.join(current_dir, 'token.pickle'), 'wb') as f:
                print('Saving Credentials for Future Use...')
                pickle.dump(credentials, f)

    return credentials

def load_frequency_config(config_filename):
    current_directory = os.path.dirname(os.path.realpath(__file__))
    if os.path.exists(os.path.join(current_directory, config_filename)):
        with open(os.path.join(current_directory, config_filename), 'r') as config_file:
            frequencies = json.load(config_file)
            return frequencies
    return None

def get_playlist_videos(youtube, playlist_id, nextPageToken=None):
    pl_request = youtube.playlistItems().list(
        part='contentDetails, snippet',
        playlistId=playlist_id,
        maxResults=50,
        pageToken=nextPageToken)
    pl_response = pl_request.execute()
    vid_ids = []
    for item in pl_response['items']:
        vid_ids.append(item['contentDetails']['videoId'])
    return pl_response, vid_ids

def get_videos(youtube, vid_ids):
    vid_request = youtube.videos().list(
        part="contentDetails, snippet, statistics",
        id=','.join(vid_ids))
    vid_response = vid_request.execute()
    return vid_response

def get_song_info_youtube(items, video_list, frequencies=None):
    current_directory = os.path.dirname(os.path.realpath(__file__))
    for item in items:
        # print(item['statistics']['viewCount'])
        song_id = item['id']
        yt_link = f'https://youtu.be/{song_id}'
        song_title = item['snippet']['localized']['title']
        artist = item['snippet']['tags'][0]
        duration = item['contentDetails']['duration']
        song_viewcount = int(item['statistics']['viewCount'])
        if frequencies:
            if song_id in frequencies:
                song_list.append({'id': song_id, 'title': song_title, 
                                'artist': artist, 'views': song_viewcount, 
                                'link': yt_link, 'duration': duration, 
                                'frequency':frequencies[song_id]['frequency']})
            else: 
                song_list.append({'id': song_id, 'title': song_title, 
                                'artist': artist, 'views': song_viewcount, 
                                'link': yt_link, 'duration': duration, 
                                'frequency': 1})
                
                frequencies[song_id]['id'] = song_id
                frequencies[song_id]['title'] = song_title
                frequencies[song_id]['artist'] = artist
                frequencies[song_id]['frequency'] = 1
                with open(os.path.join(current_directory, config_filename), 'w') as config_file:
                    json.dump(frequencies, config_file, indent=2)
        else:
            song_list.append({'id': song_id, 'title': song_title, 
                            'artist': artist, 'views': song_viewcount, 
                            'link': yt_link, 'duration': duration})
    return video_list

def get_song_info_spotify(song_info):
    # pprint(song_info)
    search_url = 'https://api.spotify.com/v1/search'
    client_id = 'a1207442b6e94da2b337583fa004fd03'
    client_secret = '75824cc5047b4dc496bb1fe74729a9f7'
    auth_url = 'https://accounts.spotify.com/api/token'
    get_track_url = 'https://api.spotify.com/v1/tracks'
    get_album_url = 'https://api.spotify.com/v1/albums'

    auth_response = requests.post(auth_url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })

    auth_response_data = auth_response.json()
    access_token = auth_response_data['access_token']
    # print(access_token)
    headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
    }
    for song in song_info:
        try:
            track_query = f'''{song['title']} {song['artist']}'''
            find_track_url = f'https://api.spotify.com/v1/search?query={urllib.parse.quote(track_query)}&type=track&locale=en-US%2Cen%3Bq%3D0.5&offset=0&limit=5'
            find_track_response = requests.get(f'{find_track_url}', headers=headers)
            find_track_response = find_track_response.json()
            track_id = find_track_response['tracks']['items'][0]['id']
            track_name = find_track_response['tracks']['items'][0]['name']
            # print(find_track_response['tracks']['items'][0]['external_urls'])
            # print(track_name)
            # print(track_id)

            get_track_response = requests.get(f'{get_track_url}/{track_id}', headers=headers)
            get_track_response = get_track_response.json()
            # print(get_track_response.keys())
            song_name = get_track_response['name']
            artist = get_track_response['artists'][0]['name']
            album_name = get_track_response['album']['name']
            album_uri = get_track_response['album']['uri'].split(':')[-1]

            get_album_response = requests.get(f'{get_album_url}/{album_uri}', headers=headers)
            get_album_response = get_album_response.json()
            # print(get_album_response)
            # print(get_album_response.keys())    
            # print(get_album_response['tracks'])
            # print(get_album_response['tracks'].keys())
            song_index = -1
            for n, item in enumerate(get_album_response['tracks']['items'], 1):
                if item['name'] == song_name:
                    song_index = n
        except:
            print(f'''Error retrieving song data through spotify api. Song title: {song['title']}''')

        # print(song_name)
        # print(artist)
        # print(album_name)
        # print(song_index)
        song['album_name'] = album_name
        song['song_index'] = song_index
        print(f'''{song['title']} {song['artist']} {song['album_name']} {song_index}''')
    
    return song_info

def get_video_duration(duration):
    hours_pattern = re.compile(r'(\d+)H')
    minutes_pattern = re.compile(r'(\d+)M')
    seconds_pattern = re.compile(r'(\d+)S')
    hours = hours_pattern.search(duration)
    minutes = minutes_pattern.search(duration)
    seconds = seconds_pattern.search(duration)
    hours = int(hours.group(1)) if hours else 0
    minutes = int(minutes.group(1)) if minutes else 0
    seconds = int(seconds.group(1)) if seconds else 0
    video_seconds = timedelta(
                hours=hours,
                minutes=minutes,
                seconds=seconds
            )
    return video_seconds

def get_playlist_duration(items):
    total_seconds = timedelta(0)
    for item in items:
            duration = item['contentDetails']['duration']
            video_seconds = get_video_duration(duration)
            total_seconds += video_seconds
    return total_seconds

def create_playlist(youtube, name, channel_id):
    create_playlist_request = youtube.playlists().insert(
    part='contentDetails, snippet',
    body={
    'snippet': {
        'title': name,
        'channelId': channel_id
    }})
    create_playlist_response = create_playlist_request.execute()
    playlist_id = create_playlist_response['id']
    # print(create_playlist_response)
    return playlist_id

def add_videos_to_playlist(youtube, video_list, playlist_id, frequencies=None):
    for video in video_list:
        print(f'''{video['artist']}, {video['views']}, {video['title']} {video['id']}''')
        request_body = {
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video['id']
                }}
            }
        
        add_video_request = youtube.playlistItems().insert(
        part='snippet',
        body = request_body)
        responses = []
        if frequencies:
            for _ in range(int(frequencies[video['id']]['frequency'])):
                add_video_response = add_video_request.execute()
                responses.append(add_video_response)
        else:
            add_video_response = add_video_request.execute()
            responses.append(add_video_response)
    return responses

def clear_playlist(playlist_id):
    pass


if __name__ == '__main__':
    # scopes = ['https://www.googleapis.com/auth/youtube.readonly']
    scopes = ['https://www.googleapis.com/auth/youtube']
    channel_id = 'UCpRrrf9yZQi6Uyc8iRxv47Q'
    base_playlist_id = 'PLhrHTD00aJrFJXg94UJoz-EexjH51C5eI'
    new_playlist_name = 'test'
    config_filename = 'config.txt'
    total_time = timedelta(0)
    nextPageToken = None
    song_list = []
    current_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)))

    credentials = authenticate(scopes)
    youtube = build('youtube', 'v3', credentials=credentials)
    frequencies = load_frequency_config(config_filename)
    while True:
        get_playlist_videos_response, vid_ids = get_playlist_videos(youtube, playlist_id=base_playlist_id, nextPageToken=nextPageToken)
        nextPageToken = get_playlist_videos_response.get('nextPageToken')
        videos_response = get_videos(youtube, vid_ids)
        total_time += get_playlist_duration(videos_response['items'])
        song_list = get_song_info_youtube(videos_response['items'], song_list, frequencies=None)
        song_list = get_song_info_spotify(song_list)
        # pprint(song_list)
        if not nextPageToken:
            break
    
    hours, remainder = divmod(total_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f'{hours}:{minutes}:{seconds}')
    print(len(song_list))
  
    song_list.sort(key=lambda x:(x['artist'], x['album_name'], x['song_index'], reversor(x['views']), x['title']))
    playlist_id = create_playlist(youtube, new_playlist_name, channel_id)
    print(f'created a playlist: {playlist_id}')
    add_videos_to_playlist(youtube, song_list, playlist_id, frequencies=None)