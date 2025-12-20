import pandas as pd
from geopy.geocoders import Nominatim
from time import sleep
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# DATA_PATH = BASE_DIR / "data" / "données.csv"


# 1. Chargement des annonces brutes
df = pd.read_csv(BASE_DIR / "application"/"data" / "df_analyseVF4.csv")

# 2. Initialisation du géocodeur
geolocator = Nominatim(user_agent="Student-SDA-2025")

# 3. Nom du fichier CSV final
csv_sortie = BASE_DIR / "DATA" / "annonces_carte.csv"

# --------------------------------------------------
# 📁 Initialisation du CSV + cache des coordonnées
# --------------------------------------------------

if os.path.exists(csv_sortie):
    df_cache = pd.read_csv(csv_sortie)

    # Cache : code_postal -> (lat, lon)
    cache_cp = {
        str(row["code_postal"]): (row["latitude"], row["longitude"])
        for _, row in df_cache.dropna(subset=["code_postal", "latitude", "longitude"]).iterrows()
    }
else:
    pd.DataFrame(columns=[
        "latitude", "longitude", "prix", "surface",
        "pieces", "type_bien", "code_postal",
        "departement", "ville"
    ]).to_csv(csv_sortie, index=False)

    cache_cp = {}

print(f"🧠 {len(cache_cp)} codes postaux déjà en cache")

# --------------------------------------------------
# 🔎 PRÉLECTURE : villes avec > 20 annonces
# --------------------------------------------------

villes_valides = (
    df["Ville"]
    .value_counts()
    .loc[lambda x: x > 20]
    .index
)

df_filtre = df[df["Ville"].isin(villes_valides)].copy()

print(f"📊 {len(villes_valides)} villes retenues")
print(f"📦 {len(df_filtre)} annonces à traiter")

# --------------------------------------------------
# 4. Boucle de géocodage optimisée
# --------------------------------------------------

for i, row in df_filtre.iterrows():
    departement = row["departement_code"]
    ville = row["Ville"]
    code_postal = str(row["Code_postal"])

    # -----------------------
    # ✅ Vérification du cache
    # -----------------------
    if code_postal in cache_cp:
        latitude, longitude = cache_cp[code_postal]

    else:
        try:
            adresse_complete = f"{code_postal}, {departement}, France"
            location = geolocator.geocode(adresse_complete)

            if location:
                latitude = location.latitude
                longitude = location.longitude

                # Ajout au cache
                cache_cp[code_postal] = (latitude, longitude)
            else:
                latitude = None
                longitude = None

            sleep(1.2)  # Nominatim : 1 req / seconde

        except Exception as e:
            print(f"❌ Erreur géocodage CP {code_postal} : {e}")
            continue

    # -----------------------
    # 📄 Ligne finale
    # -----------------------
    ligne = {
        "latitude": latitude,
        "longitude": longitude,
        "prix": row["prix"],
        "surface": row["surface"],
        "pieces": row["pieces"],
        "type_bien":  row["type_bien"],
        "code_postal": code_postal,
        "departement": departement,
        "ville": ville
    }

    pd.DataFrame([ligne]).to_csv(
        csv_sortie,
        mode="a",
        header=False,
        index=False
    )

print("✅ annonces_carte.csv créé et enrichi avec cache géographique")
