import streamlit as st
import plotly.express as px
from common import load_df

st.set_page_config(page_title="Carte", layout="wide")
st.header("🌍 Carte")

df = load_df()

if not (("latitude" in df.columns) and ("longitude" in df.columns)):
    st.warning("Pas de colonnes `latitude` / `longitude` dans ton CSV → carte impossible.")
    st.stop()

df_geo = df.dropna(subset=["latitude", "longitude"]).copy()
if df_geo.empty:
    st.warning("Aucun point géolocalisé (lat/lon vides).")
    st.stop()

with st.sidebar:
    st.header("🎛️ Filtres — Carte")
    region_sel = st.selectbox("Région", ["(Tout)"] + sorted(df_geo["region"].dropna().unique().tolist()), 0)
    df1 = df_geo if region_sel == "(Tout)" else df_geo[df_geo["region"] == region_sel]

    type_sel = st.selectbox("Type de bien", ["(Tout)"] + sorted(df1["type_bien"].dropna().unique().tolist()), 0)
    df2 = df1 if type_sel == "(Tout)" else df1[df1["type_bien"] == type_sel]

    max_points = st.slider("Limiter le nombre de points", 200, 20000, 3000, step=200)

df_map = df2.copy()
if len(df_map) > max_points:
    df_map = df_map.sample(max_points, random_state=42)

hover_cols = [c for c in ["Ville","departement_nom","region","prix","surface","prix_m2","type_bien"] if c in df_map.columns]

fig = px.scatter_map(
    df_map,
    lat="latitude",
    lon="longitude",
    color="prix_m2",
    size="surface" if "surface" in df_map.columns else None,
    hover_name="Ville" if "Ville" in df_map.columns else None,
    hover_data=hover_cols,
    zoom=4,
    height=650,
    title="Annonces géolocalisées (couleur = prix/m²)"
)
fig.update_layout(map_style="open-street-map")
st.plotly_chart(fig, use_container_width=True)
