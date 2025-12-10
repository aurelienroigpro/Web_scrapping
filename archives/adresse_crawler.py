from playwright.sync_api import sync_playwright
import csv
import time

def get_logic_immo_url():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # mettre True pour ne pas afficher le navigateur
        page = browser.new_page()

          # 1. Aller sur la page d’accueil
        page.goto("https://www.logic-immo.com/", wait_until="networkidle")

           # --- 1bis. Accepter les cookies (même si c'est dans une iframe) ---
        time.sleep(10)  # petite pause pour que le popup s'affiche
        try:
            # parcourir toutes les iframes pour trouver le bouton
            for frame in page.frames:
                cookie_btn = frame.locator("button:has-text('Tout accepter')")
                if cookie_btn.count() > 0:
                    cookie_btn.first.click()
                    print("Cookies acceptés automatiquement.")
                    time.sleep(10)
                    break
        except Exception:
            print("Aucune bannière cookies détectée ou click échoué.")



        # 2. Attendre la barre de recherche
        page.wait_for_selector("input[name='searchValue']")

        # 3. Taper le code postal
        page.fill("input[name='searchValue']", "76000")

        # 4. Simuler la touche Entrée
        page.keyboard.press("Enter")

        # 5. Attendre que la navigation se fasse
        page.wait_for_load_state("networkidle")
        time.sleep(2)  # laisse le temps au site de rediriger complètement

        # 6. Récupérer l’URL des résultats
        final_url = page.url
        print("URL récupérée :", final_url)

        # 7. Enregistrer dans un CSV
        with open("liste_adresses.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url"])
            writer.writerow([final_url])

        browser.close()

# ---- Exécution ----
get_logic_immo_url()
