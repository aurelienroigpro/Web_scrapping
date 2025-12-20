import pandas as pd

# ============================================================
# 📂 FICHIERS (à adapter)
# ============================================================
CSV_1 = "annonce2.csv"  
CSV_2 = "annonce.csv"   
OUTPUT_CSV = "annonceclean.csv"

# ============================================================
# 🧼 Fonctions utilitaires
# ============================================================
def clean_price_series(s: pd.Series) -> pd.Series:
    """
    Nettoie une série de prix au format FR (espaces, espaces fines) et convertit en numérique.
    Renvoie une série float avec NaN si conversion impossible.
    """
    s = s.astype(str)
    # retire espaces fines insécables + espaces classiques
    s = s.str.replace("\u202f", "", regex=False).str.replace(" ", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def clean_surface_series(s: pd.Series) -> pd.Series:
    """
    Nettoie une série de surfaces (virgule -> point) et convertit en numérique.
    Renvoie une série float avec NaN si conversion impossible.
    """
    s = s.astype(str).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


# ============================================================
# 1) Chargement
# ============================================================
df1 = pd.read_csv(CSV_1)
df2 = pd.read_csv(CSV_2)

print("CSV 1 :", df1.shape)
print("CSV 2 :", df2.shape)

# ============================================================
# 2) Harmonisation colonnes
# ============================================================
if "sous_type" not in df1.columns:
    # on garde l'info la plus proche possible : sous_type = type_bien
    df1["sous_type"] = df1.get("type_bien")

# Si df2 n'a pas sous_type (au cas où), on le crée aussi
if "sous_type" not in df2.columns:
    df2["sous_type"] = df2.get("type_bien")

cols = [
    "prix", "surface", "pieces", "adresse",
    "type_bien", "sous_type",
    "departement_nom", "departement_code"
]

# On ne garde que les colonnes attendues (si une manque: erreur explicite)
missing_1 = [c for c in cols if c not in df1.columns]
missing_2 = [c for c in cols if c not in df2.columns]
if missing_1:
    raise ValueError(f"Colonnes manquantes dans CSV_1: {missing_1}")
if missing_2:
    raise ValueError(f"Colonnes manquantes dans CSV_2: {missing_2}")

df1 = df1[cols].copy()
df2 = df2[cols].copy()

# ============================================================
# 3) Fusion
# ============================================================
df = pd.concat([df1, df2], ignore_index=True)
print("Après fusion :", df.shape)

# ============================================================
# 4) Suppression des viagers (bouquet) AVANT conversion
# ============================================================
df["prix"] = df["prix"].astype(str)
mask_viager = df["prix"].str.contains("bouquet", case=False, na=False)
print("Lignes viager détectées (bouquet) :", int(mask_viager.sum()))
df = df[~mask_viager].copy()
print("Après suppression viagers :", df.shape)

# ============================================================
# 5) Conversion / nettoyage prix, surface, pièces (SAFE)
# ============================================================
df["prix"] = clean_price_series(df["prix"])
df["surface"] = clean_surface_series(df["surface"])
df["pieces"] = pd.to_numeric(df["pieces"], errors="coerce")

# On enlève les lignes non exploitables pour prix/surface
df = df.dropna(subset=["prix", "surface"]).copy()

# ============================================================
# 6) Filtre "validité" (évite valeurs impossibles / erreurs)
# ============================================================
df = df[
    (df["prix"] > 20000) &
    (df["surface"] > 10) &
    (df["surface"] < 500)
].copy()

print("Après filtres validité :", df.shape)

# ============================================================
# 7) Suppression des doublons
# ============================================================
avant = len(df)
df = df.drop_duplicates()
apres = len(df)
print(f"Doublons supprimés : {avant - apres}")
print("Après déduplication :", df.shape)

# ============================================================
# 8) Calcul prix/m² (optionnel mais utile)
# ============================================================
df["prix_m2"] = df["prix"] / df["surface"]

# (Optionnel) Filtre métier sur prix/m² — à activer si tu veux
# df = df[(df["prix_m2"] > 800) & (df["prix_m2"] < 18000)].copy()

# ============================================================
# 9) Sauvegarde
# ============================================================
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
print("\n✅ CSV final créé →", OUTPUT_CSV)
print("Taille finale :", df.shape)
