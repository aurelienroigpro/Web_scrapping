import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from pathlib import Path

# =========================
# Chargement des données
# =========================

# Chemin du fichier courant (4_Carte.py)
BASE_DIR = Path(__file__).resolve().parents[2]

# Chemin vers DATA/annonces_carte.csv
DATA_PATH = BASE_DIR / "DATA" / "annonces_carte.csv"

# Chargement
source = pd.read_csv(DATA_PATH)

st.title("Annonces immobilières de France")

# Carte centrée sur la France
carte = folium.Map(
    location=[46.603354, 1.888334],
    zoom_start=6,
    tiles="OpenStreetMap"
)

# Groupement par coordonnées
grouped = source.groupby(["latitude", "longitude"])

for (lat, lon), group in grouped:

    popup_html = """
    <div style="
        max-height: 200px;
        width: 260px;
        overflow-y: auto;
        font-size: 13px;
    ">
    """

    for _, row in group.iterrows():
        popup_html += (
            f"<b>{row['type_bien']}</b><br>"
            f"Prix : {row['prix']} €<br>"
            f"Surface : {row['surface']} m²<br>"
            f"Pièces : {row['pieces']}<br>"
            f"Ville : {row['ville']}<br>"
            f"<hr style='margin:6px 0;'>"
        )

    popup_html += "</div>"

    folium.CircleMarker(
    location=[lat, lon],
    radius=6,
    color="blue",
    fill=True,
    fill_color="blue",
    fill_opacity=0.7,
    tooltip=f"{len(group)} annonces",
    popup=folium.Popup(popup_html, max_width=300)
).add_to(carte)



st_folium(carte, width=900, height=900)
