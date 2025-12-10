from playwright.sync_api import sync_playwright

def scrap_logic_immo():
    with sync_playwright() as p:
        # 👉 Mode headless = aucune fenêtre ne s’ouvre. Il faut que la fenêtre s'ouvre pour que oooooooooooooooooooo
        # o
        # ole code fonctionne.uj+
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
        })


        url = "https://www.logic-immo.com/classified-search?distributionTypes=Buy,Buy_Auction,Compulsory_Auction&estateTypes=House,Apartment&locations=AD08FR31096&order=Default&m=homepage_new_search_classified_search_result"
        
        # Charge la page et exécute le JS
        page.goto(url, wait_until="networkidle")

        # On attend qu'un élément soit chargé (sécurise le rendu du JS)
        page.wait_for_selector("body")

        # 👉 Récupère tout le HTML (DOM final après JS)
        html = page.content()

        # 👉 Sauvegarde dans un fichier
        with open("page_logic_immo3.2.txt", "w", encoding="utf-8") as f:
            f.write(html)

        browser.close()
        # Donc ici, le code crée le fichier txt, puis il ferme le navigateur qu'il a ouvert une fois terminé.
        print("HTML enregistré dans page_logic_immo3.txt")

# 🔥 EXÉCUTION
scrap_logic_immo()
