from playwright.sync_api import sync_playwright
import pandas as pd
import time
import random

def lire_adresses():
    fichier = pd.read_csv("liste_adresse.csv")
    return fichier.iloc[:,1].tolist()  # 2e colonne

def scrap_logic_immo(adresses):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        for adresse in adresses[:3]:
            page = browser.new_page()
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 ..."
            })

            page.goto(adresse, wait_until="networkidle")
            page.wait_for_selector("body")

            html = page.content()
            nom_fichier = f"page_{adresses.index(adresse)}.txt"
            with open(nom_fichier, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"HTML enregistré pour {adresse}")
            page.close()
            time.sleep(random.uniform(2, 5))  # pause aléatoire

        browser.close()

adresses = lire_adresses()
scrap_logic_immo(adresses)
