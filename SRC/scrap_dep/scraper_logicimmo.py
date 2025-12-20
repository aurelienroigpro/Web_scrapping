import re
import time
import random
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ============================================================
# ⚙️ PARAMÈTRES
# ============================================================

INPUT_CSV = "DATA/departements.csv"
OUTPUT_CSV = "annonce.csv"

START_DEPARTEMENT_CODE = None
NB_DEPARTEMENTS_A_SCRAPER = None     # Mets None pour tout faire (après test)
NB_PAGES_PAR_DEPARTEMENT = 4      # Max pages à tenter (stop si page vide)

# Pauses (anti-blocage “soft”)
SLEEP_BETWEEN_PAGES = (4.1, 6.6)      # secondes
SLEEP_BETWEEN_DEPS = (10, 20)     # secondes


# ============================================================
# 🍪 Cookies (Usercentrics)
# ============================================================

def accept_cookies_if_present(driver, timeout=8):
    """
    Clique sur "Tout accepter" si la popup cookies est affichée.
    Ne fait rien si elle n'est pas présente.
    """
    try:
        wait = WebDriverWait(driver, timeout)

        # Bouton "Tout accepter"
        btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Tout accepter')]"))
        )
        btn.click()
        time.sleep(1.5)
        print("      ✅ Cookies acceptés")
    except Exception:
        # Pas de popup, ou déjà accepté
        pass


# ============================================================
# 🧠 Parsing ALT
# ============================================================

def parse_from_alt(alt: str) -> dict | None:
    """
    Retourne un dict si l'annonce correspond à nos types + prix + surface + adresse,
    sinon None.
    """

    # Type + sous-type
    if "Appartement à vendre" in alt:
        type_bien, sous_type = "Appartement", "Appartement"
    elif "Duplex à vendre" in alt:
        type_bien, sous_type = "Appartement", "Duplex"
    elif "Maison à vendre" in alt:
        type_bien, sous_type = "Maison", "Maison"
    elif "Pavillon à vendre" in alt:
        type_bien, sous_type = "Maison", "Pavillon"
    else:
        return None

    # Prix
    m_price = re.search(r"(\d[\d\s ]+)\s*€", alt)  # inclut l'espace fine insécable ( )
    # Surface (pas terrain)
    m_surface = re.search(r"(\d[\d\s,]+)\s*m²(?!\s*de terrain)", alt)
    # Pièces
    m_pieces = re.search(r"(\d+)\s+pièce", alt, flags=re.IGNORECASE)
    # Adresse ville + CP (gère Lyon 3ème 69003 / LYON 3EME, 69003)
    m_addr = re.findall(r"([A-ZÀ-Ý][A-Za-z0-9À-ÿ\-' ]+)\s*,?\s*\(?(\d{5})\)?", alt)

    if not (m_price and m_surface and m_addr):
        return None

    ville, cp = m_addr[-1]

    return {
        "prix": m_price.group(1).strip(),
        "surface": m_surface.group(1).strip(),
        "pieces": m_pieces.group(1) if m_pieces else None,
        "adresse": f"{ville.strip()} ({cp})",
        "type_bien": type_bien,
        "sous_type": sous_type,
    }


# ============================================================
# 🔗 URL pagination
# ============================================================

def build_page_url(base_url: str, page: int) -> str:
    if page == 1:
        return base_url

    m = re.search(r"(ad\d+\w+)$", base_url.lower())
    if not m:
        raise ValueError(f"Code AD introuvable dans l'URL : {base_url}")

    ad_code = m.group(1).upper()

    return (
        "https://www.logic-immo.com/classified-search"
        f"?distributionTypes=Buy&locations={ad_code}&page={page}&order=DateDesc"
    )


# ============================================================
# 🧭 Département (nom + code)
# ============================================================

def parse_dep(nom: str):
    m = re.search(r"\((\d+|2a|2b)\)", nom.lower())
    dep_code = m.group(1).upper() if m else None
    dep_nom = nom.replace("Immobilier", "").split("(")[0].strip()
    return dep_nom, dep_code


# ============================================================
# 🌍 Scraping d'un département
# ============================================================

def collect_ads_for_department(driver, base_url: str) -> list:
    ads = []
    cookies_checked = False

    for page in range(1, NB_PAGES_PAR_DEPARTEMENT + 1):
        url = build_page_url(base_url, page)
        print(f"  → Page {page} : {url}")

        driver.get(url)
        time.sleep(2.5)

        # On gère la popup cookies une seule fois au début du run (ou au besoin)
        if not cookies_checked:
            accept_cookies_if_present(driver)
            cookies_checked = True
            time.sleep(1.5)

        time.sleep(random.uniform(*SLEEP_BETWEEN_PAGES))

        soup = BeautifulSoup(driver.page_source, "html.parser")

        imgs = soup.find_all("img", alt=True)
        count_page = 0

        for img in imgs:
            data = parse_from_alt(img.get("alt", ""))
            if data:
                ads.append(data)
                count_page += 1

        print(f"      Annonces valides sur cette page : {count_page}")

        # Si une page ne retourne rien, on suppose fin de pagination / page bloquée
        if count_page == 0:
            break

    return ads


# ============================================================
# 🚀 MAIN
# ============================================================

def main():
    df = pd.read_csv(INPUT_CSV)
    df["dep_code"] = df["nom"].apply(lambda x: parse_dep(str(x))[1])

    # Reprise à partir d'un code
    if START_DEPARTEMENT_CODE:
        start_code = START_DEPARTEMENT_CODE.upper()
        if start_code not in df["dep_code"].values:
            raise ValueError(f"START_DEPARTEMENT_CODE='{START_DEPARTEMENT_CODE}' introuvable dans le CSV.")
        start_idx = df.index[df["dep_code"] == start_code][0]
        df = df.loc[start_idx:].reset_index(drop=True)
        print(f"Reprise à partir du département {start_code} (ligne CSV originale {start_idx}).\n")

    if NB_DEPARTEMENTS_A_SCRAPER is not None:
        df = df.head(NB_DEPARTEMENTS_A_SCRAPER)

    print("Départements à scraper :", len(df))

    # Firefox (non-headless)
    options = webdriver.FirefoxOptions()
    # options.add_argument("--headless")  # laisse commenté

    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()),
        options=options
    )

    all_ads = []

    for idx, row in df.iterrows():
        dep_nom, dep_code = parse_dep(row["nom"])
        print(f"\n=== [{idx+1}/{len(df)}] Département {dep_code} – {dep_nom} ===")
        print("URL de base :", row["url"])

        ads = collect_ads_for_department(driver, row["url"])
        print(f"  → Total annonces valides pour ce département : {len(ads)}")

        for ad in ads:
            ad["departement_nom"] = dep_nom
            ad["departement_code"] = dep_code
            all_ads.append(ad)

        time.sleep(random.uniform(*SLEEP_BETWEEN_DEPS))

    driver.quit()
    print("\nNavigateur fermé.")

    df_final = pd.DataFrame(all_ads)
    print("\nTotal annonces récoltées :", len(df_final))

    df_final.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print("CSV final créé →", OUTPUT_CSV)


if __name__ == "__main__":
    main()
