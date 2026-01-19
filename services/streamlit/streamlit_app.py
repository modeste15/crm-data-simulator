import os
import requests
import pandas as pd
import streamlit as st

FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="CRM Dashboard (POC)", layout="wide")
st.title("CRM Dashboard (Streamlit)")


@st.cache_data(ttl=30)
def api_get(path: str, params=None):
    url = f"{FASTAPI_BASE_URL}{path}"
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def safe_df(data):
    if data is None:
        return pd.DataFrame()
    if isinstance(data, dict):
        return pd.DataFrame([data])
    return pd.DataFrame(data)


with st.sidebar:
    st.header("Connexion")
    st.write("API:", FASTAPI_BASE_URL)
    if st.button("Tester /health"):
        try:
            h = api_get("/health")
            st.success(f"OK: {h}")
        except Exception as e:
            st.error(f"Erreur API: {e}")

# --- Récupération données
colA, colB, colC = st.columns(3)

try:
    produits = api_get("/produits", params={"limit": 200, "offset": 0})
except Exception:
    produits = []

try:
    devis = api_get("/devis", params={"limit": 200, "offset": 0})
except Exception:
    devis = []

try:
    ventes = api_get("/ventes", params={"limit": 200, "offset": 0})
except Exception:
    ventes = []

df_produits = safe_df(produits)
df_devis = safe_df(devis)
df_ventes = safe_df(ventes)

# --- KPI
with colA:
    st.metric("Produits", len(df_produits))
with colB:
    st.metric("Devis", len(df_devis))
with colC:
    st.metric("Ventes", len(df_ventes))

# --- Pipeline / stats simples
st.divider()
c1, c2 = st.columns([2, 3])

with c1:
    st.subheader("Pipeline ventes (par status)")
    if not df_ventes.empty and "status" in df_ventes.columns:
        vc = (
            df_ventes["status"]
            .fillna("unknown")
            .astype(str)
            .value_counts()
            .rename_axis("status")
            .reset_index(name="count")
        )
        st.dataframe(vc, use_container_width=True)
    else:
        st.info("Aucune vente ou champ status absent.")

with c2:
    st.subheader("Top devis (montants)")
    if not df_devis.empty and "total_amount" in df_devis.columns:
        dd = df_devis.copy()
        dd["total_amount"] = pd.to_numeric(dd["total_amount"], errors="coerce").fillna(0)
        st.dataframe(dd.sort_values("total_amount", ascending=False).head(20), use_container_width=True)
    else:
        st.info("Aucun devis ou champ total_amount absent.")

# --- Tables détaillées
st.divider()
tab1, tab2, tab3 = st.tabs(["Produits", "Devis", "Ventes"])

with tab1:
    st.subheader("Liste Produits")
    st.dataframe(df_produits, use_container_width=True)

with tab2:
    st.subheader("Liste Devis")
    st.dataframe(df_devis, use_container_width=True)

with tab3:
    st.subheader("Liste Ventes")
    st.dataframe(df_ventes, use_container_width=True)

st.caption("Données lues via FastAPI (réseau docker) — cache Streamlit 30s.")
