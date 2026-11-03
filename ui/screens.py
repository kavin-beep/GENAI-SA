"""Sign-in and Settings screens for CoachBot AI."""

from html import escape

import streamlit as st
from pydantic import ValidationError
import config
from core.safety import CoachProfile
from ui.account_memory import persist_account_memory


_PROFILE_WIDGET_DEFAULTS = {
    "profile_preferred_name": "",
    "profile_age_band": "Prefer not to share",
    "profile_sport": "",
    "profile_position": "",
    "profile_experience": "Not set",
    "profile_goal": "",
    "profile_equipment": "",
    "profile_memory": "",
}


def render_login(mode: str, providers: tuple[str | None, ...]) -> None:
    """Show real OIDC sign-in when configured and clearly labeled local preview otherwise."""
    st.markdown(
        """
        <section class="cb-login-art" aria-label="CoachBot AI sign in">
          <div class="cb-login-art-copy">
            <div class="cb-kicker"><span class="cb-live-dot"></span> A CALMER WAY TO REVIEW SPORT</div>
            <h1>Every moment<br><em>can teach you something.</em></h1>
            <p>Bring one moment from practice or a game. Leave with a clearer question for your coach.</p>
            <div class="cb-login-stamp"><span>COACHBOT</span><b>AI</b><i>SPORT / REFLECT / GROW</i></div>
          </div>
          <div class="cb-login-orbit" aria-hidden="true">
            <svg viewBox="0 0 320 260" role="presentation">
              <ellipse class="orbit orbit-one" cx="160" cy="130" rx="125" ry="62" transform="rotate(-24 160 130)" />
              <ellipse class="orbit orbit-two" cx="160" cy="130" rx="94" ry="104" transform="rotate(34 160 130)" />
              <path class="orbit-route" d="M42 172 C79 186 87 88 127 105 S180 187 211 142 S253 75 281 91" />
              <circle class="orbit-ball" cx="42" cy="172" r="7" />
              <circle class="orbit-node" cx="211" cy="142" r="6" />
              <circle class="orbit-node orbit-node-blue" cx="281" cy="91" r="5" />
              <circle class="orbit-core" cx="160" cy="130" r="18" />
              <circle class="orbit-core-inner" cx="160" cy="130" r="6" />
            </svg>
            <div class="cb-orbit-caption">NOTICE <span>·</span> REFLECT <span>·</span> DISCUSS</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown('<div class="cb-section-label">YOUR ACCOUNT</div>', unsafe_allow_html=True)
        st.markdown('<div class="cb-login-form-heading">Sign in to CoachBot AI</div>', unsafe_allow_html=True)
        st.caption("CoachBot is a reflection tool. It does not diagnose injuries or replace a qualified coach or physician.")

        if mode == "invalid":
            st.error("Sign-in settings are incomplete. Add a complete OpenID Connect setup under [auth] in your private Streamlit secrets.")
            with st.expander("What belongs in the private auth settings"):
                st.code(
                    '[auth]\nredirect_uri = "https://YOUR-APP-URL/oauth2callback"\ncookie_secret = "A-LONG-RANDOM-SECRET"\nclient_id = "YOUR-CLIENT-ID"\nclient_secret = "YOUR-CLIENT-SECRET"\nserver_metadata_url = "YOUR-PROVIDER-METADATA-URL"',
                    language="toml",
                )
            return

        if mode == "configured":
            if len(providers) == 1:
                provider = providers[0]
                label = f"Continue with {escape(provider.title())}" if provider else "Sign in securely"
                if st.button(label, type="primary", key="oidc_login", width="stretch"):
                    st.session_state["active_page"] = "Chat"
                    if provider:
                        st.login(provider)
                    else:
                        st.login()
            else:
                for provider in providers:
                    label = f"Continue with {escape(provider.title())}"
                    if st.button(label, type="primary", key=f"oidc_login_{provider}", width="stretch"):
                        st.session_state["active_page"] = "Chat"
                        st.login(provider)
            st.markdown(
                '<div class="cb-login-remember"><b aria-hidden="true">✓</b>'
                '<span><strong>Remember this device</strong><small>After sign-in, this browser stays signed in for up to 30 days.</small></span></div>',
                unsafe_allow_html=True,
            )
            if len(providers) == 1 and providers[0] == "google":
                st.caption("Use your Gmail account. Google handles your password; CoachBot never receives or stores it.")
            else:
                st.caption("Your identity provider handles your password securely; CoachBot never receives or stores it.")
            return

        st.caption("This temporary preview does not create an account or remember sign-in. Configure Google sign-in to use your Gmail account and have this device remembered.")
        with st.expander("Set up secure Google sign-in"):
            st.write("Create an OpenID Connect web client in Google Cloud, add the callback URL there, then place the client details in your private Streamlit secrets. Your Gmail password stays on Google's sign-in page.")
            st.code(
                '[auth]\nredirect_uri = "http://127.0.0.1:8501/oauth2callback"\ncookie_secret = "GENERATE_A_LONG_RANDOM_SECRET"\n\n[auth.google]\nclient_id = "YOUR_GOOGLE_CLIENT_ID"\nclient_secret = "YOUR_GOOGLE_CLIENT_SECRET"\nserver_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"',
                language="toml",
            )
        with st.expander("Set up saved account memory"):
            st.write("Run `supabase/setup.sql` in your Supabase SQL Editor, then add your project URL and server-only secret key to the same private Streamlit secrets file. Never use a publishable key for this server setting.")
            st.code('[supabase]\nurl = "https://YOUR_PROJECT_REF.supabase.co"\nsecret_key = "sb_secret_YOUR_SERVER_KEY"', language="toml")
        if st.button("Continue in local preview", type="primary", key="preview_login", width="stretch"):
            st.session_state.preview_authenticated = True
            st.session_state["active_page"] = "Chat"
            st.rerun()


def render_page_header(kicker: str, title: str, description: str) -> None:
    """Use a compact editorial masthead on the working pages."""
    st.markdown(
        f'<div class="cb-screen-eyebrow"><span>{escape(kicker.upper())}</span><i></i><span>COACHBOT AI</span></div>'
        f'<section class="cb-page-heading"><h1>{escape(title)}</h1><p>{escape(description)}</p></section>',
        unsafe_allow_html=True,
    )


def render_chat_header(language: str = config.DEFAULT_LANGUAGE) -> None:
    """Small chat workspace header, keeping the conversation as the focus."""
    safe_language = escape(language.upper())
    st.markdown(
        '<section class="cb-chat-header"><div class="cb-chat-model">'
        '<strong>CoachBot</strong><span>AI coach</span></div>'
        f'<div class="cb-chat-language">{safe_language}</div></section>',
        unsafe_allow_html=True,
    )


def render_settings(
    api_notice: str | None,
    oidc_mode: str,
    account_memory_status: str = "not_configured",
    account_store=None,
    account_key: str | None = None,
) -> None:
    """Explain appearance, private API setup, and optional account sign-in."""
    render_page_header("Your preferences", "Settings", "A few clear choices for the way your workspace behaves.")

    try:
        profile = CoachProfile.model_validate(st.session_state.get("coach_profile", {}))
    except (ValueError, ValidationError):
        profile = CoachProfile()
        st.session_state["coach_profile"] = profile.model_dump()
    profile_values = profile.model_dump()
    for widget_key, value in _PROFILE_WIDGET_DEFAULTS.items():
        field_name = widget_key.removeprefix("profile_")
        if field_name == "experience":
            field_name = "experience_level"
        st.session_state.setdefault(widget_key, profile_values[field_name])

    with st.container(border=True):
        st.markdown('<div class="cb-section-label">ABOUT YOU & MEMORY</div>', unsafe_allow_html=True)
        st.subheader("Give CoachBot useful context")
        st.write("Add your name, sports background, and preferences you want CoachBot to remember. Everything is optional.")
        st.toggle(
            "Use my saved details and memory in chats",
            key="coach_profile_enabled",
            help="When enabled, these details accompany chat requests to Groq. Turn this off any time.",
        )
        with st.form("coach_profile_form", clear_on_submit=False):
            first, second = st.columns(2)
            with first:
                preferred_name = st.text_input("Preferred name (optional)", max_chars=60, key="profile_preferred_name")
                sport = st.text_input("Main sport", max_chars=60, key="profile_sport")
                experience_level = st.selectbox(
                    "Experience level", ("Not set", "Beginner", "Developing", "Experienced"),
                    key="profile_experience",
                )
            with second:
                age_band = st.selectbox(
                    "Age range (optional)", ("Prefer not to share", "Under 13", "13–15", "16–17"),
                    key="profile_age_band",
                    help="Choose a broad range only; CoachBot does not need your birth date.",
                )
                position = st.text_input("Position or event", max_chars=60, key="profile_position")
                equipment = st.text_input("Equipment you can use", max_chars=180, key="profile_equipment")
            goal = st.text_area("Main sports goal", max_chars=180, height=84, key="profile_goal")
            memory = st.text_area(
                "What should CoachBot remember?",
                max_chars=1000,
                height=120,
                key="profile_memory",
                help="For example: preferred explanation style, sports interests, or equipment you often use.",
            )
            save_profile = st.form_submit_button("Save profile", type="primary", width="stretch")
        if save_profile:
            try:
                updated_profile = CoachProfile(
                    preferred_name=preferred_name,
                    age_band=age_band,
                    sport=sport,
                    position=position,
                    experience_level=experience_level,
                    goal=goal,
                    equipment=equipment,
                    memory=memory,
                )
                st.session_state["coach_profile"] = updated_profile.model_dump()
                save_status = persist_account_memory(account_store, account_key)
                if save_status == "connected":
                    st.success("Profile saved to your signed-in account.")
                elif save_status == "unavailable":
                    st.warning("Profile updated for this session. Supabase could not sync it yet.")
                else:
                    st.success("Profile saved for this app session.")
            except (ValueError, ValidationError):
                st.error("Keep the profile to sports preferences. Contact, injury, and medical details are not accepted.")
        if account_memory_status == "connected":
            st.caption("Your saved profile and conversation history are stored in Supabase for this signed-in account. Profile details go to Groq only when memory sharing is on.")
        else:
            st.caption("Profile details and chat history stay in this session until Supabase account storage is connected. Profile details go to Groq only when memory sharing is on.")

    with st.container(border=True):
        st.markdown('<div class="cb-section-label">APPEARANCE</div>', unsafe_allow_html=True)
        st.subheader("A workspace that feels right")
        st.markdown("Use the **Black theme** switch in the navigation rail. When it is on, the whole workspace uses a black canvas with white text; when it is off, the workspace uses a white day canvas with black text.")
        st.caption("The page, side rail, cards, menus, and form controls change together.")

    with st.container(border=True):
        st.markdown('<div class="cb-section-label">AI RESPONSES</div>', unsafe_allow_html=True)
        st.subheader("Language, tone, and response length")
        choice = st.selectbox("Response language", config.LANGUAGE_OPTIONS, key="chat_language_choice")
        if choice == "Other language":
            other_language = st.text_input("Language name", key="chat_other_language", max_chars=60)
            st.session_state["chat_language"] = other_language.strip() or config.DEFAULT_LANGUAGE
        else:
            st.session_state["chat_language"] = choice
        st.selectbox(
            "Response length", (512, 1024, 2048),
            format_func=lambda value: {512: "Concise", 1024: "Balanced", 2048: "Detailed"}[value],
            key="chat_max_tokens",
            help="This adjusts the answer limit; it does not change safety checks.",
        )
        st.selectbox(
            "Response tone", ("Balanced", "Encouraging", "Straightforward"),
            key="chat_response_style",
            help="Choose the way CoachBot phrases its replies.",
        )
        st.caption("You can also ask in chat to change the theme, language, answer length, tone, or memory sharing. Settings commands are applied locally.")

    with st.container(border=True):
        st.markdown('<div class="cb-section-label">AI CONNECTION</div>', unsafe_allow_html=True)
        st.subheader("Groq API key")
        if api_notice:
            st.warning("Not connected yet. Add the key in the private local file .streamlit/secrets.toml or in your Streamlit Cloud app secrets.")
        else:
            st.success("A private key is saved. This confirms the setting exists; the connection is checked when you send a chat message.")
        with st.expander("Set up the key"):
            st.write("Keep the key in Streamlit secrets. Never paste it into the app, a screenshot, GitHub, or chat.")
            st.code('[groq]\napi_key = "YOUR_API_KEY_HERE"', language="toml")

    with st.container(border=True):
        st.markdown('<div class="cb-section-label">ACCOUNT</div>', unsafe_allow_html=True)
        st.subheader("Sign-in and account memory")
        if oidc_mode == "configured":
            st.success("Secure sign-in is configured through your identity provider.")
        elif oidc_mode == "invalid":
            st.error("The private OpenID Connect settings need attention. Sign-in is not available until they are complete.")
        else:
            st.info("You are in local preview mode. Configure Streamlit OpenID Connect to enable secure account sign-in.")

        if account_memory_status == "connected":
            st.success("Supabase is connected. Chats, saved profile details, and preferences sync with this Google account.")
        elif account_memory_status == "unavailable":
            st.error("Supabase could not load or save account data. This session still works, and CoachBot will not overwrite saved data while the connection is unavailable.")
        elif account_memory_status == "incomplete":
            st.warning("Supabase settings are incomplete. Add both the project URL and private secret key in Streamlit secrets.")
        elif account_memory_status == "invalid":
            st.warning("The Supabase project URL is invalid. Check the private [supabase] settings.")
        elif account_memory_status == "invalid_key":
            st.warning("Use a Supabase server secret key (`sb_secret_...`), not a publishable key.")
        elif account_memory_status == "not_configured":
            st.info("Connect Supabase to keep chats and profile details after sign-out or an app restart.")
        elif account_memory_status == "identity_missing":
            st.warning("The identity provider did not supply an account ID, so account memory cannot be isolated safely.")
        elif account_memory_status == "preview":
            st.info("Local preview keeps chats only for this session. Sign in with Google and connect Supabase for account memory.")
        with st.expander("Set up Supabase account memory"):
            st.write("Run **supabase/setup.sql** in your Supabase SQL Editor. Then add the project URL and a server-only secret key to your private Streamlit secrets. The key stays on the app server; never add it to GitHub or paste it into chat.")
            st.code('[supabase]\nurl = "https://YOUR_PROJECT_REF.supabase.co"\nsecret_key = "sb_secret_YOUR_SERVER_KEY"', language="toml")

    with st.container(border=True):
        st.markdown('<div class="cb-section-label">PRIVACY</div>', unsafe_allow_html=True)
        st.subheader("Your information")
        if account_memory_status == "connected":
            st.write("Chats, profile details, and preferences are saved in your Supabase account row. Conversation context from recent chats may be sent to Groq to support follow-ups; saved profile details are sent only when memory sharing is enabled. Do not add contact, injury, or medical information or use CoachBot for urgent health decisions.")
        else:
            st.write("Chats and saved profile details remain in this app session until Supabase account storage is connected. Saved profile details are sent to Groq only when memory sharing is enabled. Do not add contact, injury, or medical information or use CoachBot for urgent health decisions.")


def render_about() -> None:
    """Describe the product and its intended boundaries."""
    render_page_header("About the project", "A place to think through the play.", "CoachBot AI helps young athletes prepare thoughtful questions for a coach.")
    with st.container(border=True):
        st.markdown('<div class="cb-section-label">THE IDEA</div>', unsafe_allow_html=True)
        st.subheader("Reflection before reaction")
        st.write("Start with one sporting moment, describe what you want to understand, then review a few suggestions with a qualified coach. The athlete remains in charge of the conversation and next step.")
    with st.container(border=True):
        st.markdown('<div class="cb-section-label">BOUNDARIES</div>', unsafe_allow_html=True)
        st.subheader("What CoachBot is for")
        st.write("The AI can answer sports questions, explain general wellness topics, and draft practice plans. It does not diagnose, prescribe injury rehabilitation, guarantee safety, or replace professional coaching or medical care.")
    with st.container(border=True):
        st.markdown('<div class="cb-section-label">LANGUAGE</div>', unsafe_allow_html=True)
        st.subheader("English first, more languages available")
        st.write("The interface and default response are in English. Choose another response language in Settings or ask CoachBot to change it in chat.")
