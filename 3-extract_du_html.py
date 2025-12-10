# Code de récupération des infos et création du .csv:
# Ici, on va utiliser en plus une boucle for pour lire tous les 
# txt à la suite et remplir le csv avec.
# Tout sera stocké dans le fichier annonces-8.csv (sauf les 3 premières
# villes qui sont dans annonces-7).

# C'est la copie du code: extraction.3.3.py

from bs4 import BeautifulSoup
import csv
import os


for j in range (1,33):

    adresse_fichier= f"page_logic_immo_{j}.txt"
    # --- 1. Charger le fichier HTML ---
    try:
        with open(adresse_fichier, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "lxml")
    except FileNotFoundError:
        print (f"Manque le fichier page_logic_immo_{j}")
        continue

    # --- 2. Trouver toutes les annonces ---
    annonces = soup.find_all("div", {"data-testid": lambda x: x and "classified-card" in x})

    # --- 3. Préparer le fichier CSV ---
    csv_exists = os.path.exists("annonces-9.csv")


    with open("annonces-9.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # ecrire l'en tête seulement si le fichier n'existe pas
        if not csv_exists:
            writer.writerow([
                "type_bien",
                "prix",
                "pieces",
                "chambres",
                "surface",
                "etage",
                "adresse",
                "description",
                "agence"
            ])

        # --- 4. Extraire les infos pour chaque annonce ---
        for ann in annonces:

            # Prix
            prix = ann.select_one('div[data-testid="cardmfe-price-testid"]')
            prix = prix.get_text(strip=True) if prix else None

            # Type de bien
            type_bien = ann.select_one("div.css-1e55dlz")
            type_bien = type_bien.get_text(strip=True) if type_bien else None

            # Caractéristiques
            keyfacts = ann.select_one('div[data-testid="cardmfe-keyfacts-testid"]')
            pieces = chambres = surface = etage = None
            
            if keyfacts:
                facts = [x.get_text(strip=True) for x in keyfacts.find_all("div", class_="css-9u48bm")]
                facts = [f for f in facts if f != "·"]

                for f in facts:
                    if "pièce" in f:
                        pieces = f.replace("pièces", "").replace("pièce", "").strip()
                    elif "chambre" in f:
                        chambres = f.replace("chambres", "").replace("chambre", "").strip()
                    elif "m²" in f:
                        surface = f.replace("m²", "").strip()
                    elif "Étage" in f:
                        etage = f.replace("Étage", "").strip()

            # Adresse
            adresse = ann.select_one('div[data-testid="cardmfe-description-box-address"]')
            adresse = adresse.get_text(strip=True) if adresse else None

            # DESCRIPTION
            description = ann.select_one("div.css-oorffy")
            description = description.get_text(strip=True) if description else None

            # --- 🆕 RÉCUPÉRATION DU NOM DE L’AGENCE ---
            agency = None
            imgs = ann.find_all("img")

            for img in imgs:
                alt = img.get("alt", "").strip()
                if not alt:
                    continue

                # On élimine les alt contenant une description du bien
                if any(x in alt for x in ["€", "m²", "pièce", "chambre", "Paris", "sur"]):
                    continue

                # Si l'alt ne ressemble pas à une description : c'est le nom de l'agence
                agency = alt
                break

            # --- 5. Écrire dans le CSV ---
            writer.writerow([
                type_bien,
                prix,
                pieces,
                chambres,
                surface,
                etage,
                adresse,
                description,
                agency
            ])



    if os.path.exists(adresse_fichier):
        #os.remove("page_logic_immo3.1.txt")
        print("Fichier HTML supprimé.")
    else:
        print("Fichier HTML introuvable (déjà supprimé ?).")