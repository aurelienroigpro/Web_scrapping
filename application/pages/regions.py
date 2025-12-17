import streamlit as st
import plotly.express as px
from common import load_df, summary_block

st.set_page_config(page_title="Régions", layout="wide")
st.header("🇫🇷 Analyse par Région")

df = load_df()

with st.sidebar:
    st.header("🎛️ Filtres — Régions")
    type_sel = st.selectbox("Type de bien", ["(Tout)"] + sorted(df["type_bien"].dropna().unique().tolist()), 0)
    df1 = df if type_sel == "(Tout)" else df[df["type_bien"] == type_sel]

    metric = st.radio("Métrique principale", ["Prix/m² médian", "Prix médian", "Surface médiane", "Volume annonces"], index=0)

    min_annonces = st.slider("Seuil min annonces (pour classement)", 1, 100, 10)

# Vue filtrée (sans filtre région ici)
df_view = df1.copy()
if df_view.empty:
    summary_block(df_view)
    st.stop()

# Bandeau synthèse
summary_block(df_view)

st.divider()

# Agrégation région
tab = (
    df_view.groupby("region")
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

# choix métrique
metric_map = {
    "Prix/m² médian": ("prix_m2_median", "€/m²"),
    "Prix médian": ("prix_median", "€"),
    "Surface médiane": ("surface_median", "m²"),
    "Volume annonces": ("annonces", "annonces"),
}
ycol, ylab = metric_map[metric]

tab_sorted = tab.sort_values(ycol, ascending=False)

c1, c2 = st.columns([1.2, 1])

with c1:
    st.subheader("📋 Tableau régions")
    st.dataframe(tab_sorted, use_container_width=True, hide_index=True)

with c2:
    st.subheader(f"📊 {metric} par région")
    fig = px.bar(tab_sorted.head(15), x="region", y=ycol, title=f"Top 15 — {metric}")
    fig.update_layout(xaxis_title="Région", yaxis_title=ylab)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Graphiques supplémentaires
colA, colB = st.columns(2)

with colA:
    st.subheader("📈 Distribution du prix/m² (selon filtres)")
    st.plotly_chart(px.histogram(df_view, x="prix_m2", nbins=80), use_container_width=True)

with colB:
    st.subheader("🏷️ Répartition par type de bien (selon filtres)")
    t = df_view["type_bien"].astype(str).value_counts().reset_index()
    t.columns = ["type_bien", "annonces"]
    st.plotly_chart(px.bar(t, x="type_bien", y="annonces"), use_container_width=True)

st.subheader("🔎 Comparer 2 régions")
regions = sorted(df_view["region"].dropna().unique().tolist())
if len(regions) >= 2:
    r1, r2 = st.columns(2)
    with r1:
        reg_a = st.selectbox("Région A", regions, index=0)
    with r2:
        reg_b = st.selectbox("Région B", regions, index=1)

    dfa = df_view[df_view["region"] == reg_a]
    dfb = df_view[df_view["region"] == reg_b]

    comp = px.box(
        df_view[df_view["region"].isin([reg_a, reg_b])],
        x="region",
        y="prix_m2",
        title="Comparaison prix/m² (boxplot)"
    )
    st.plotly_chart(comp, use_container_width=True)
else:
    st.info("Pas assez de régions disponibles après filtres pour une comparaison.")
