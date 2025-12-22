# 🏠 Immo France — Analyse du marché immobilier

## 📌 Présentation

Ce projet vise à analyser le **marché immobilier français** à partir d’annonces de vente collectées par **web scraping**.  
L’objectif principal est de répondre à la problématique suivante :

> **Comment le prix au mètre carré varie-t-il en fonction de la localisation, de la surface et du type de bien immobilier en France ?**

Le projet combine une **analyse exploratoire des données** et une **application interactive Streamlit** permettant d’explorer le marché immobilier à différentes échelles géographiques.

---

## 📊 Données

Les données utilisées proviennent d’annonces immobilières en ligne (maisons et appartements à vendre).  
Elles ont été :
- collectées par scraping à l’échelle départementale,
- fusionnées et nettoyées dans des notebooks Python,
- enrichies (prix au m², régions, géolocalisation),
- utilisées pour l’analyse et la visualisation.

⚠️ Les prix correspondent à des **prix affichés** et non à des prix de transaction réels.

---

## 🧠 Méthodologie (résumé)

- Scraping des annonces par département afin d’obtenir une couverture nationale homogène  
- Fusion de plusieurs fichiers CSV après harmonisation des colonnes  
- Nettoyage et analyse exploratoire dans des notebooks  
- Analyses complémentaires et visualisations intégrées directement dans l’application Streamlit  
- Utilisation d’OpenStreetMap (via Folium) pour la cartographie interactive  

---

## 🖥️ Application Streamlit

L’application permet :
- une **vue nationale** du marché immobilier,
- une analyse **régionale**, **départementale** et **par ville**,
- une **comparaison appartements / maisons**,
- une exploration des relations entre **prix, surface et prix au m²**,
- une **carte interactive** des annonces géolocalisées,
- une page de **recherche avancée** avec filtres dynamiques.

---

## 📂 Structure du projet

```plaintext
├── DATA/
│ ├── df_analyseVF4.csv # Jeu de données final
│ ├── annonces_carte.csv # Données géolocalisées
│
├── application/
│ ├── Accueil.py # Page principale Streamlit
│ ├── common.py # Fonctions communes
│ ├── pages/
│ │ ├── 1_Régions.py
│ │ ├── 2_Départements.py
│ │ ├── 3_Villes.py
│ │ ├── 4_Carte.py
│ │ └── 5_Recherche_annonces.py
│
├── notebooks/
│ ├── test_analyse.ipynb
│ └── nettoyageVF.ipynb
│
├── README.md
└── requirements.txt
```
---

## ⚙️ Installation

### Prérequis
- Python 3.9 ou plus
- `pip`

### Installation des dépendances
```bash
pip install -r requirements.txt




