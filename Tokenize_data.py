import pandas as pd
import spacy
import nltk
from nltk.corpus import stopwords
import os

# Paths
raw_csv = "DATA/spotify_genius_data.csv"                 
out_csv = "DATA/tokenized_data.csv"   

# download / load stopwords
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
nlp = spacy.load("en_core_web_sm", disable=["parser","ner"])

# Preprocessing function
def preprocess(text):
    doc = nlp(str(text).lower())
    return [
        tok.lemma_ for tok in doc
        if tok.is_alpha and tok.lemma_ not in stop_words
    ]

# read raw data
df = pd.read_csv(raw_csv)

# tokenize lyrics
df["tokens_no_stop"] = df["lyrics"].apply(preprocess)

# dataframe
tokenized_data = (
    df[["spotify_id", "tokens_no_stop"]]
      .rename(columns={"spotify_id": "song_id"})
)

tokenized_data.to_csv(out_csv, index=False)
print(f"Saved {len(tokenized_data)} rows of tokenized data to {out_csv}")
