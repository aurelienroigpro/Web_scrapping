import re
import time
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager


# ============================================================
# ⚙️ PARAMÈTRES GLOBAUX
# ============================================================

INPUT_CSV = "DATA/departements.csv"          # ton CSV (nom,url)
OUTPUT_CSV = "annonces_france_finalVVFF.csv"   # fichier de sortie

# Combien de départements à scraper ?
#  - 5 pour tester
#  - None pour tous
NB_DEPARTEMENTS_A_SCRAPER = None


# ============================================================
# 1) Parsing d'une annonce à partir de l'attribut ALT
# ============================================================

def parse_from_alt(alt: str) -> dict:
    """
    Extrait prix, surface, pièces, adresse, type de bien à partir du texte ALT
    d'une image d'annonce Logic-Immo.
    """

    # Type de bien
    if "Appartement à vendre" in alt:
        type_bien = "Appartement"
    elif "Maison à vendre" in alt:
        type_bien = "Maison"
    else:
        type_bien = None

    # Prix : premier nombre + €
    m_price = re.search(r"(\d[\d\s]+)\s*€", alt)
    prix = m_price.group(1).strip() if m_price else None

    # Pièces : "X pièce(s)"
    m_pieces = re.search(r"(\d+)\s+pièce", alt, flags=re.IGNORECASE)
    pieces = m_pieces.group(1) if m_pieces else None

    # Surface : on prend un "m²" qui n'est PAS suivi de "de terrain"
    m_surface = re.search(r"(\d[\d\s,]+)\s*m²(?!\s*de terrain)", alt)
    surface = m_surface.group(1).strip() if m_surface else None

    # ------------------------------------------
    # Adresse : ville + code postal
    # ex : "Savigny sur Orge (91600)" ou "Savigny sur Orge 91600"
    # On prend la DERNIÈRE occurrence dans le ALT.
    # ------------------------------------------
    m_addr = re.findall(
        r"([A-ZÀ-Ý][A-Za-zÀ-ÿ\-' ]+)\s*\(?(\d{5})\)?",
        alt
    )
    if m_addr:
        ville, cp = m_addr[-1]
        adresse = f"{ville.strip()} ({cp})"
    else:
        adresse = None

    return {
        "prix": prix,
        "surface": surface,
        "pieces": pieces,
        "adresse": adresse,
        "type_bien": type_bien,
    }


# ============================================================
# 2) Construire l'URL des pages 1, 2, 3
# ============================================================

def build_page_url(base_url: str, page: int) -> str:
    """
    Page 1 : URL de ton CSV (recherche-immo/...)
    Pages 2+ : /classified-search?...&locations=ADXXXXX&page=N&...
    """

    if page == 1:
        return base_url

    # Extraire le code adxxxfyy à la fin de l'URL
    m = re.search(r"(ad\d+\w+)$", base_url.lower())
    if not m:
        raise ValueError(f"Impossible d'extraire le code ADxxxxx depuis l'URL : {base_url}")

    ad_code = m.group(1).upper()  # ex: AD06FR1

    return (
        "https://www.logic-immo.com/classified-search"
        f"?distributionTypes=Buy&locations={ad_code}&page={page}&order=DateDesc"
    )


# ============================================================
# 3) Scraper 3 pages pour un département
# ============================================================

def collect_ads_for_department(driver, base_url: str, nb_pages: int = 3) -> list:
    all_ads = []

    for page in range(1, nb_pages + 1):
        page_url = build_page_url(base_url, page)
        print(f"  → Page {page} : {page_url}")

        driver.get(page_url)
        time.sleep(1.2)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Toutes les images avec un ALT
        imgs = soup.find_all("img", alt=True)

        count_page_ads = 0

        for img in imgs:
            alt = img["alt"]

            # On garde seulement les Appartements / Maisons à vendre
            if "Appartement à vendre" not in alt and "Maison à vendre" not in alt:
                continue

            data = parse_from_alt(alt)

            # On garde si au moins prix + surface
            if data["prix"] and data["surface"]:
                all_ads.append(data)
                count_page_ads += 1

        print(f"      Annonces valides sur cette page : {count_page_ads}")

    return all_ads


# ============================================================
# 4) Extraire nom + code du département
# ============================================================

def parse_dep(nom: str):
    """
    'Immobilier Ain (01)' → ('Ain', '01')
    """
    m = re.search(r"\((\d+|2a|2b)\)", nom.lower())
    dep_code = m.group(1).upper() if m else None
    dep_nom = nom.replace("Immobilier", "").split("(")[0].strip()
    return dep_nom, dep_code


# ============================================================
# 5) Programme principal
# ============================================================

def main():
    df_urls = pd.read_csv(INPUT_CSV)
    print("Nombre total de départements dans le CSV :", len(df_urls))

    if NB_DEPARTEMENTS_A_SCRAPER is not None:
        df_urls = df_urls.head(NB_DEPARTEMENTS_A_SCRAPER)
        print("On ne garde que les", len(df_urls), "premiers départements pour ce test.\n")
    else:
        print("On va scraper tous les départements.\n")

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")

    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()),
        options=options,
    )

    all_ads = []

    for idx, row in df_urls.iterrows():
        base_url = row["url"]
        nom_dep_raw = row["nom"]
        dep_nom, dep_code = parse_dep(nom_dep_raw)

        print(f"\n=== [{idx+1}/{len(df_urls)}] Département {dep_code} – {dep_nom} ===")
        print("URL de base :", base_url)

        ads = collect_ads_for_department(driver, base_url, nb_pages=3)
        print(f"  → Total annonces valides pour ce département : {len(ads)}")

        for ad in ads:
            ad["departement_nom"] = dep_nom
            ad["departement_code"] = dep_code
            all_ads.append(ad)

    driver.quit()
    print("\nNavigateur fermé.")

    df_final = pd.DataFrame(all_ads)

    print("\nAperçu du DataFrame :")
    print(df_final.head())
    print("\nTotal d'annonces récoltées :", len(df_final))

    df_final.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print("\nCSV final créé →", OUTPUT_CSV)


if __name__ == "__main__":
    main()