import streamlit as st
import plotly.express as px
from common import load_df, summary_block, apply_theme

st.set_page_config(page_title="Départements", layout="wide")
apply_theme("departements")

st.header("🗺️ Analyse par Département")

df = load_df()

with st.sidebar:
    st.header("🎛️ Filtres — Départements")

    region_sel = st.selectbox("Région", ["(Tout)"] + sorted(df["region"].dropna().unique().tolist()), 0)
    df1 = df if region_sel == "(Tout)" else df[df["region"] == region_sel]

    type_sel = st.selectbox("Type de bien", ["(Tout)"] + sorted(df1["type_bien"].dropna().unique().tolist()), 0)
    df2 = df1 if type_sel == "(Tout)" else df1[df1["type_bien"] == type_sel]

    metric = st.radio("Métrique principale", ["Prix/m² médian", "Prix médian", "Volume annonces"], index=0)

    top_n = st.slider("Top N (graph)", 5, 30, 10)
    min_annonces = st.slider("Seuil min annonces", 1, 100, 10)

df_view = df2.copy()
if df_view.empty:
    summary_block(df_view)
    st.stop()

summary_block(df_view)
st.divider()

tab = (
    df_view.groupby(["departement_nom", "departement_code", "region"])
    .agg(
        annonces=("prix_m2","size"),
        prix_m2_median=("prix_m2","median"),
        prix_median=("prix","median"),
        surface_median=("surface","median"),
    )
    .reset_index()
)
tab = tab[tab["annonces"] >= min_annonces].copy()
tab["prix_m2_median"] = tab["prix_m2_median"].round(0).astype(int)
tab["prix_median"] = tab["prix_median"].round(0).astype(int)
tab["surface_median"] = tab["surface_median"].round(1)

metric_map = {
    "Prix/m² médian": ("prix_m2_median", "€/m²"),
    "Prix médian": ("prix_median", "€"),
    "Volume annonces": ("annonces", "annonces"),
}
ycol, ylab = metric_map[metric]

tab_sorted = tab.sort_values(ycol, ascending=False)

c1, c2 = st.columns([1.2, 1])
with c1:
    st.subheader("📋 Tableau départements")
    st.dataframe(tab_sorted, use_container_width=True, hide_index=True)

with c2:
    st.subheader(f"📊 Top {top_n} — {metric}")
    fig = px.bar(tab_sorted.head(top_n), x="departement_nom", y=ycol)
    fig.update_layout(xaxis_title="Département", yaxis_title=ylab)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

colA, colB = st.columns(2)
with colA:
    st.subheader("📈 Distribution prix/m² (selon filtres)")
    st.plotly_chart(px.histogram(df_view, x="prix_m2", nbins=80), use_container_width=True)

with colB:
    st.subheader("📉 Prix vs surface (échantillon)")
    sample = df_view.sample(min(len(df_view), 4000), random_state=42)
    st.plotly_chart(px.scatter(sample, x="surface", y="prix", color="type_bien"), use_container_width=True)

st.subheader("🏙️ Top 10 villes (dans le scope actuel)")
top_v = (
    df_view.groupby("Ville")
    .size()
    .sort_values(ascending=False)
    .head(10)
    .reset_index(name="annonces")
)
st.dataframe(top_v, use_container_width=True, hide_index=True)