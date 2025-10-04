from typing import Tuple

import streamlit as st
import streamlit_authenticator as stauth


def _to_plain(obj):
    if hasattr(obj, "items"):
        return {key: _to_plain(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_plain(value) for value in obj]
    return obj


def build_authenticator() -> stauth.Authenticate:
    auth_conf = st.secrets.get("auth", {})
    credentials = _to_plain(auth_conf.get("credentials", {}))
    cookie_name = auth_conf.get("cookie_name", "contractgen")
    signature_key = auth_conf.get("signature_key", "CHANGE_ME_SECRET")
    cookie_expiry_days = auth_conf.get("cookie_expiry_days", 7)
    return stauth.Authenticate(
        credentials,
        cookie_name,
        signature_key,
        cookie_expiry_days,
    )


def require_login(location: str = "main") -> Tuple[stauth.Authenticate, str, str]:
    authenticator = build_authenticator()
    name, auth_status, username = authenticator.login(location=location)

    if auth_status is False:
        st.error("Ugyldigt brugernavn eller adgangskode")
        st.stop()
    elif auth_status is None:
        st.info("Indtast brugernavn og adgangskode for at fortsætte")
        st.stop()

    return authenticator, name, username


def logout(authenticator: stauth.Authenticate, label: str = "Log ud") -> None:
    authenticator.logout(label)
