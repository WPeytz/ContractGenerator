import streamlit as st
from dotenv import load_dotenv

from core.api import has_api_key
from core.auth import logout, require_login
from views import VIEW_REGISTRY

load_dotenv()

st.set_page_config(page_title="Kontraktgenerator", layout="wide")

# Temporarily disable authentication for testing
# authenticator, name, username = require_login()
name = "Test User"
username = "test"

# with st.sidebar:
#     st.caption(f"Logget ind som: {name or username}")
#     logout(authenticator, label="Log ud")
#     st.markdown("---")

st.title("Kontraktgenerator")
if not has_api_key():
    st.warning(
        "Appen har ingen API-nøgle endnu. Tilføj `LEGIS_API_KEY` i Secrets (⚙️ → Secrets) for at hente data."
    )

with st.sidebar:
    st.subheader("Skabeloner")
    view_keys = list(VIEW_REGISTRY.keys())
    selected_view_key = st.radio(
        "Vælg generator",
        options=view_keys,
        format_func=lambda key: VIEW_REGISTRY[key].label,
        key="selected_view",
    )

selected_view = VIEW_REGISTRY[selected_view_key]
selected_view.render()
