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
                        return lyrics
        return "Lyrics not in English"
    except Exception as e:
        print(f"Error retrieving lyrics for {title} by {artist}: {e}")
        return "Lyrics not found"

def get_all_tracks_for_artist(artist_id, sp):
    tracks = []
    albums = sp.artist_albums(artist_id, album_type="album,single", country="US", limit=50)
    album_ids = list({album['id'] for album in albums['items']})  # Unique albums only

    for album_id in album_ids:
        album_tracks = sp.album_tracks(album_id)['items']
        for track in album_tracks:
            tracks.append(track)

    return tracks