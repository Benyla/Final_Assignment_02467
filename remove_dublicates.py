import pandas as pd

df_tracks = pd.read_csv("DATA/spotify_genius_data.csv")
df_deduplicated = df_tracks.drop_duplicates(subset='spotify_id', keep='first')
df_deduplicated.to_csv("DATA/spotify_genius_data_noduplicates.csv", index=False)