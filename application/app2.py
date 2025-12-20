import streamlit as st
import plotly.express as px
from common import load_df, fmt_int, apply_theme, add_type_cat, SCATTER_COLOR_MAP

st.set_page_config(page_title="Immo France — Accueil", layout="wide")
apply_theme("accueil")

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
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Annonces", fmt_int(len(df)))
c2.metric("Villes", fmt_int(df["Ville"].dropna().nunique()))
c3.metric("Départements", fmt_int(df["departement_nom"].dropna().nunique()))
c4.metric("Régions", fmt_int(df["region"].dropna().nunique()))
c5.metric("Prix/m² médian", f"{df['prix_m2'].median():.0f} €/m²")
c6.metric("Prix/m² moyen", f"{df['prix_m2'].mean():.0f} €/m²")

tb = df["type_bien"].astype(str).str.lower()
cA, cB, cC = st.columns(3)
cA.metric("Appartements", fmt_int(tb.str.contains("appart").sum()))
cB.metric("Maisons", fmt_int(tb.str.contains("maison").sum()))
cC.metric("Prix médian", f"{df['prix'].median():.0f} €")

st.divider()

st.subheader("🇫🇷 Comparaison nationale — Appartement vs Maison")

tb = df["type_bien"].astype(str).str.lower()
df_nat = df.copy()
df_nat["type_cat"] = "Autre"
df_nat.loc[tb.str.contains("appart"), "type_cat"] = "Appartement"
df_nat.loc[tb.str.contains("maison"), "type_cat"] = "Maison"

df_am = df_nat[df_nat["type_cat"].isin(["Appartement", "Maison"])].copy()

if df_am.empty:
    st.info("Pas assez de données Appartement/Maison pour afficher la comparaison.")
else:
    c1, c2 = st.columns([1, 1.4])

    with c1:
        st.caption("Part des annonces")
        parts = df_am["type_cat"].value_counts().reset_index()
        parts.columns = ["type_cat", "annonces"]
        st.plotly_chart(px.pie(parts, names="type_cat", values="annonces", hole=0.4), use_container_width=True)

    with c2:
        st.caption("Comparaison des médianes")
        comp = (
            df_am.groupby("type_cat")
            .agg(
                prix_m2_median=("prix_m2", "median"),
                prix_median=("prix", "median"),
                surface_median=("surface", "median"),
            )
            .reset_index()
        )

        a, b, c = st.columns(3)
        with a:
            st.subheader("Prix/m² médian")
            st.plotly_chart(px.bar(comp, x="type_cat", y="prix_m2_median"), use_container_width=True)
        with b:
            st.subheader("Prix médian")
            st.plotly_chart(px.bar(comp, x="type_cat", y="prix_median"), use_container_width=True)
        with c:
            st.subheader("Surface médiane")
            st.plotly_chart(px.bar(comp, x="type_cat", y="surface_median"), use_container_width=True)

st.divider()

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
    reg_pm2 = (
        df.groupby("region")["prix_m2"].median()
        .sort_values(ascending=False).head(12)
        .reset_index(name="prix_m2_median")
    )
    st.plotly_chart(px.bar(reg_pm2, x="region", y="prix_m2_median"), use_container_width=True)

st.subheader("📉 Prix vs Surface (échantillon)")

sample = df.sample(min(len(df), 4000), random_state=42)
sample = add_type_cat(sample)

fig = px.scatter(
    sample,
    x="surface",
    y="prix",
    color="type_cat",
    color_discrete_map=SCATTER_COLOR_MAP,
    opacity=0.65
)

fig.update_traces(marker=dict(size=6))
fig.update_layout(
    xaxis=dict(range=[0, 200], title="Surface (m²)"),
    yaxis=dict(range=[0, 3_000_000], title="Prix (€)"),
    legend_title_text=""
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("📉 Prix/m² vs Surface (échantillon)")

zoom = st.checkbox(
    "Limiter l'affichage (surface ≤ 350 m², prix/m² ≤ 10 000 €)",
    value=True
)

sample = df.sample(min(len(df), 4000), random_state=42)

if zoom:
    sample = sample[
        (sample["surface"] <= 350) &
        (sample["prix_m2"] <= 10_000)
    ]

sample = add_type_cat(sample)

fig = px.scatter(
    sample,
    x="surface",
    y="prix_m2",
    color="type_cat",
    color_discrete_map=SCATTER_COLOR_MAP,
    opacity=0.65
)

fig.update_traces(marker=dict(size=6))
fig.update_layout(
    xaxis_title="Surface (m²)",
    yaxis_title="Prix au m² (€)",
    legend_title_text=""
)

st.plotly_chart(fig, use_container_width=True)


st.subheader("🏙️ Top 10 villes (volume)")
top_v = df.groupby("Ville").size().sort_values(ascending=False).head(10).reset_index(name="annonces")
st.dataframe(top_v, use_container_width=True, hide_index=True)

st.info("➡️ Utilise les pages : Régions / Départements / Villes / Carte. Chaque page a ses filtres + bandeau synthèse.")

