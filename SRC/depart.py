import re
import os
import pandas as pd

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

# ==========================
# PARAMÈTRES GLOBAUX
# ==========================

# Fichier CSV d'entrée contenant la liste des URLs Logic-Immo
# (une ligne par département)
INPUT_URLS_CSV = "DATA/departements.csv"

# Fichier CSV de sortie avec toutes les annonces
OUTPUT_CSV = "annonces_france.csv"

# Nombre de pages à scraper par URL
NB_PAGES = 3



def parse_segment(segment: str) -> dict:
    """Prend un bloc de texte (une 'annonce') et extrait type de bien / prix / surface / pièces / adresse."""

    # Type de bien (très simple : on cherche 'Maison' quelque part)
    if "Maison" in segment or "maison" in segment:
        type_bien = "Maison"
    else:
        type_bien = "Appartement"

    # Prix : premier nombre suivi de €
    m_price = re.search(r"(\d[\d\s]+)\s*€", segment)
    prix = m_price.group(1).strip() if m_price else None

    # Surface : nombre + m² (avec éventuellement des espaces / virgules)
    m_surface = re.search(r"(\d[\d\s,]+)\s*m²", segment)
    surface = m_surface.group(1).strip() if m_surface else None

    # Pièces : 'X pièce(s)'
    m_pieces = re.search(r"(\d+)\s+pièce", segment, flags=re.IGNORECASE)
    pieces = m_pieces.group(1) if m_pieces else None

    # Adresse : une ligne avec un code postal entre parenthèses
    adresse = None
    for line in segment.splitlines():
        line = line.strip()
        if "(" in line and ")" in line and any(ch.isdigit() for ch in line):
            adresse = line
            break

    return {
        "type_bien": type_bien,
        "prix": prix,
        "surface": surface,
        "pieces": pieces,
        "adresse": adresse,
    }


def collect_segments_for_url(driver, base_url: str, nb_pages: int = 3) -> list:
    """
    Pour une URL de recherche Logic-Immo, récupère une liste de segments texte,
    chacun correspondant à une annonce (sur plusieurs pages).
    """
    annonces_text = []

    for page in range(1, nb_pages + 1):
        # Construction de l'URL de la page
        if page == 1:
            page_url = base_url
        else:
            sep = "&" if "?" in base_url else "?"
            page_url = f"{base_url}{sep}page={page}"

        print(f"\n  → Page {page} : {page_url}")
        driver.get(page_url)
        print("    Titre de la page :", driver.title)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        full_text = soup.get_text("\n", strip=True)

        # Normalisation pour capter maisons + apparts + quelques variantes
        normalized = full_text
        normalized = normalized.replace("Maison de ville à vendre", "Maison à vendre")
        normalized = normalized.replace("Appartement à vendre - neuf", "Appartement à vendre")
        normalized = normalized.replace("Duplex à vendre", "Appartement à vendre")

        # On remplace "Maison à vendre" par "Appartement à vendre" pour tout traiter pareil
        normalized = normalized.replace("Maison à vendre", "Appartement à vendre")

        parts = normalized.split("Appartement à vendre")
        print(f"    Nombre de morceaux après split = {len(parts)}")

        for part in parts[1:]:  # on saute l'en-tête
            seg = "Appartement à vendre " + part

            # On garde seulement si ça ressemble à une annonce
            if "€" in seg and "m²" in seg:
                annonces_text.append(seg)

    return annonces_text


def parse_departement_info(nom: str) -> tuple:
    """
    À partir de la colonne 'nom', extrait :
      - departement_nom : ex. 'Ain'
      - departement_code : ex. '01'
    'Immobilier Ain (01)' -> ('Ain', '01')
    """
    # Code département dans les parenthèses
    m = re.search(r"\((\d{2,3})\)", nom)
    code = m.group(1) if m else None

    # Nom du département = ce qu'il y a entre 'Immobilier ' et ' (code)'
    dep_nom = nom
    if nom.lower().startswith("immobilier "):
        dep_nom = nom[len("Immobilier "):]
    if "(" in dep_nom:
        dep_nom = dep_nom.split("(")[0].strip()

    return dep_nom, code


def main():
    # ==========================
    # 1) Lecture des URLs
    # ==========================
    if not os.path.exists(INPUT_URLS_CSV):
        print(f"⚠️ Fichier {INPUT_URLS_CSV} introuvable.")
        return

    urls_df = pd.read_csv(INPUT_URLS_CSV)
    print(f"Nombre de lignes (départements) dans {INPUT_URLS_CSV} :", len(urls_df))

    # On s'attend à avoir au minimum les colonnes : 'nom', 'url'
    required_cols = ["nom", "url"]
    for col in required_cols:
        if col not in urls_df.columns:
            print(f"⚠️ Colonne '{col}' manquante dans {INPUT_URLS_CSV}.")
            return

    # ==========================
    # 2) Initialisation Selenium
    # ==========================
    print("\nInitialisation de Firefox...")
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")

    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()),
        options=options,
    )

    all_annonces = []

    try:
        # ==========================
        # 3) Boucle sur chaque ligne (département)
        # ==========================
        for idx, row in urls_df.iterrows():

            base_url = str(row["url"])
            nom_dep = str(row["nom"])

            departement_nom, departement_code = parse_departement_info(nom_dep)

            print(f"\n=== [{idx+1}/{len(urls_df)}] Département {departement_code} – {departement_nom} ===")
            print(f"Nom brut : {nom_dep}")
            print(f"URL de recherche : {base_url}")

            segments = collect_segments_for_url(driver, base_url, NB_PAGES)
            print(f"  → Segments trouvés pour {departement_nom} : {len(segments)}")

            # On parse chaque segment texte en dict de données
            for seg in segments:
                data = parse_segment(seg)
                if data["prix"] is not None and data["surface"] is not None:
                    data["departement_nom"] = departement_nom
                    data["departement_code"] = departement_code
                    all_annonces.append(data)

    finally:
        driver.quit()
        print("\nNavigateur fermé.")

    # ==========================
    # 4) Création du DataFrame + export
    # ==========================
    print("\nTotal d'annonces valides :", len(all_annonces))
    if not all_annonces:
        print("⚠️ Aucune annonce valide trouvée, rien à exporter.")
        return

    df_out = pd.DataFrame(all_annonces)
    print("\nAperçu du DataFrame final :")
    print(df_out.head())

    df_out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"\n✅ CSV final créé : {OUTPUT_CSV}")


if __name__ == "__main__":
    main()