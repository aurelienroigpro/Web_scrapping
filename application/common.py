import pandas as pd
import streamlit as st
import plotly.io as pio

CSV_PATH = "data/df_analyseVF4.csv"

DEPT_TO_REGION = {
    "01":"Auvergne-Rhône-Alpes","03":"Auvergne-Rhône-Alpes","07":"Auvergne-Rhône-Alpes","15":"Auvergne-Rhône-Alpes",
    "26":"Auvergne-Rhône-Alpes","38":"Auvergne-Rhône-Alpes","42":"Auvergne-Rhône-Alpes","43":"Auvergne-Rhône-Alpes",
    "63":"Auvergne-Rhône-Alpes","69":"Auvergne-Rhône-Alpes","73":"Auvergne-Rhône-Alpes","74":"Auvergne-Rhône-Alpes",
    "21":"Bourgogne-Franche-Comté","25":"Bourgogne-Franche-Comté","39":"Bourgogne-Franche-Comté","58":"Bourgogne-Franche-Comté",
    "70":"Bourgogne-Franche-Comté","71":"Bourgogne-Franche-Comté","89":"Bourgogne-Franche-Comté","90":"Bourgogne-Franche-Comté",
    "22":"Bretagne","29":"Bretagne","35":"Bretagne","56":"Bretagne",
    "18":"Centre-Val de Loire","28":"Centre-Val de Loire","36":"Centre-Val de Loire","37":"Centre-Val de Loire",
    "41":"Centre-Val de Loire","45":"Centre-Val de Loire",
    "2A":"Corse","2B":"Corse",
    "08":"Grand Est","10":"Grand Est","51":"Grand Est","52":"Grand Est","54":"Grand Est","55":"Grand Est","57":"Grand Est",
    "67":"Grand Est","68":"Grand Est","88":"Grand Est",
    "02":"Hauts-de-France","59":"Hauts-de-France","60":"Hauts-de-France","62":"Hauts-de-France","80":"Hauts-de-France",
    "75":"Île-de-France","77":"Île-de-France","78":"Île-de-France","91":"Île-de-France","92":"Île-de-France","93":"Île-de-France",
    "94":"Île-de-France","95":"Île-de-France",
    "14":"Normandie","27":"Normandie","50":"Normandie","61":"Normandie","76":"Normandie",
    "16":"Nouvelle-Aquitaine","17":"Nouvelle-Aquitaine","19":"Nouvelle-Aquitaine","23":"Nouvelle-Aquitaine","24":"Nouvelle-Aquitaine",
    "33":"Nouvelle-Aquitaine","40":"Nouvelle-Aquitaine","47":"Nouvelle-Aquitaine","64":"Nouvelle-Aquitaine","79":"Nouvelle-Aquitaine",
    "86":"Nouvelle-Aquitaine","87":"Nouvelle-Aquitaine",
    "09":"Occitanie","11":"Occitanie","12":"Occitanie","30":"Occitanie","31":"Occitanie","32":"Occitanie","34":"Occitanie",
    "46":"Occitanie","48":"Occitanie","65":"Occitanie","66":"Occitanie","81":"Occitanie","82":"Occitanie",
    "44":"Pays de la Loire","49":"Pays de la Loire","53":"Pays de la Loire","72":"Pays de la Loire","85":"Pays de la Loire",
    "04":"Provence-Alpes-Côte d'Azur","05":"Provence-Alpes-Côte d'Azur","06":"Provence-Alpes-Côte d'Azur","13":"Provence-Alpes-Côte d'Azur",
    "83":"Provence-Alpes-Côte d'Azur","84":"Provence-Alpes-Côte d'Azur",
    "971":"Guadeloupe","972":"Martinique","973":"Guyane","974":"La Réunion","976":"Mayotte",
}

def fmt_int(x) -> str:
    try:
        return f"{int(x):,}".replace(",", " ")
    except Exception:
        return str(x)

def normalize_dept_code(x):
    if pd.isna(x):
        return None
    s = str(x).strip().upper()
    if s.isdigit() and len(s) == 1:
        s = s.zfill(2)
    return s

@st.cache_data(show_spinner=False)
def load_df() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, dtype={"Code_postal": str})

    for col in ["prix", "surface", "prix_m2", "pieces", "Arrondissement", "latitude", "longitude"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "departement_code" in df.columns:
        df["departement_code"] = df["departement_code"].apply(normalize_dept_code)
        df["region"] = df["departement_code"].map(DEPT_TO_REGION)

    for c in ["prix", "surface", "prix_m2"]:
        if c not in df.columns:
            raise ValueError(f"Colonne manquante : {c}")

    df = df.dropna(subset=["prix", "surface", "prix_m2"])

    for c in ["Ville", "departement_nom", "type_bien"]:
        if c not in df.columns:
            df[c] = "Inconnu"

    if "region" not in df.columns:
        df["region"] = "Inconnue"

    # --- Libellé Ville + Code postal (pour désambiguïsation)
    if "Ville" in df.columns and "Code_postal" in df.columns:
        df["Code_postal"] = df["Code_postal"].astype(str).str.zfill(5)
        df["ville_cp"] = (
            df["Ville"].fillna("Inconnu").astype(str).str.strip()
            + " ("
            + df["Code_postal"].fillna("00000").astype(str)
            + ")"
        )
    else:
        df["ville_cp"] = df.get("Ville", "Inconnu")

    return df

def summary_block(df_view: pd.DataFrame, title: str = "Synthèse (selon filtres)"):
    """Petit bandeau KPI à mettre en haut de chaque page."""
    if df_view is None or df_view.empty:
        st.warning("Aucune donnée avec les filtres actuels.")
        return

    st.subheader(title)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annonces", fmt_int(len(df_view)))
    c2.metric("Prix médian", f"{fmt_int(df_view['prix'].median())} €")
    c3.metric("Surface médiane", f"{df_view['surface'].median():.1f} m²")
    c4.metric("Prix/m² médian", f"{df_view['prix_m2'].median():.0f} €/m²")

    nb_villes = df_view["Ville"].dropna().nunique()
    nb_depts = df_view["departement_nom"].dropna().nunique()
    nb_regions = df_view["region"].dropna().nunique()
    tb = df_view["type_bien"].astype(str).str.lower()
    nb_appart = int(tb.str.contains("appart").sum())
    nb_maison = int(tb.str.contains("maison").sum())

    cA, cB, cC, cD, cE = st.columns(5)
    cA.metric("Villes", fmt_int(nb_villes))
    cB.metric("Départements", fmt_int(nb_depts))
    cC.metric("Régions", fmt_int(nb_regions))
    cD.metric("Appartements", fmt_int(nb_appart))
    cE.metric("Maisons", fmt_int(nb_maison))

# ----------------------------
# THEME PASTEL (par page)
# ----------------------------
PAGE_ACCENTS = {
    "accueil": "#7AA7C7",
    "regions": "#7FB7B2",
    "departements": "#9BBF9A",
    "villes": "#A89CC8",
    "carte": "#E7A7A0",
    "recherche": "#D7C58A",
}

def apply_theme(page_key: str):
    accent = PAGE_ACCENTS.get(page_key, "#7AA7C7")

    template_name = f"immo_{page_key}"
    if template_name not in pio.templates:
        base = pio.templates["plotly_white"]
        pio.templates[template_name] = base
        pio.templates[template_name].layout.colorway = [
            accent,
            "#B7C3D0",
            "#C9D6D2",
            "#D7D0E6",
            "#E8C9C3",
            "#D9D9D9",
        ]
    pio.templates.default = template_name

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: #F7F8FB;
            color: #1F2937;
        }}
        h1, h2, h3, h4 {{
            color: #1F2937;
        }}
        h1::after {{
            content: "";
            display: block;
            width: 72px;
            height: 6px;
            border-radius: 99px;
            margin-top: 10px;
            background: {accent};
            opacity: 0.9;
        }}
        [data-testid="metric-container"] {{
            background-color: #FFFFFF;
            border: 1px solid #E7EAF0;
            border-radius: 14px;
            padding: 12px;
            box-shadow: 0 1px 6px rgba(16,24,40,0.06);
        }}
        [data-testid="metric-container"] [data-testid="stMetricValue"] {{
            color: {accent};
            font-weight: 700;
        }}
        .stButton > button {{
            border-radius: 12px;
            border: 1px solid #E7EAF0;
        }}
        .stButton > button:hover {{
            border-color: {accent};
        }}
        .stDataFrame {{
            background: white;
            border: 1px solid #E7EAF0;
            border-radius: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

SCATTER_COLOR_MAP = {
    "Appartement": "#2563EB",  # bleu plus franc
    "Maison": "#16A34A",       # vert plus franc
    "Autre": "#6B7280",        # gris
}

def add_type_cat(df):
    """Crée une colonne type_cat stable pour les couleurs scatter."""
    tb = df["type_bien"].astype(str).str.lower()
    out = df.copy()
    out["type_cat"] = "Autre"
    out.loc[tb.str.contains("appart"), "type_cat"] = "Appartement"
    out.loc[tb.str.contains("maison"), "type_cat"] = "Maison"
    return out