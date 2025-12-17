import streamlit as st
import plotly.express as px
from common import load_df, fmt_int

st.set_page_config(page_title="Immo France — Accueil", layout="wide")

df = load_df()

st.title("🏠 Immo France — Dashboard")
st.markdown(
    """
**Contexte du projet**  
Cette application présente une analyse exploratoire d’annonces immobilières en France (scraping).  
Objectif : comprendre la distribution des prix, surfaces et prix au m² selon la **région**, le **département** et la **ville**.
"""
)

# KPIs globaux
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Annonces", fmt_int(len(df)))
c2.metric("Villes", fmt_int(df["Ville"].dropna().nunique()))
c3.metric("Départements", fmt_int(df["departement_nom"].dropna().nunique()))
c4.metric("Régions", fmt_int(df["region"].dropna().nunique()))
c5.metric("Prix/m² médian", f"{df['prix_m2'].median():.0f} €/m²")

tb = df["type_bien"].astype(str).str.lower()
cA, cB, cC = st.columns(3)
cA.metric("Appartements", fmt_int(tb.str.contains("appart").sum()))
cB.metric("Maisons", fmt_int(tb.str.contains("maison").sum()))
cC.metric("Prix médian", f"{df['prix'].median():.0f} €")

st.divider()

# --- Grille de graphiques
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏷️ Répartition par type de bien")
    t = df["type_bien"].astype(str).value_counts().reset_index()
    t.columns = ["type_bien", "annonces"]
    st.plotly_chart(px.bar(t, x="type_bien", y="annonces"), use_container_width=True)

with col2:
    st.subheader("🇫🇷 Top 10 régions (volume)")
    top_regions = df.groupby("region").size().sort_values(ascending=False).head(10).reset_index(name="annonces")
    st.plotly_chart(px.bar(top_regions, x="region", y="annonces"), use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("📈 Distribution du prix au m²")
    st.plotly_chart(px.histogram(df, x="prix_m2", nbins=80), use_container_width=True)

with col4:
    st.subheader("📊 Prix/m² médian par région (Top 12)")
    reg_pm2 = (df.groupby("region")["prix_m2"].median().sort_values(ascending=False).head(12)
               .reset_index(name="prix_m2_median"))
    st.plotly_chart(px.bar(reg_pm2, x="region", y="prix_m2_median"), use_container_width=True)

st.subheader("📉 Prix vs Surface (échantillon)")
sample = df.sample(min(len(df), 4000), random_state=42)
st.plotly_chart(px.scatter(sample, x="surface", y="prix", color="type_bien"), use_container_width=True)

st.subheader("🏙️ Top 10 villes (volume)")
top_v = df.groupby("Ville").size().sort_values(ascending=False).head(10).reset_index(name="annonces")
st.dataframe(top_v, use_container_width=True, hide_index=True)

st.info("➡️ Utilise les pages : Régions / Départements / Villes / Carte. Chaque page a ses filtres + bandeau synthèse.")
