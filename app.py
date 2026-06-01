from flask import Flask, render_template, request, jsonify
import requests
import os
import random
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LASTFM_API_KEY = os.getenv('LASTFM_API_KEY')
LASTFM_BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

def lastfm_get(params):
    params['api_key'] = LASTFM_API_KEY
    params['format'] = 'json'
    response = requests.get(LASTFM_BASE_URL, params=params)
    return response.json()

def get_top_tracks(artist, limit=10):
    data = lastfm_get({
        'method': 'artist.getTopTracks',
        'artist': artist,
        'limit': limit
    })
    tracks = data.get('toptracks', {}).get('track', [])
    return [format_track(t) for t in tracks]

def get_similar_artists(artist, limit=8):
    data = lastfm_get({
        'method': 'artist.getSimilar',
        'artist': artist,
        'limit': limit
    })
    artists = data.get('similarartists', {}).get('artist', [])
    return [{
        'name': a['name'],
        'image': get_image(a.get('image', [])),
    } for a in artists]

def get_artist_info(artist):
    data = lastfm_get({
        'method': 'artist.getInfo',
        'artist': artist
    })
    info = data.get('artist', {})
    return {
        'name': info.get('name', artist),
        'bio': info.get('bio', {}).get('summary', ''),
        'image': get_image(info.get('image', [])),
        'tags': [t['name'] for t in info.get('tags', {}).get('tag', [])[:5]],
        'listeners': info.get('stats', {}).get('listeners', ''),
    }

def get_deep_cuts(artist, limit=10):
    data = lastfm_get({
        'method': 'artist.getTopTracks',
        'artist': artist,
        'limit': 200
    })
    tracks = data.get('toptracks', {}).get('track', [])
    if len(tracks) > 50:
        deep = tracks[50:]
        random.shuffle(deep)
        return [format_track(t) for t in deep[:limit]]
    return [format_track(t) for t in tracks]

def get_random_track(artist):
    data = lastfm_get({
        'method': 'artist.getTopTracks',
        'artist': artist,
        'limit': 200
    })
    tracks = data.get('toptracks', {}).get('track', [])
    if not tracks:
        return None
    track = random.choice(tracks)
    return format_track(track)


def format_track(track):
    name = track.get('name', '')
    artist = track.get('artist', {}).get('name', '') if isinstance(track.get('artist'), dict) else track.get('artist', '')
    return {
        'name': name,
        'artist': artist,
        'playcount': track.get('playcount', ''),
        'spotify_url': f"https://open.spotify.com/search/{requests.utils.quote(name + ' ' + artist)}",
        'apple_url': f"https://music.apple.com/search?term={requests.utils.quote(name + ' ' + artist)}",
        'youtube_url': f"https://music.youtube.com/search?q={requests.utils.quote(name + ' ' + artist)}",
    }

def get_image(images):
    for img in reversed(images):
        if img.get('#text'):
            return img['#text']
    return ''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search_artist')
def search_artist():
    query = request.args.get('q', '')
    data = lastfm_get({
        'method': 'artist.search',
        'artist': query,
        'limit': 5
    })
    artists = data.get('results', {}).get('artistmatches', {}).get('artist', [])
    return jsonify([{
        'name': a['name'],
        'listeners': a.get('listeners', ''),
        'image': get_image(a.get('image', []))
    } for a in artists])

@app.route('/artist/<path:artist_name>')
def artist(artist_name):
    size = int(request.args.get('size', 10))
    info = get_artist_info(artist_name)
    popular = get_top_tracks(artist_name, size)
    deep_cuts = get_deep_cuts(artist_name, size)
    random_track = get_random_track(artist_name)
    similar = get_similar_artists(artist_name)

    return jsonify({
        'info': info,
        'popular': popular,
        'deep_cuts': deep_cuts,
        'random': random_track,
        'similar': similar
    })

if __name__ == '__main__':
    app.run(debug=True)