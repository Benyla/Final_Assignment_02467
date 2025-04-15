import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import lyricsgenius
import pandas as pd
import time
from langdetect import detect
from pop_artists import top_pop_artists
from utils import get_english_lyrics, get_top_tracks_for_artist
from tqdm import tqdm


# ------------------------------
# Set up API Credentials
# ------------------------------

SPOTIFY_CLIENT_ID = "1e9f17fbe8f84b3ebabe5d48603e6ffc"
SPOTIFY_CLIENT_SECRET = "6f33b108987544418206cb70fd94d403"
GENIUS_ACCESS_TOKEN = "tRFnVnQJ2Ltli7ANNbqLg3I_Ir2NX7TX_iS6L7ufNGWFldulVJjGOmYiVb5w_EDl"

# ------------------------------
# Authenticate with Spotify & Genius
# ------------------------------

auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=10, retries=3)
genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN, timeout=15, retries=3)


# ------------------------------
# Data Collection from Spotify & Genius
# ------------------------------

data = []

for artist_name in tqdm(top_pop_artists, desc="Processing artists"):
    artist_results = sp.search(q=f"artist:{artist_name}", type="artist", limit=1)
    if not artist_results['artists']['items']:
        print(f"Artist {artist_name} not found on Spotify.")
        continue

    artist = artist_results['artists']['items'][0]
    artist_id = artist['id']
    print(f"Collecting top tracks for {artist_name}...")

    top_tracks = get_top_tracks_for_artist(artist_id, sp, max_tracks=50, country="US")
    print(f"Found {len(top_tracks)} top tracks for {artist_name}.")

    for track in top_tracks:

        track_id = track['id']
        full_track = sp.track(track_id)

        track_title = track['name']
        track_artists = [a['name'] for a in track['artists']]
        is_collaboration = len(track_artists) > 1
        track_id = track['id']
        track_duration = track['duration_ms'] / 1000
        album_info = full_track['album']
        release_date = album_info.get('release_date', 'Unknown')
        popularity = track.get('popularity', 0)

        lyrics = get_english_lyrics(track_title, artist_name, genius)

        if lyrics == False:
            print(f"Skipping {track_title} by {artist_name} due to missing lyrics.")
            continue

        time.sleep(0.5)

        data.append({
            "song_title": track_title,
            "artists": ", ".join(track_artists),
            "release_date": release_date,
            "popularity": popularity,
            "is_collaboration": is_collaboration,
            "duration_seconds": track_duration,
            "spotify_id": track_id,
            "lyrics": lyrics
        })

df = pd.DataFrame(data)
df.to_csv("spotify_genius_data.csv", index=False)