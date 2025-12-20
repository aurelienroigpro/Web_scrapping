import time
import random
from playwright.sync_api import sync_playwright
import pandas as pd

# Cette version va simuler un comportement humain, pour éviter l'apparition de captcha
# Ne fonctionne que si la connexion internet passe par un téléphone mobile. 
# En fixe, je suis bloqué par DataDome, le protecteur (firewall?) du site.

# Collecte les url à la suite de "liste_adresse.csv", récupére le html des pages d'annonces. Le copie dans un fichier .txt.
# C'est la copie de : tscrap4.4.py



def lire_adresses():
    fichier = pd.read_csv("liste_adresse.csv")
    adresses = fichier.iloc[:, 1].tolist()
    return adresses


def pause_humaine(min_s=1.2, max_s=3.5):
    """Pause aléatoire pour simuler un comportement humain."""
    time.sleep(random.uniform(min_s, max_s))


def mouvements_souris_humains(page):
    """Déplace la souris aléatoirement pour simuler une activité humaine."""
    for _ in range(random.randint(2, 5)):
        x = random.randint(50, 900)
        y = random.randint(50, 600)
        page.mouse.move(x, y, steps=random.randint(5, 20))
        time.sleep(random.uniform(0.1, 0.3))


def scroll_humain(page):
    """Scroll doux et aléatoire comme un humain."""
    for _ in range(random.randint(2, 6)):
        page.mouse.wheel(0, random.randint(200, 500))
        time.sleep(random.uniform(0.3, 0.8))


def scrap_logic_immo():

    adresses = lire_adresses()

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()

        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/123 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9"
        })

        for i, adresse in enumerate(adresses[:4], start=29):

            print(f"\n➡️ Scraping {i} /32 : {adresse}")

            pause_humaine(1.5, 4)      # pause avant de changer de page

            # Charger la page
            page.goto(adresse, wait_until="networkidle")

            pause_humaine(2, 4)

            # Mouvements humains
            mouvements_souris_humains(page)
            scroll_humain(page)

            # Attendre que le DOM soit bien rendu
            page.wait_for_selector("body")

            # Attendre un peu (l'humain lit)
            pause_humaine(3, 7)

            # Récupération du HTML
            html = page.content()

            # Sauvegarde dans un fichier
            filename = f"page_logic_immo_{i}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"✔️ Page enregistrée : {filename}")

        browser.close()
        print("\n🎉 Scraping terminé sans provoquer de captcha !")


# EXÉCUTION
scrap_logic_immo()
