import re
from langdetect import detect
import lyricsgenius

def is_english(text):
    try:
        return detect(text) == 'en'
    except:
        return False
    
def get_english_lyrics(title, artist, genius):
    try:
        song = genius.search_song(title, artist)
        if song:
            lyrics = clean_lyrics(song.lyrics)
            if is_english(lyrics):
                return lyrics
            else:
                # Retry with 'English' in title
                print(f"Non-English lyrics for {title} by {artist}, retrying with 'English' hint...")
                song = genius.search_song(f"{title} English", artist)
                if song:
                    lyrics = clean_lyrics(song.lyrics)
                    if is_english(lyrics):
                        return lyrics
        return "Lyrics not in English"
    except Exception as e:
        print(f"Error retrieving lyrics for {title} by {artist}: {e}")
        return "Lyrics not found"

def clean_lyrics(raw_lyrics):
    raw_lyrics = raw_lyrics.split("Lyrics", 1)[-1]
    raw_lyrics = re.sub(r"^[^\n]*Contributors[^\n]*\n", "", raw_lyrics, flags=re.MULTILINE)
    raw_lyrics = re.sub(r"\[.*?\]", "", raw_lyrics)
    raw_lyrics = re.sub(r"\n{2,}", "\n", raw_lyrics)
    raw_lyrics = raw_lyrics.replace('\n', ' ')
    raw_lyrics = raw_lyrics.replace("\\", "") 
    return raw_lyrics.strip() 