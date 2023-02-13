import os
import pickle
import re
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

    print(api_key)
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

def video_request(vid_id):
    pass

def get_playlist_videos(playlist_id, nextPageToken=None):
    pl_request = youtube.playlistItems().list(
        part='contentDetails, snippet',
        playlistId=playlist_id,
        maxResults=50,
        pageToken=nextPageToken)
    pl_response = pl_request.execute()
    vid_ids = []
    for item in pl_response['items']:
        vid_ids.append(item['contentDetails']['videoId'])
    nextPageToken = pl_response.get('nextPageToken')
    return pl_response, vid_ids

def get_videos(vid_ids):
    nextPageToken = get_playlist_response.get('nextPageToken')
    vid_request = youtube.videos().list(
        part="contentDetails, snippet, statistics",
        id=','.join(vid_ids))
    vid_response = vid_request.execute()
    return vid_response

def get_song_info(items, video_list):
    for item in items:
            # print(item['statistics']['viewCount'])
            song_id = item['id']
            yt_link = f'https://youtu.be/{song_id}'
            song_title = item['snippet']['localized']['title']
            artist = item['snippet']['tags'][0]
            duration = item['contentDetails']['duration']
            song_viewcount = int(item['statistics']['viewCount'])
            song_list.append({'id': song_id, 'title': song_title, 
                            'artist': artist, 'views': song_viewcount, 
                            'link': yt_link, 'duration': duration})
    return video_list

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
            ).total_seconds()
    return video_seconds

def get_playlist_duration(items):
    total_seconds = 0
    for item in items:
            duration = item['contentDetails']['duration']
            video_seconds = get_video_duration(duration)
            total_seconds += video_seconds
    return total_seconds

def create_playlist(name, channel_id):
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

def add_videos_to_playlist(video_list, playlist_id):
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
            body = request_body
        )
        add_video_response = add_video_request.execute()


# scopes = ['https://www.googleapis.com/auth/youtube.readonly']
scopes = ['https://www.googleapis.com/auth/youtube']
channel_id = 'UCpRrrf9yZQi6Uyc8iRxv47Q'
base_playlist_id = 'PLhrHTD00aJrFJXg94UJoz-EexjH51C5eI'
new_playlist_name = 'test'
credentials = authenticate(scopes)
youtube = build('youtube', 'v3', credentials=credentials)
total_seconds = 0
nextPageToken = None
song_list = []

while True:
    get_playlist_response, vid_ids = get_playlist_videos(playlist_id=base_playlist_id)
    videos_response = get_videos(vid_ids)
    total_seconds = get_playlist_duration(videos_response['items'])
    song_list = get_song_info(videos_response['items'], song_list, total_seconds)
    if not nextPageToken:
        break

total_seconds = int(total_seconds)
total_time = datetime.fromtimestamp(total_seconds)

print(f'{total_time.hour}:{total_time.minute}:{total_time.second}')
print(len(song_list))

song_list.sort(key=lambda x:(x['artist'], reversor(x['views']), x['title']))
playlist_id = create_playlist(new_playlist_name, channel_id)
add_videos_to_playlist(song_list, playlist_id)