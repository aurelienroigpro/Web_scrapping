import streamlit as st
import pandas as pd
from common import load_df, summary_block, fmt_int

st.set_page_config(page_title="Recherche d'annonces", layout="wide")
st.header("🔎 Recherche d'annonces — France entière")

df0 = load_df()

# ----------------------------
# Utils
# ----------------------------
def uniq_sorted(s: pd.Series):
    return sorted(s.dropna().astype(str).unique().tolist())

def bounds_int(s: pd.Series):
    s2 = pd.to_numeric(s, errors="coerce").dropna()
    if s2.empty:
        return None
    return int(s2.min()), int(s2.max())

def clamp_range(rng, lo, hi):
    a, b = rng
    a = max(lo, min(int(a), hi))
    b = max(lo, min(int(b), hi))
    if a > b:
        a, b = lo, hi
    return (a, b)

def ensure_select_state(key: str, options: list, default="(Tout)"):
    if key not in st.session_state:
        st.session_state[key] = default
    if st.session_state[key] not in options:
        st.session_state[key] = default

def ensure_slider_state(key: str, lo: int, hi: int):
    """Init + clamp d’un slider range dans session_state, sans passer value= au widget."""
    if hi < lo:
        lo, hi = hi, lo
    if key not in st.session_state:
        st.session_state[key] = (lo, hi)
    st.session_state[key] = clamp_range(st.session_state[key], lo, hi)

# Colonnes utiles
ville_col = "ville_cp" if "ville_cp" in df0.columns else "Ville"
SUBTYPE_CANDIDATES = ["sous_type", "sous_type_bien", "type_detail", "categorie", "type_bien_detail"]
subtype_col = next((c for c in SUBTYPE_CANDIDATES if c in df0.columns), None)

# Reset
if st.button("↩️ Réinitialiser tous les filtres"):
    for k in list(st.session_state.keys()):
        if k.startswith("f_"):
            del st.session_state[k]
    st.rerun()

# ----------------------------
# Filtres catégoriels en cascade
# ----------------------------
st.subheader("🎛️ Filtres (catégories)")

c1, c2, c3, c4, c5 = st.columns(5)

# Région
regions = ["(Tout)"] + (uniq_sorted(df0["region"]) if "region" in df0.columns else [])
ensure_select_state("f_region", regions)
with c1:
    st.selectbox("Région", regions, key="f_region")

df1 = df0 if st.session_state.f_region == "(Tout)" else df0[df0["region"] == st.session_state.f_region]

# Département
depts = ["(Tout)"] + (uniq_sorted(df1["departement_nom"]) if "departement_nom" in df1.columns else [])
ensure_select_state("f_dept", depts)
with c2:
    st.selectbox("Département", depts, key="f_dept")

df2 = df1 if st.session_state.f_dept == "(Tout)" else df1[df1["departement_nom"] == st.session_state.f_dept]

# Ville (ville_cp si dispo)
villes = ["(Tout)"] + (uniq_sorted(df2[ville_col]) if ville_col in df2.columns else [])
ensure_select_state("f_ville", villes)
with c3:
    st.selectbox("Ville", villes, key="f_ville")

df3 = df2 if st.session_state.f_ville == "(Tout)" else df2[df2[ville_col] == st.session_state.f_ville]

# Type de bien
types = ["(Tout)"] + (uniq_sorted(df3["type_bien"]) if "type_bien" in df3.columns else [])
ensure_select_state("f_type", types)
with c4:
    st.selectbox("Type de bien", types, key="f_type")

df4 = df3 if st.session_state.f_type == "(Tout)" else df3[df3["type_bien"] == st.session_state.f_type]

# Sous-type (si dispo)
with c5:
    if subtype_col:
        sous_types = ["(Tout)"] + uniq_sorted(df4[subtype_col])
        ensure_select_state("f_subtype", sous_types)
        st.selectbox("Sous-type", sous_types, key="f_subtype")
        df5 = df4 if st.session_state.f_subtype == "(Tout)" else df4[df4[subtype_col] == st.session_state.f_subtype]
    else:
        st.caption("Sous-type : non disponible")
        df5 = df4

# Recherche texte (optionnelle)
q1, q2 = st.columns([2, 1])
with q1:
    if "f_query" not in st.session_state:
        st.session_state.f_query = ""
    st.text_input("Recherche texte (optionnel)", key="f_query", placeholder="ex: ville")

df6 = df5.copy()
query = str(st.session_state.f_query).strip()
if query:
    needle = query.lower()
    text_cols = [c for c in ["titre", "title", "description", "adresse", "Adresse", "Ville"] if c in df6.columns]
    if text_cols:
        mask = False
        for c in text_cols:
            mask = mask | df6[c].astype(str).str.lower().str.contains(needle, na=False)
        df6 = df6[mask].copy()
    else:
        st.info("Aucune colonne texte (titre/description/adresse) trouvée pour la recherche.")

st.divider()

# ----------------------------
# Filtres numériques connectés
# ----------------------------
st.subheader("🔢 Filtres (numériques) — connectés")

# On calcule les bornes sur df6 (après filtres catégoriels)
p_bounds = bounds_int(df6["prix"]) if "prix" in df6.columns else None
s_bounds = bounds_int(df6["surface"]) if "surface" in df6.columns else None
k_bounds = bounds_int(df6["pieces"]) if "pieces" in df6.columns else None  # peut être None si vide/NaN

n1, n2, n3, n4 = st.columns(4)

# Prix
with n1:
    if p_bounds:
        pmin, pmax = p_bounds
        ensure_slider_state("f_prix", pmin, pmax)
        st.slider("Prix (€)", pmin, pmax, key="f_prix")
    else:
        st.caption("Prix indisponible")

# Surface
with n3:
    if s_bounds:
        smin, smax = s_bounds
        ensure_slider_state("f_surface", smin, smax)
        st.slider("Surface (m²)", smin, smax, key="f_surface")
    else:
        st.caption("Surface indisponible")

# Pièces
with n4:
    if k_bounds:
        kmin, kmax = k_bounds
        ensure_slider_state("f_pieces", kmin, kmax)
        st.slider("Pièces", kmin, kmax, key="f_pieces")
        pieces_filter_on = True
    else:
        st.caption("Pièces indisponible")
        pieces_filter_on = False

# Appliquer prix/surface/pièces d’abord
df_num = df6.copy()

if p_bounds:
    a, b = st.session_state.f_prix
    df_num = df_num[df_num["prix"].between(a, b)].copy()

if s_bounds:
    a, b = st.session_state.f_surface
    df_num = df_num[df_num["surface"].between(a, b)].copy()

if pieces_filter_on:
    a, b = st.session_state.f_pieces
    df_num = df_num[(df_num["pieces"].isna()) | (df_num["pieces"].between(a, b))].copy()

# Puis on calcule les bornes de prix/m² sur le sous-ensemble => connecté
pm2_bounds = bounds_int(df_num["prix_m2"]) if "prix_m2" in df_num.columns else None
with n2:
    if pm2_bounds:
        mmin, mmax = pm2_bounds
        ensure_slider_state("f_pm2", mmin, mmax)
        st.slider("Prix/m² (€)", mmin, mmax, key="f_pm2")
    else:
        st.caption("Prix/m² indisponible")

# Appliquer prix/m² en dernier
df_view = df_num.copy()
if pm2_bounds:
    a, b = st.session_state.f_pm2
    df_view = df_view[df_view["prix_m2"].between(a, b)].copy()

st.divider()

# ----------------------------
# Synthèse + Tri + Table + Export
# ----------------------------
summary_block(df_view, title="Synthèse (résultats de recherche)")

if df_view.empty:
    st.warning("Aucune annonce ne correspond aux filtres actuels.")
    st.stop()

t1, t2, t3 = st.columns([1.3, 1, 1])

sort_candidates = [c for c in ["prix_m2", "prix", "surface", "pieces", "region", "departement_nom", "Ville"] if c in df_view.columns]
if not sort_candidates:
    sort_candidates = [df_view.columns[0]]

with t1:
    ensure_select_state("f_sort", sort_candidates, default=sort_candidates[0])
    st.selectbox("Trier par", sort_candidates, key="f_sort")

with t2:
    ensure_select_state("f_order", ["Descendant", "Ascendant"], default="Descendant")
    st.radio("Ordre", ["Descendant", "Ascendant"], key="f_order", horizontal=True)

with t3:
    if "f_nrows" not in st.session_state:
        st.session_state.f_nrows = 200
    st.session_state.f_nrows = st.slider("Lignes affichées", 50, 2000, int(st.session_state.f_nrows), step=50)

ascending = (st.session_state.f_order == "Ascendant")
df_view = df_view.sort_values(st.session_state.f_sort, ascending=ascending, na_position="last")

st.subheader("📄 Résultats")
cols_show = [
    ville_col if ville_col in df_view.columns else "Ville",
    "Code_postal" if "Code_postal" in df_view.columns else None,
    "region" if "region" in df_view.columns else None,
    "departement_nom" if "departement_nom" in df_view.columns else None,
    "type_bien" if "type_bien" in df_view.columns else None,
    subtype_col if subtype_col and subtype_col in df_view.columns else None,
    "pieces" if "pieces" in df_view.columns else None,
    "surface" if "surface" in df_view.columns else None,
    "prix" if "prix" in df_view.columns else None,
    "prix_m2" if "prix_m2" in df_view.columns else None,
]
cols_show = [c for c in cols_show if c is not None]

st.dataframe(df_view[cols_show].head(int(st.session_state.f_nrows)), use_container_width=True)

st.download_button(
    "⬇️ Télécharger les résultats (CSV)",
    data=df_view.to_csv(index=False).encode("utf-8"),
    file_name="annonces_filtrees.csv",
    mime="text/csv",
)

st.caption(f"Résultats : {fmt_int(len(df_view))} annonces après filtres.")
