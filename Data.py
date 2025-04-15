import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import lyricsgenius
import pandas as pd
import time
from langdetect import detect
from pop_artists import top_pop_artists
from utils import get_english_lyrics, get_top_tracks_for_artist
from tqdm import tqdm
import os

# ------------------------------
# Set up API Credentials
# ------------------------------

SPOTIFY_CLIENT_ID = "695cb4867ecd4f4fbbafa14cfba58fec"
SPOTIFY_CLIENT_SECRET = "e1626972052b48df90527dfc30c31d66"
GENIUS_ACCESS_TOKEN = "tRFnVnQJ2Ltli7ANNbqLg3I_Ir2NX7TX_iS6L7ufNGWFldulVJjGOmYiVb5w_EDl"

# ------------------------------
# Authenticate with Spotify & Genius
# ------------------------------

auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID,
                                          client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=10, retries=3)
genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN, timeout=15, retries=3)

# ------------------------------
# Caching Setup
# ------------------------------

cache_file = "spotify_genius_data.csv"
data = []
processed_artists = set()

if os.path.exists(cache_file):
    df_cache = pd.read_csv(cache_file)
    data = df_cache.to_dict(orient="records")
    # Assuming each record has a 'primary_artist' field.
    for row in data:
        processed_artists.add(row.get("primary_artist", "").lower())

# ------------------------------
# Data Collection from Spotify & Genius
# ------------------------------

for artist_name in tqdm(top_pop_artists, desc="Processing artists"):
    # Skip artist if already processed
    if artist_name.lower() in processed_artists:
        tqdm.write(f"Skipping {artist_name} (already processed).")
        continue

    artist_results = sp.search(q=f"artist:{artist_name}", type="artist", limit=1)
    if not artist_results['artists']['items']:
        tqdm.write(f"Artist {artist_name} not found on Spotify.")
        continue

    artist = artist_results['artists']['items'][0]
    artist_id = artist['id']
    tqdm.write(f"Collecting top tracks for {artist_name}...")

    top_tracks = get_top_tracks_for_artist(artist_id, sp, max_tracks=50, country="US")
    tqdm.write(f"Found {len(top_tracks)} top tracks for {artist_name}.")

    # Process each track for this artist
    for track in tqdm(top_tracks, desc=f"Processing tracks for {artist_name}"):
        track_id = track['id']
        # We call sp.track(track_id) to get full metadata (since top_tracks may be simplified)
        try:
            full_track = sp.track(track_id)
        except Exception as e:
            tqdm.write(f"Error fetching full track data for {track_id}: {e}")
            continue

        track_title = track['name']
        track_artists = [a['name'] for a in track['artists']]
        is_collaboration = len(track_artists) > 1
        track_duration = track['duration_ms'] / 1000
        album_info = full_track.get('album', {})
        release_date = album_info.get('release_date', 'Unknown')
        popularity = track.get('popularity', 0)

        lyrics = get_english_lyrics(track_title, artist_name, genius)
        if lyrics is False:
            tqdm.write(f"Skipping {track_title} by {artist_name} due to missing lyrics.")
            continue

        time.sleep(0.5)

        data.append({
            "primary_artist": artist_name,
            "song_title": track_title,
            "artists": ", ".join(track_artists),
            "release_date": release_date,
            "popularity": popularity,
            "is_collaboration": is_collaboration,
            "duration_seconds": track_duration,
            "spotify_id": track_id,
            "lyrics": lyrics
        })

    # After processing an artist, update the cache file.
    df = pd.DataFrame(data)
    df.to_csv(cache_file, index=False)
    processed_artists.add(artist_name.lower())
    tqdm.write(f"Cached data for {artist_name}. Total tracks so far: {len(data)}")

print("Data collection complete. Here's a preview:")
print(pd.DataFrame(data).head())