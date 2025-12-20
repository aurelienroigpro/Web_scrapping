# Ce code va récupérer le fichier d'annonces extraites du html, les nettoyer et les mettre en forme
# pour pouvoir fusionner avec le fichier d'antoine.


import numpy as np
import pandas as pd
import csv



# les départements de france:
departements_fr = {
    "01": "Ain",
    "02": "Aisne",
    "03": "Allier",
    "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes",
    "07": "Ardèche",
    "08": "Ardennes",
    "09": "Ariège",
    "10": "Aube",
    "11": "Aude",
    "12": "Aveyron",
    "13": "Bouches-du-Rhône",
    "14": "Calvados",
    "15": "Cantal",
    "16": "Charente",
    "17": "Charente-Maritime",
    "18": "Cher",
    "19": "Corrèze",
    "2A": "Corse-du-Sud",
    "2B": "Haute-Corse",
    "21": "Côte-d'Or",
    "22": "Côtes-d'Armor",
    "23": "Creuse",
    "24": "Dordogne",
    "25": "Doubs",
    "26": "Drôme",
    "27": "Eure",
    "28": "Eure-et-Loir",
    "29": "Finistère",
    "30": "Gard",
    "31": "Haute-Garonne",
    "32": "Gers",
    "33": "Gironde",
    "34": "Hérault",
    "35": "Ille-et-Vilaine",
    "36": "Indre",
    "37": "Indre-et-Loire",
    "38": "Isère",
    "39": "Jura",
    "40": "Landes",
    "41": "Loir-et-Cher",
    "42": "Loire",
    "43": "Haute-Loire",
    "44": "Loire-Atlantique",
    "45": "Loiret",
    "46": "Lot",
    "47": "Lot-et-Garonne",
    "48": "Lozère",
    "49": "Maine-et-Loire",
    "50": "Manche",
    "51": "Marne",
    "52": "Haute-Marne",
    "53": "Mayenne",
    "54": "Meurthe-et-Moselle",
    "55": "Meuse",
    "56": "Morbihan",
    "57": "Moselle",
    "58": "Nièvre",
    "59": "Nord",
    "60": "Oise",
    "61": "Orne",
    "62": "Pas-de-Calais",
    "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées",
    "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin",
    "68": "Haut-Rhin",
    "69": "Rhône",
    "70": "Haute-Saône",
    "71": "Saône-et-Loire",
    "72": "Sarthe",
    "73": "Savoie",
    "74": "Haute-Savoie",
    "75": "Paris",
    "76": "Seine-Maritime",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "79": "Deux-Sèvres",
    "80": "Somme",
    "81": "Tarn",
    "82": "Tarn-et-Garonne",
    "83": "Var",
    "84": "Vaucluse",
    "85": "Vendée",
    "86": "Vienne",
    "87": "Haute-Vienne",
    "88": "Vosges",
    "89": "Yonne",
    "90": "Territoire de Belfort",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
    "97": "DOM",
    "98": "COM"
}

# définition du csv qui va être utilisé pour le formatage.

f_source= pd.read_csv("annonces-9.csv")



#
# 1ere étape, nettoyage des éléments à problème du fichier.
#**********************************************************

# On va supprimer la mention "à vendre "dans la colonne type de bien

f_source["type_bien"] = f_source["type_bien"].str.split(" ").str[0]



# Dans la colonne: "prix", on va supprimer toutes les mentions de prix au m2.
# Pour ce faire, on supprime tout ce qui est après le symbole €, ainsi que les espaces en trop.

f_source["prix"] = f_source["prix"].str.replace(r"€.*","",regex=True).str.strip()



# On va extraire le code postal pour récupérer le n° de département.
f_source["code postal"]=f_source["adresse"].str.extract(r"\((\d{5})\)")
#n° de département
f_source["departement_code"]= f_source["code postal"].str[:2]

# création de la colonne departement_nom, en utilisant un dictionnaire:
f_source["departement_nom"]=f_source["departement_code"].map(departements_fr)

# On va supprimer le code postal, dans adresse, qui empêche de trouver la localisation.
#f_source["adresse"] = f_source["adresse"].str.replace(r"\(.*$","",regex=True).str.strip()


#
# 2eme étape, réordonner les colonnes et supprimer les inutiles.
#***************************************************************


#1: suppression des colonnes inutiles

#suppression de la colonne chambre
f_source=f_source.drop(columns=["chambres"])

#suppression de la colonne etage
f_source=f_source.drop(columns=["etage"])

#suppression de la colonne description
f_source=f_source.drop(columns=["description"])

#suppression de la colonne agence
f_source=f_source.drop(columns=["agence"])

#suppression de la colonne code postal
f_source=f_source.drop(columns=["code postal"])

#2: réorganisation des colonnes

f_source = f_source[["prix","surface","pieces","adresse","type_bien","departement_nom","departement_code"]]

# tri par numéro de département puis par prix décroissant
f_source=f_source.sort_values(by=["departement_code","prix"],ascending=[True,False]) 



#
# 3eme étape: enregistrement dans un nouveau csv
#***********************************************
f_source.to_csv("annonces_france-2.csv", index=False, encoding="utf-8")


