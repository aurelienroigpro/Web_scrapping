import csv
import time
import random
import os
from playwright.sync_api import sync_playwright
from playwright.sync_api import expect
import pandas as pd
from pathlib import Path


# Chemin du fichier ou aller récupérer les codes postaux:
BASE_DIR = Path(__file__).resolve().parents[2]  # webscrap/
DATA_PATH = BASE_DIR / "DATA" / "1-villes_france.csv"

# Chemin ou enregister les url:
DATA_PATH2 = BASE_DIR / "DATA" / "2-liste_url.csv"

df = pd.read_csv(DATA_PATH)



    # ---- Fonctions utilitaires ----
    # ---- Correspond à adresse_crawler 7.1.py
    
def human_sleep(base=1.0, variance=0.5):
        """Pause aléatoire pour simuler un comportement humain."""
        t = base + random.uniform(0, variance)
        time.sleep(t)

def accepter_cookies(page, timeout=5):
        """Tente de cliquer sur un bouton 'Tout accepter' dans tous les frames."""
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                for frame in page.frames:
                    btn = frame.locator("button:has-text('Tout accepter')")
                    if btn.count() > 0:
                        btn.first.click()
                        print("➡️ Cookies acceptés")
                        human_sleep(0.5, 0.2)
                        return True
            except Exception:
                pass
            time.sleep(0.2)  # petite pause avant de réessayer
        return False



def nouvelle_recherche(page):
        """
        Vérifie si le site affiche la fenêtre 'Voulez-vous reprendre la recherche précédente ?'
        et clique sur le bouton 'Nouvelle recherche' si présent.
        """
        try:
            # On recherche le bouton "Nouvelle recherche" dans la page et les frames
            for frame in page.frames:
                btn = frame.locator("button:has-text('Nouvelle recherche')")
                if btn.count() > 0:
                    btn.first.click()
                    print("➡️ Fenêtre 'reprendre la recherche' détectée et 'Nouvelle recherche' cliquée")
                    # Petite pause pour laisser le site réagir
                    time.sleep(1)
                    return True
        except Exception:
            pass
        return False



def lire_codes_postaux(fichier_csv, start=0, limite=None):
    codes_postaux = []
    with open(fichier_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for i, row in enumerate(reader):

            # ―― Sauter les lignes avant "start" ――
            if i < start:
                continue

            # ―― Si limite activée : stopper ――
            if limite is not None and (i - start) >= limite:
                break

            # ―― Lecture du code postal ――
            code_postal = row.get("Code postal", "").strip()
            if code_postal:
                codes_postaux.append(code_postal)

    return codes_postaux


    # ---- Récupération de l'URL Logic-Immo pour un code postal ----
def get_logic_immo_url(page, code_postal):
        print(f"\n🔍 Traitement du code postal : {code_postal}")

        # Aller à l'accueil
        page.goto("https://www.logic-immo.com/", wait_until="networkidle")
        accepter_cookies(page)
        nouvelle_recherche(page) 
        human_sleep(0.6,0.3)

        # Trouver le champ de recherche
        selectors = [
            "input[name='searchValue']",
            "input[placeholder*='Ville']",
            "input[placeholder*='code postal']",
            "input[placeholder*='département']"
        ]

        search_field = None
        for _ in range(4):          # Nombre de fois ou on va chercher le champ de recherche
            accepter_cookies(page)
            nouvelle_recherche(page) 
            for sel in selectors:
                field = page.query_selector(sel)
                if field:
                    search_field = field
                    break
            if search_field:
                break
            human_sleep(0.5, 0.2)

        if not search_field:
            print("❌ Champ de recherche introuvable.")
            return None

    # Simuler un humain : délais aléatoires entre les actions
        human_sleep(1, 0.1)
        try:
            search_field.fill("")  # vider
            search_field.fill(code_postal)
            human_sleep(0.6, 0.3)

            # Forcer le déclenchement de l'auto-suggest
            search_field.click()
            search_field.press("ArrowDown")  # ou "Enter"
            search_field.press("ArrowUp")
        except Exception as e:
            print("⚠️ Erreur lors du fill :", e)
            return None

        human_sleep(0.3, 0.1)


    # Cliquer sur la première suggestion
        try:
            first_suggest = page.locator("ul[role='listbox'] li").first
            accepter_cookies(page)
            nouvelle_recherche(page) 
            first_suggest.click()
            print("✔️ Suggestion cliquée.")
        except Exception as e:
            print("⚠️ Impossible de cliquer sur la suggestion.", e)
            return None

    # Attendre l'apparition des annonces
    

        try:
            #with page.expect_navigation():
            print("démarre la page")
            first_suggest.click(timeout=3000)
            print("prépare le timesleep")
            time.sleep(1)
            print("fin du timesleep")
        except Exception as e:
            print("⚠️ Problème lors du clic sur la suggestion :", e)

        # Copier l'url de la page des annonces
        url = page.url
        print(f"➡️ URL trouvée : {url}")
        return url

# ---- Boucle principale ----
def main():
    # Ajuste la limite si nécessaire (None = tout lire)
    # villes_france.csv contient la liste des 100 plus grandes villes de france par population.





    codes = lire_codes_postaux(DATA_PATH)
    if not codes:
        print("❌ Aucun code postal trouvé.")
        return
# "C:\Users\HP USER\Documents\Sorbonne_Data\5__Pyth_av_webscrap\Cours_de_webscrap - VS Code\Web_scrapping\SRC\par_villle\1-recup_url.py"
# "C:\Users\HP USER\Documents\Sorbonne_Data\5__Pyth_av_webscrap\Cours_de_webscrap - VS Code\Web_scrapping\SRC\par_villle\data_ville\2-liste_url.csv"
    OUTPUT_FILE = DATA_PATH2  # nom exact demandé

    # Assure le dossier courant (optionnel)
    # os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=30)
        page = browser.new_page()

        # Ouvrir le fichier en mode ajout
        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # écrire l'entête si le fichier est vide
            f.seek(0, 2)
            if f.tell() == 0:
                writer.writerow(["code_postal", "url_or_error"])
                f.flush()
                os.fsync(f.fileno())

            # Boucle sur les codes (limités par la variable codes)
            for code_postal in codes:
                try:
                    url = get_logic_immo_url(page, code_postal)
                except Exception as exc:
                    # Capturer toute exception inattendue pour enregistrer l'erreur et continuer
                    url = None
                    print(f"❌ Exception durant le traitement de {code_postal}: {exc}")

                # Toujours écrire une ligne, même si url est None
                if url:
                    writer.writerow([code_postal, url])
                else:
                    writer.writerow([code_postal, "ERROR_OR_NO_RESULT"])
                # Forcer l'écriture sur le disque immédiatement
                f.flush()
                os.fsync(f.fileno())

                # Pause humaine entre les recherches
                human_sleep(2.5, 3.0)

        browser.close()

if __name__ == "__main__":
    main()
