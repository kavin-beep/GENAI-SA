"""List models available to the configured Groq key; no coaching prompt is sent."""

import requests
import streamlit as st

import config


def main() -> None:
    st.set_page_config(page_title="CoachBot model check", layout="centered")
    st.title("Check available Groq models")
    st.write("This lists the model IDs visible to your key. It does not generate a response.")
    try:
        api_key = st.secrets["groq"]["api_key"]
    except Exception:
        st.info("Add [groq] and api_key to .streamlit/secrets.toml, then restart.")
        return
    if not isinstance(api_key, str) or not api_key.strip() or api_key.strip() == "YOUR_API_KEY_HERE":
        st.info("Replace the placeholder in your private secrets.toml with your Groq API key.")
        return
    if not st.button("List available models"):
        return
    try:
        with st.spinner("Checking the model IDs available to your account..."):
            response = requests.get(
                config.GROQ_MODELS_URL,
                headers={"Authorization": f"Bearer {api_key.strip()}", "Accept": "application/json"},
                timeout=config.REQUEST_TIMEOUT_MS / 1000,
            )
        if response.status_code >= 400:
            if response.status_code == 429:
                st.warning("Rate limit reached. Wait and try again, or check your Groq quota.")
            elif response.status_code in (401, 403):
                st.error("The request was rejected. Check the Groq key and account access.")
            else:
                st.error("Groq could not list models right now. Try again later.")
            return
        data = response.json().get("data", [])
        rows = [{"model": row.get("id", "")} for row in data if isinstance(row, dict) and row.get("id")]
        if not rows:
            st.warning("No models were returned. Check the key and account access.")
            return
        st.dataframe(rows, hide_index=True, width="stretch")
        st.info("The app uses the default model shown in config.py. Update MODEL_NAME only if needed.")
        st.caption("A model listing does not prove generation quota or strict JSON Schema access.")
        if config.MODEL_NAME in {row["model"] for row in rows}:
            st.success("Your configured model appears in this account's list.")
        else:
            st.warning("Your configured model does not appear in this account's list.")
    except Exception:
        # Never display provider exception text, request headers, or credential data.
        st.error("The model check could not connect or complete. Check your network and try again.")


if __name__ == "__main__":
    main()
