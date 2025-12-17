import streamlit as st
import plotly.express as px
import pandas as pd
from common import load_df, summary_block, fmt_int

st.set_page_config(page_title="Villes", layout="wide")
st.header("🏙️ Analyse par Ville")

df = load_df()

with st.sidebar:
    st.header("🎛️ Filtres — Villes")

    region_sel = st.selectbox("Région", ["(Tout)"] + sorted(df["region"].dropna().unique().tolist()), 0)
    df1 = df if region_sel == "(Tout)" else df[df["region"] == region_sel]

    dept_sel = st.selectbox("Département", ["(Tout)"] + sorted(df1["departement_nom"].dropna().unique().tolist()), 0)
    df2 = df1 if dept_sel == "(Tout)" else df1[df1["departement_nom"] == dept_sel]

    type_sel = st.selectbox("Type de bien", ["(Tout)"] + sorted(df2["type_bien"].dropna().unique().tolist()), 0)
    df3 = df2 if type_sel == "(Tout)" else df2[df2["type_bien"] == type_sel]

    mode = st.radio("Mode", ["Classement villes", "Profil d'une ville"], index=0)

    min_annonces = st.slider("Seuil min annonces", 1, 100, 10)

    ville_sel = None
    if mode == "Profil d'une ville":
        search = st.text_input("Recherche ville (contient…)", "")
        villes = sorted(df3["Ville"].dropna().unique().tolist())
        if search:
            needle = search.lower()
            villes = [v for v in villes if needle in str(v).lower()]
        ville_sel = st.selectbox("Ville", ["(Choisir)"] + villes, 0)

# mini synthèse sur le scope
if df3.empty:
    summary_block(df3)
    st.stop()

summary_block(df3)

st.divider()

if mode == "Classement villes":
    tab = (
        df3.groupby(["Ville", "departement_nom", "region"])
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

    st.subheader("🏙️ Top 30 villes (par volume)")
    tab_vol = tab.sort_values("annonces", ascending=False).head(30)
    st.dataframe(tab_vol, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Volume annonces — Top 15")
        st.plotly_chart(px.bar(tab_vol.head(15), x="Ville", y="annonces"), use_container_width=True)
    with c2:
        st.subheader("📊 Prix/m² médian — Top 15 (volume)")
        st.plotly_chart(px.bar(tab_vol.head(15), x="Ville", y="prix_m2_median"), use_container_width=True)

else:
    if ville_sel in (None, "(Choisir)"):
        st.info("Choisis une ville dans la sidebar pour afficher son profil.")
        st.stop()

    df_city = df3[df3["Ville"] == ville_sel].copy()
    if df_city.empty:
        st.warning("Aucune annonce pour cette ville avec les filtres.")
        st.stop()

    st.subheader(f"📍 Profil : {ville_sel}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annonces", fmt_int(len(df_city)))
    c2.metric("Prix médian", f"{fmt_int(df_city['prix'].median())} €")
    c3.metric("Surface médiane", f"{df_city['surface'].median():.1f} m²")
    c4.metric("Prix/m² médian", f"{df_city['prix_m2'].median():.0f} €/m²")

    colA, colB = st.columns(2)
    with colA:
        st.subheader("Distribution prix/m²")
        st.plotly_chart(px.histogram(df_city, x="prix_m2", nbins=60), use_container_width=True)
    with colB:
        st.subheader("Prix vs surface")
        st.plotly_chart(px.scatter(df_city, x="surface", y="prix"), use_container_width=True)

    if "Arrondissement" in df_city.columns and ville_sel in ["Paris", "Lyon", "Marseille"]:
        arr = df_city.dropna(subset=["Arrondissement"]).copy()
        arr["Arrondissement"] = pd.to_numeric(arr["Arrondissement"], errors="coerce")
        arr = arr.dropna(subset=["Arrondissement"])
        if not arr.empty:
            arr["Arrondissement"] = arr["Arrondissement"].astype(int)
            st.subheader("Focus arrondissements")
            st.plotly_chart(px.box(arr, x="Arrondissement", y="prix_m2"), use_container_width=True)

    st.subheader("Annonces (200 max)")
    st.dataframe(df_city.head(200), use_container_width=True)

    st.download_button(
        "Télécharger le CSV filtré (ville)",
        data=df_city.to_csv(index=False).encode("utf-8"),
        file_name=f"immo_{ville_sel}.csv",
        mime="text/csv",
    )
