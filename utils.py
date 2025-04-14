import re

def clean_lyrics(raw_lyrics):
    # Remove translation and contributor header lines
    raw_lyrics = raw_lyrics.split("Lyrics", 1)[-1]  # Remove everything before first "Lyrics"
    
    # Remove translation & contributor block at the top
    raw_lyrics = re.sub(r"^[^\n]*Contributors[^\n]*\n", "", raw_lyrics, flags=re.MULTILINE)

        # Remove section headers like [Intro], [Chorus], etc.
    raw_lyrics = re.sub(r"\[.*?\]", "", raw_lyrics)

    # Collapse multiple newlines into one
    raw_lyrics = re.sub(r"\n{2,}", "\n", raw_lyrics)

    raw_lyrics = raw_lyrics.replace('\n', ' ')
    raw_lyrics = raw_lyrics.replace("\\", "") 
    
    return raw_lyrics.strip()  # Remove leading/trailing whitespace