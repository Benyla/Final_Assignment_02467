import re
from langdetect import detect
import lyricsgenius
import contextlib
import io


def is_english(text): # helper func to check if lyrics are in English
    try:
        return detect(text) == 'en'
    except:
        return False
    
def clean_lyrics(raw_lyrics): # helper func to clean the lyrics
    raw_lyrics = raw_lyrics.split("Lyrics", 1)[-1]
    if "Read More" in raw_lyrics:
        raw_lyrics = raw_lyrics.split("Read More", 1)[-1]
    raw_lyrics = re.sub(r"^[^\n]*Contributors[^\n]*\n", "", raw_lyrics, flags=re.MULTILINE)
    raw_lyrics = re.sub(r"\[.*?\]", "", raw_lyrics)
    raw_lyrics = re.sub(r"\n{2,}", "\n", raw_lyrics)
    raw_lyrics = raw_lyrics.replace('\n', ' ')
    raw_lyrics = raw_lyrics.replace("\\", "") 
    return raw_lyrics.strip() 

def silent_search_song(title, artist, genius): # to suppress output from the search
    with contextlib.redirect_stdout(io.StringIO()):
        return genius.search_song(title, artist)
    
# ------------------------------
# Function that gets english lyrics for a given song title and artist
# ------------------------------
def get_english_lyrics(title, artist, genius):
    try:
        song = silent_search_song(title, artist, genius)
        if song:
            lyrics = clean_lyrics(song.lyrics)
            if is_english(lyrics):
                return lyrics
            else:
                print(f"Non-English lyrics for {title} by {artist}, retrying with 'English' hint...")
                song = silent_search_song(f"{title} English", artist, genius)
                if song:
                    lyrics = clean_lyrics(song.lyrics)
                    if is_english(lyrics):
                        print(f"Found English lyrics for {title} by {artist} on retry.")
                        return lyrics
        return False
    except Exception as e:
        print(f"Error retrieving lyrics for {title} by {artist}: {e}")
        return False

# ------------------------------
# Gets top 50 (if available) tracks for a given artist
# ------------------------------
def get_top_tracks_for_artist(artist_id, sp, max_tracks=50, country="US"):
    albums_response = sp.artist_albums(artist_id, album_type="album,single", country=country, limit=50)
    album_ids = list({album['id'] for album in albums_response['items']})
    track_ids = set()
    for album_id in album_ids:
        album_tracks = sp.album_tracks(album_id)['items']
        for track in album_tracks:
            track_ids.add(track['id'])
    track_ids = list(track_ids)
    full_tracks = []
    for i in range(0, len(track_ids), 50):
        batch = track_ids[i:i+50]
        results = sp.tracks(batch)
        full_tracks.extend(results['tracks'])
    full_tracks = [t for t in full_tracks if t is not None]
    sorted_tracks = sorted(full_tracks, key=lambda x: x.get('popularity', 0), reverse=True)
    return sorted_tracks[:max_tracks]
