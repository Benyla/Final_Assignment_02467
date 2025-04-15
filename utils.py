import re
from langdetect import detect
import lyricsgenius
import contextlib
import io

def is_english(text):
    try:
        return detect(text) == 'en'
    except:
        return False
    
def clean_lyrics(raw_lyrics):
    raw_lyrics = raw_lyrics.split("Lyrics", 1)[-1]
    raw_lyrics = re.sub(r"^[^\n]*Contributors[^\n]*\n", "", raw_lyrics, flags=re.MULTILINE)
    raw_lyrics = re.sub(r"\[.*?\]", "", raw_lyrics)
    raw_lyrics = re.sub(r"\n{2,}", "\n", raw_lyrics)
    raw_lyrics = raw_lyrics.replace('\n', ' ')
    raw_lyrics = raw_lyrics.replace("\\", "") 
    return raw_lyrics.strip() 

def silent_search_song(title, artist, genius):
    with contextlib.redirect_stdout(io.StringIO()):
        return genius.search_song(title, artist)
    
def get_english_lyrics(title, artist, genius):
    try:
        song = silent_search_song(title, artist, genius)
        if song:
            lyrics = clean_lyrics(song.lyrics)
            if is_english(lyrics):
                return lyrics
            else:
                # Retry with 'English' in title
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

def get_top_tracks_for_artist(artist_id, sp, max_tracks=50, country="US"):
    """
    Retrieves all unique tracks from an artist's albums and singles, then returns
    up to max_tracks sorted by popularity (most popular first).
    
    Parameters:
        artist_id (str): The Spotify artist ID.
        sp (spotipy.Spotify): An authenticated Spotify client.
        max_tracks (int): Maximum number of tracks to return.
        country (str): Country code (used for album filtering).

    Returns:
        List[dict]: A list of track dictionaries with full metadata,
                    sorted in descending order of popularity.
    """
    # Fetch albums and singles for the artist
    albums_response = sp.artist_albums(artist_id, album_type="album,single", country=country, limit=50)
    
    # Get unique album IDs (to avoid duplicates from re-releases)
    album_ids = list({album['id'] for album in albums_response['items']})
    
    # Collect unique track IDs from each album
    track_ids = set()
    for album_id in album_ids:
        album_tracks = sp.album_tracks(album_id)['items']
        for track in album_tracks:
            track_ids.add(track['id'])
    
    # Convert set to list
    track_ids = list(track_ids)
    
    # Fetch full track details in batches (Spotify API allows up to 50 IDs per call)
    full_tracks = []
    for i in range(0, len(track_ids), 50):
        batch = track_ids[i:i+50]
        results = sp.tracks(batch)
        full_tracks.extend(results['tracks'])
    
    # Ensure we only keep valid track objects
    full_tracks = [t for t in full_tracks if t is not None]
    
    # Sort tracks by the 'popularity' field in descending order
    sorted_tracks = sorted(full_tracks, key=lambda x: x.get('popularity', 0), reverse=True)
    
    # Return the top max_tracks (if less than that are available, return all)
    return sorted_tracks[:max_tracks]
