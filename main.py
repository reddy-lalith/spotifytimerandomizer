from flask import Flask, redirect, request, session, url_for, make_response
from spotipy.oauth2 import SpotifyOAuth
import requests
import random
import os
import config  # Import the configuration file

# Flask app setup
app = Flask(__name__)
app.secret_key = 'some_random_secret'  # Change this for production

# Spotify credentials and other constants
CLIENT_ID = config.SPOTIPY_CLIENT_ID
CLIENT_SECRET = config.SPOTIPY_CLIENT_SECRET
REDIRECT_URI = 'https://www.spotifytime.com/callback'
SCOPE = 'user-modify-playback-state user-read-playback-state user-read-private'
USERNAME = ''


@app.route('/')
def index():
    token = request.cookies.get('token')
    if not token:
        return redirect(url_for('login'))
    return '''
    <form action="/play" method="post">
        Playlist ID: <input type="text" name="playlist_id">
        <input type="submit" value="Play Random Song">
    </form>
    '''


@app.route('/login')
def login():
    sp_oauth = SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, scope=SCOPE)
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, scope=SCOPE)
    token_info = sp_oauth.get_access_token(request.args['code'])
    resp = make_response(redirect(url_for('index')))
    session['token'] = token_info['access_token']
    return resp


@app.route('/play', methods=['POST'])
def play():
    token = session.get('token')
    playlist_id = request.form['playlist_id']
    result = play_random_song_from_playlist(token, playlist_id)
    return result


def play_random_song_from_playlist(token, playlist_id):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Fetch playlist tracks
    response = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=headers)
    playlist_data = response.json()

    items = playlist_data.get('items', [])
    if not items:
        return "No songs found in the playlist."

    # Select a random song and get its URI
    track = random.choice(items)
    track_uri = track['track']['uri']

    # Get track duration and select a random start position
    duration_ms = track['track']['duration_ms']
    start_position = random.randint(0, duration_ms - 10000)  # -10000 to ensure at least 10 seconds playtime

    # Start playback at the random position
    playback_data = {
        "uris": [track_uri],
        "position_ms": start_position
    }
    response = requests.put("https://api.spotify.com/v1/me/player/play", headers=headers, json=playback_data)

    if response.status_code == 204:
        return f"Playing {track['track']['name']} from a random position."
    else:
        return f"Error starting playback: {response.text}"


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
