# SRC/departements.py
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

URL_DEPS = "https://www.logic-immo.com/index/departements-vente"
def get_departements():
    print("1) J'ouvre la page des départements avec Selenium...")

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")  # tu peux enlever cette ligne si tu veux voir la fenêtre

    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()),
        options=options,
    )

    driver.get(URL_DEPS)
    print("   Titre de la page :", driver.title)

    # On récupère le HTML rendu par le navigateur
    html = driver.page_source

    driver.quit()
    print("   Navigateur fermé.")

    # On parse le HTML avec BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    print("2) Je cherche les liens de départements...")

    deps = []
    for a in soup.find_all("a"):
        txt = a.get_text(strip=True)
        # Les liens ressemblent à "Immobilier Nord (59)"
        if txt.startswith("Immobilier") and "(" in txt and ")" in txt:
            href = a.get("href")
            if not href:
                continue
            if href.startswith("/"):
                href = "https://www.logic-immo.com" + href

            deps.append({"nom": txt, "url": href})

    print(f"3) J'ai trouvé {len(deps)} départements.")
    # On affiche quelques exemples pour vérifier
    for d in deps[:5]:
        print("   -", d["nom"], "->", d["url"])

    return deps

def main():
    print("1) Je récupère les départements...")
    deps = get_departements()
    df = pd.DataFrame(deps)
    df.to_csv("DATA/departements.csv", index=False)
    print("✔ Sauvegardé dans DATA/departements.csv")

if __name__ == "__main__":
    main()
