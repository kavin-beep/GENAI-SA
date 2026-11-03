"""Paper-inspired visual layer and a responsive 1,200-particle motion panel."""

import json

import streamlit as st
import streamlit.components.v1 as components


_CSS = """
<style>
:root {
  color-scheme: light;
  --cb-ink: #17221b;
  --cb-muted: #586a60;
  --cb-green: #24724b;
  --cb-blue: #315f94;
  --cb-paper: #ffffff;
  --cb-page: #f8faf7;
  --cb-line: #d9e1d7;
  --cb-font: "Anthropic Sans", "Segoe UI", Arial, sans-serif;
}
html, body, [data-testid="stAppViewContainer"] {
  background: var(--cb-page);
  color: var(--cb-ink);
  font-family: var(--cb-font);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"], .block-container {
  max-width: 1040px;
  padding: 1.7rem 1.5rem 4rem;
}
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] li { color: var(--cb-ink); }
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] p {
  color: var(--cb-muted);
}
h1, h2, h3 { color: var(--cb-ink); letter-spacing: -.035em; }

.cb-hero {
  position: relative;
  overflow: hidden;
  margin: .25rem 0 1.5rem;
  padding: 1.6rem 1.8rem 1.45rem;
  border: 1px solid #dce3d9;
  border-radius: 18px;
  background:
    repeating-linear-gradient(0deg, rgba(38,73,50,.012) 0, rgba(38,73,50,.012) 1px, transparent 1px, transparent 5px),
    var(--cb-paper);
  box-shadow: 6px 7px 0 #d9e5db, 0 18px 38px rgba(30,51,37,.10);
  animation: paper-arrive .55s cubic-bezier(.2,.75,.25,1) both;
}
.cb-hero::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 6px;
  background: linear-gradient(180deg, var(--cb-green) 0 54%, var(--cb-blue) 54% 100%);
}
.cb-hero-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--cb-blue);
  font-size: 11px;
  font-weight: 750;
  letter-spacing: .12em;
  text-transform: uppercase;
}
.cb-hero-meta .cb-meta-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--cb-green);
}
.cb-hero h1 {
  margin: 12px 0 6px;
  color: #141d17 !important;
  font-family: var(--cb-font);
  font-size: clamp(32px, 4.5vw, 46px);
  font-weight: 760;
  line-height: 1.04;
  letter-spacing: -.06em;
}
.cb-hero p {
  max-width: 640px;
  margin: 0;
  color: #36483d;
  font-size: 16px;
  line-height: 1.55;
}
.cb-hero-foot {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 17px;
  color: var(--cb-muted);
  font-size: 12px;
}
.cb-hero-foot strong { color: var(--cb-green); font-weight: 700; }

div[data-testid="stVerticalBlockBorderWrapper"] {
  border: 1px solid var(--cb-line);
  border-radius: 16px;
  background-color: var(--cb-paper);
  box-shadow: 4px 5px 0 #dce7dd, 0 12px 26px rgba(30,51,37,.065);
  transition: transform .2s ease, box-shadow .2s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  transform: translateY(-1px);
  box-shadow: 5px 7px 0 #dce7dd, 0 15px 28px rgba(30,51,37,.08);
}
div[data-testid="stExpander"] {
  border: 1px solid var(--cb-line);
  border-radius: 13px;
  background-color: #fbfcf8;
}
div[data-testid="stExpander"] summary { color: var(--cb-ink); }
.cb-section-label {
  margin: 0 0 .15rem;
  color: var(--cb-blue);
  font-size: 11px;
  font-weight: 760;
  letter-spacing: .1em;
  text-transform: uppercase;
}
[data-testid="stSubheader"] { margin-top: .1rem; }
[data-testid="stSubheader"] h2 {
  color: #17221b;
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: -.035em;
}
.stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div {
  color: #17221b !important;
  border: 1px solid #cbd6cc !important;
  border-radius: 10px !important;
  background: #fff !important;
  box-shadow: inset 0 1px 2px rgba(23,34,27,.035);
}
.stTextInput input:focus, .stTextArea textarea:focus,
[data-baseweb="select"] > div:focus-within {
  border-color: var(--cb-blue) !important;
  box-shadow: 0 0 0 3px rgba(49,95,148,.13) !important;
}
[data-testid="stRadio"] label, [data-testid="stMultiSelect"] label,
[data-testid="stSelectbox"] label, [data-testid="stTextInput"] label,
[data-testid="stTextArea"] label, [data-testid="stNumberInput"] label {
  color: #26362c !important;
  font-weight: 580;
}
.stButton > button, [data-testid="stDownloadButton"] > button {
  min-height: 2.75rem;
  border: 1px solid #1d6842;
  border-radius: 10px;
  background: var(--cb-green);
  color: #fff !important;
  font-weight: 690;
  box-shadow: 3px 4px 0 #cdded0, 0 7px 15px rgba(28,88,53,.12);
  transition: transform .18s ease, box-shadow .18s ease, background .18s ease;
}
.stButton > button:hover, [data-testid="stDownloadButton"] > button:hover {
  transform: translateY(-2px);
  background: #1b603e;
  box-shadow: 3px 6px 0 #cdded0, 0 10px 19px rgba(28,88,53,.16);
  border-color: #174f34;
}
.stButton > button:focus-visible, [data-testid="stDownloadButton"] > button:focus-visible {
  outline: 3px solid rgba(49,95,148,.48);
  outline-offset: 3px;
}
.stButton > button p, [data-testid="stDownloadButton"] > button p {
  color: #fff !important;
}
[data-testid="stAlert"] {
  border: 1px solid #d7e2e9;
  border-radius: 12px;
  background-color: #f5f9fb;
}
[data-testid="stSpinner"] p { color: var(--cb-blue) !important; }
[data-testid="stHorizontalBlock"] { gap: 1rem; }
@keyframes paper-arrive {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 700px) {
  [data-testid="stMainBlockContainer"], .block-container { padding: .8rem 1rem 2.5rem; }
  .cb-hero { padding: 1.25rem 1.2rem 1.2rem; margin-bottom: 1.15rem; }
  .cb-hero p { font-size: 14px; }
  [data-testid="stHorizontalBlock"] { flex-direction: column !important; gap: .2rem; }
  [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
  }
}
</style>
"""

_BLACK_CSS = """
<style>
:root {
  color-scheme: dark;
  --cb-ink: #edf3ee;
  --cb-muted: #a5b3a9;
  --cb-green: #54bd83;
  --cb-blue: #83afe3;
  --cb-paper: #131a15;
  --cb-page: #090d0b;
  --cb-line: #2c3a30;
}
html, body, [data-testid="stAppViewContainer"] {
  background: #090d0b !important;
  color: #edf3ee !important;
}
[data-testid="stMainBlockContainer"], .block-container { color: #edf3ee; }
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] li,
h1, h2, h3 { color: #edf3ee; }
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] p {
  color: #a5b3a9 !important;
}
.cb-hero {
  border-color: #2c3a30;
  background:
    repeating-linear-gradient(0deg, rgba(255,255,255,.012) 0, rgba(255,255,255,.012) 1px, transparent 1px, transparent 5px),
    #131a15;
  box-shadow: 6px 7px 0 #1d3927, 0 18px 38px rgba(0,0,0,.38);
}
.cb-hero-meta { color: #83afe3; }
.cb-hero h1 { color: #edf3ee !important; }
.cb-hero p { color: #c2cec5; }
.cb-hero-foot { color: #a5b3a9; }
.cb-hero-foot strong { color: #69ce96; }
.cb-section-label { color: #83afe3; }
[data-testid="stSubheader"] h2 { color: #edf3ee; }
div[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: #2c3a30;
  background-color: #131a15 !important;
  box-shadow: 4px 5px 0 #1b3424, 0 12px 26px rgba(0,0,0,.32);
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  box-shadow: 5px 7px 0 #1b3424, 0 15px 28px rgba(0,0,0,.38);
}
div[data-testid="stExpander"] {
  border-color: #2c3a30;
  background-color: #101612 !important;
}
div[data-testid="stExpander"] summary { color: #edf3ee; }
[data-testid="stAppViewContainer"] .stTextInput input,
[data-testid="stAppViewContainer"] .stTextArea textarea,
[data-testid="stAppViewContainer"] [data-baseweb="select"],
[data-testid="stAppViewContainer"] [data-baseweb="select"] > div,
[data-testid="stAppViewContainer"] [data-testid="stSelectbox"] input[role="combobox"],
[data-testid="stAppViewContainer"] [data-testid="stMultiSelect"] input[role="combobox"],
[data-testid="stAppViewContainer"] [data-testid="stNumberInput"] input {
  color: #edf3ee !important;
  border-color: #35453a !important;
  background: #101612 !important;
  background-color: #101612 !important;
}
.stSelectbox [data-baseweb="select"] > div > div,
.stMultiSelect [data-baseweb="select"] > div > div {
  color: #edf3ee !important;
  background: transparent !important;
}
[data-testid="stSelectbox"] [role="group"],
[data-testid="stMultiSelect"] [role="group"] {
  border-color: #35453a !important;
  background: #101612 !important;
}
[data-testid="stSelectbox"] button[aria-label="Open"],
[data-testid="stMultiSelect"] button[aria-label="Open"] {
  color: #edf3ee !important;
  background: transparent !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
  color: #93a196 !important;
}
[data-testid="stRadio"] label, [data-testid="stMultiSelect"] label,
[data-testid="stSelectbox"] label, [data-testid="stTextInput"] label,
[data-testid="stTextArea"] label, [data-testid="stNumberInput"] label,
[data-testid="stToggle"] label { color: #dce7df !important; }
div[data-baseweb="popover"], ul[role="listbox"] {
  color: #edf3ee !important;
  background: #151d17 !important;
}
[role="option"] { color: #edf3ee !important; }
.stButton > button, [data-testid="stDownloadButton"] > button {
  border-color: #3b9a66;
  background: #24724b;
  color: #fff !important;
  box-shadow: 3px 4px 0 #16351f, 0 7px 15px rgba(0,0,0,.28);
}
.stButton > button:hover, [data-testid="stDownloadButton"] > button:hover {
  background: #2b8657;
  border-color: #54bd83;
}
.stButton > button p, [data-testid="stDownloadButton"] > button p {
  color: #fff !important;
}
[data-testid="stAlert"] {
  border-color: #354c5d;
  background-color: #111a20 !important;
  color: #dbe8f2;
}
[data-testid="stSpinner"] p { color: #83afe3 !important; }
</style>
"""


_FLEXED_ARM_POLYGON = (
    (28, 108), (39, 95), (52, 81), (66, 69), (80, 60), (93, 53), (103, 45), (112, 36),
    (120, 27), (127, 24), (134, 28), (140, 36), (146, 25), (153, 22), (160, 28), (165, 37),
    (172, 30), (180, 30), (186, 36), (188, 44), (183, 52), (175, 59), (169, 69), (162, 81),
    (152, 93), (140, 102), (127, 110), (113, 116), (99, 121), (84, 122), (69, 119), (55, 115),
    (42, 111), (34, 110),
)


_APP_SHELL_CSS = """
<style>
:root {
  --cb-rail-bg: #e8ede6;
  --cb-card-soft: #f5f7f2;
  --cb-field-bg: #fffef9;
  --cb-field-line: #cbd6cc;
  --cb-strong: #17221b;
  --cb-soft: #536459;
  --cb-shadow: #d9e5db;
  --cb-gridline: rgba(23,34,27,.075);
  --cb-art-bg: #111a14;
  --cb-art-line: rgba(226,244,230,.19);
  --cb-art-soft: #bfcec3;
  --cb-art-green: #69ce96;
  --cb-art-blue: #83afe3;
  --cb-brand-mark-bg: #c5e6cf;
}
[data-testid="stMainBlockContainer"], .block-container { max-width: 1040px; padding-top: .9rem; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMain"] [data-testid="stHeaderActionElements"] { display:none !important; }
[data-testid="stSidebar"] { background: var(--cb-rail-bg) !important; border-right: 1px solid var(--cb-line); }
[data-testid="stSidebar"] > div:first-child { background: var(--cb-rail-bg) !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: var(--cb-soft) !important; }
.cb-brand { display:flex; align-items:center; gap:11px; margin: .55rem .3rem 1.35rem; color:var(--cb-strong); }
.cb-brand-mark { display:grid; place-items:center; width:40px; height:40px; border-radius:13px; color:var(--cb-strong); background:var(--cb-brand-mark-bg); font-size:23px; font-weight:800; box-shadow:0 7px 14px rgba(26,95,58,.16); }
.cb-brand-mark span { color:var(--cb-blue); }
.cb-brand b { display:block; font-size:16px; letter-spacing:-.045em; }
.cb-brand small { display:block; margin-top:2px; color:var(--cb-soft); font-size:9px; font-weight:760; letter-spacing:.14em; }
.cb-rail-label { margin:1rem .45rem .55rem; color:var(--cb-soft); font-size:9px; font-weight:780; letter-spacing:.15em; }
[data-testid="stSidebar"] [data-testid="stButton"] > button { min-height:38px; justify-content:flex-start; text-align:left; border:1px solid transparent !important; border-radius:9px !important; background:transparent !important; box-shadow:none !important; color:var(--cb-strong) !important; }
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover { transform:none; border-color:var(--cb-line) !important; background:var(--cb-card-soft) !important; }
[data-testid="stSidebar"] [data-testid="stButton"] > button p { color:var(--cb-strong) !important; }
[data-testid="stSidebar"] hr { margin:.6rem 0; border-color:var(--cb-line); }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] { gap:5px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { min-height:42px; padding:8px 11px; border:1px solid transparent; border-radius:11px; color:var(--cb-strong) !important; transition:background .18s ease,border-color .18s ease,transform .18s ease; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { transform:translateX(2px); background:var(--cb-card-soft); }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { border-color:var(--cb-line); background:var(--cb-field-bg); box-shadow:2px 3px 0 var(--cb-shadow); }
[data-testid="stSidebar"] [data-testid="stRadio"] label p { color:var(--cb-strong) !important; font-size:13px; font-weight:650; }
[data-testid="stSidebar"] [data-testid="stRadio"] label > div > div:first-child { display:none !important; }
[data-testid="stSidebar"] [data-testid="stToggle"] label { color:var(--cb-strong) !important; font-weight:640; }
.cb-rail-footer { display:flex; align-items:center; gap:8px; margin:1.6rem .45rem .8rem; color:var(--cb-soft); font-size:9px; font-weight:760; letter-spacing:.1em; }
.cb-rail-footer i,.cb-live-dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--cb-green); box-shadow:0 0 0 4px rgba(36,114,75,.12); animation:cb-breathe 2.2s ease-in-out infinite; }
.cb-screen-eyebrow { display:flex; align-items:center; gap:10px; margin:.2rem 0 .85rem; color:var(--cb-blue); font-size:9px; font-weight:780; letter-spacing:.15em; }
.cb-screen-eyebrow i { width:24px; height:1px; background:var(--cb-green); }
.cb-page-heading { margin:0 0 1.3rem; animation:cb-rise .42s cubic-bezier(.2,.75,.25,1) both; }
.cb-page-heading h1 { margin:0 0 .35rem; color:var(--cb-strong) !important; font-size:clamp(30px,4vw,43px); font-weight:760; line-height:1.05; letter-spacing:-.06em; }
.cb-page-heading p { max-width:720px; margin:0; color:var(--cb-soft) !important; font-size:14px; line-height:1.6; }
.cb-home-hero { display:grid; grid-template-columns:minmax(0,1.1fr) minmax(300px,.9fr); gap:22px; align-items:center; position:relative; overflow:hidden; padding:clamp(22px,4vw,42px); border:1px solid var(--cb-line); border-radius:24px; background:linear-gradient(125deg,var(--cb-field-bg),var(--cb-card-soft)); box-shadow:7px 8px 0 var(--cb-shadow),0 20px 45px rgba(22,42,29,.09); animation:cb-rise .52s cubic-bezier(.2,.75,.25,1) both; }
.cb-home-copy { position:relative; z-index:1; }
.cb-kicker { display:flex; align-items:center; gap:9px; color:var(--cb-blue); font-size:9px; font-weight:780; letter-spacing:.13em; }
.cb-home-copy h1,.cb-login-art h1 { margin:18px 0 12px; color:var(--cb-strong) !important; font-size:clamp(35px,5vw,58px); font-weight:790; line-height:.99; letter-spacing:-.073em; }
.cb-home-copy h1 em,.cb-login-art h1 em { color:var(--cb-green); font-style:normal; }
.cb-home-copy p,.cb-login-art-copy p { max-width:510px; margin:0; color:var(--cb-soft); font-size:14px; line-height:1.65; }
.cb-home-meta { display:flex; flex-wrap:wrap; gap:9px 17px; margin-top:25px; color:var(--cb-soft); font-size:9px; font-weight:760; letter-spacing:.1em; }
.cb-home-meta span:first-child { color:var(--cb-green); }
.cb-pitch-art { position:relative; overflow:hidden; min-height:280px; border:1px solid rgba(146,185,155,.18); border-radius:19px; background:var(--cb-art-bg); box-shadow:inset 0 0 50px rgba(0,0,0,.23),0 13px 28px rgba(15,34,21,.19); }
.cb-pitch-art::before { content:""; position:absolute; inset:0; opacity:.18; background-image:linear-gradient(rgba(208,236,213,.15) 1px,transparent 1px),linear-gradient(90deg,rgba(208,236,213,.15) 1px,transparent 1px); background-size:25px 25px; mask-image:linear-gradient(135deg,black,transparent 85%); }
.cb-pitch-label { position:absolute; z-index:1; top:15px; left:17px; color:var(--cb-art-soft); font-size:8px; font-weight:760; letter-spacing:.14em; }
.cb-pitch-art svg { position:absolute; inset:15px 3px 21px; width:calc(100% - 6px); height:calc(100% - 36px); overflow:visible; }
.pitch-outline,.pitch-lines { fill:none; stroke:var(--cb-art-line); stroke-width:1; }
.pitch-route { fill:none; stroke:var(--cb-art-green); stroke-width:3; stroke-linecap:round; stroke-dasharray:6 9; animation:cb-route 7s linear infinite; filter:drop-shadow(0 0 5px rgba(105,206,150,.55)); }
.pitch-start { fill:var(--cb-art-blue); filter:drop-shadow(0 0 7px rgba(131,175,227,.75)); }
.pitch-stop { fill:var(--cb-art-green); filter:drop-shadow(0 0 7px rgba(105,206,150,.8)); animation:cb-pulse 1.9s ease-in-out infinite; transform-origin:318px 79px; }
.pitch-pulse { fill:none; stroke:var(--cb-art-green); stroke-width:1.5; animation:cb-ripple 2.4s ease-out infinite; transform-origin:193px 170px; }
.cb-pitch-foot { position:absolute; right:15px; bottom:13px; left:17px; display:flex; justify-content:space-between; gap:8px; color:var(--cb-art-soft); font-size:8px; letter-spacing:.08em; }
.cb-pitch-foot b { color:var(--cb-art-green); font-size:9px; }
.cb-home-strip { display:grid; grid-template-columns:1.15fr repeat(3,1fr); align-items:center; gap:10px; margin:22px 0 12px; padding:15px 17px; border:1px solid var(--cb-line); border-radius:16px; background:var(--cb-field-bg); box-shadow:3px 4px 0 var(--cb-shadow); }
.cb-home-strip-title span { display:block; color:var(--cb-blue); font-size:8px; font-weight:780; letter-spacing:.12em; }
.cb-home-strip-title b { display:block; margin-top:4px; color:var(--cb-strong); font-size:12px; }
.cb-practice-step { display:flex; align-items:center; gap:9px; color:var(--cb-soft); font-size:10px; line-height:1.35; }
.cb-practice-step i { display:grid; place-items:center; flex:0 0 25px; width:25px; height:25px; border:1px solid var(--cb-line); border-radius:50%; color:var(--cb-green); font-size:8px; font-style:normal; font-weight:780; }
.cb-login-art { display:grid; grid-template-columns:1fr minmax(230px,.65fr); align-items:center; gap:14px; min-height:290px; margin:.65rem 0 1.3rem; padding:clamp(22px,4vw,40px); overflow:hidden; border:1px solid var(--cb-line); border-radius:23px; background:linear-gradient(128deg,var(--cb-field-bg),var(--cb-card-soft)); box-shadow:7px 8px 0 var(--cb-shadow),0 20px 45px rgba(22,42,29,.09); animation:cb-rise .55s cubic-bezier(.2,.75,.25,1) both; }
.cb-login-art h1 { font-size:clamp(33px,4.6vw,52px); }
.cb-login-art-copy p { max-width:460px; }
.cb-login-stamp { display:flex; align-items:center; gap:7px; margin-top:24px; color:var(--cb-strong); font-size:9px; font-weight:800; letter-spacing:.12em; }
.cb-login-stamp b { color:var(--cb-blue); }
.cb-login-stamp i { margin-left:4px; color:var(--cb-soft); font-size:8px; font-style:normal; font-weight:650; }
.cb-login-orbit { position:relative; min-width:0; }
.cb-login-orbit svg { display:block; width:100%; overflow:visible; }
.orbit { fill:none; stroke:var(--cb-line); stroke-width:1; stroke-dasharray:3 7; transform-origin:160px 130px; animation:cb-orbit 23s linear infinite; }
.orbit-two { animation-direction:reverse; animation-duration:29s; }
.orbit-route { fill:none; stroke:var(--cb-green); stroke-width:2.5; stroke-linecap:round; stroke-dasharray:5 8; animation:cb-route 6s linear infinite; }
.orbit-ball { fill:var(--cb-blue); filter:drop-shadow(0 0 7px rgba(72,130,189,.65)); }
.orbit-node { fill:var(--cb-green); filter:drop-shadow(0 0 6px rgba(36,114,75,.6)); }
.orbit-node-blue { fill:var(--cb-blue); }
.orbit-core { fill:var(--cb-green); opacity:.13; animation:cb-pulse 2.5s ease-in-out infinite; transform-origin:160px 130px; }
.orbit-core-inner { fill:var(--cb-green); }
.cb-orbit-caption { margin-top:-8px; color:var(--cb-blue); text-align:center; font-size:8px; font-weight:760; letter-spacing:.13em; }
.cb-orbit-caption span { padding:0 5px; color:var(--cb-green); }
.cb-login-form-heading { margin-top:.25rem; color:var(--cb-strong); font-size:18px; font-weight:740; letter-spacing:-.04em; }
.cb-login-remember { display:flex; align-items:flex-start; gap:10px; margin:.45rem 0 .2rem; color:var(--cb-strong); }
.cb-login-remember > b { display:grid; place-items:center; flex:0 0 22px; width:22px; height:22px; border-radius:50%; color:var(--cb-strong); background:var(--cb-green); font-size:13px; }
.cb-login-remember strong,.cb-login-remember small { display:block; }
.cb-login-remember strong { font-size:12px; }
.cb-login-remember small { margin-top:2px; color:var(--cb-soft); font-size:11px; }
.cb-section-label { color:var(--cb-blue); }
[data-testid="stSubheader"] h2 { color:var(--cb-strong); }
div[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--cb-line); background:var(--cb-field-bg); box-shadow:4px 5px 0 var(--cb-shadow),0 12px 26px rgba(30,51,37,.065); }
.stTextInput input,.stTextArea textarea,[data-testid="stNumberInput"] input,[data-testid="stSelectbox"] input[role="combobox"],[data-testid="stMultiSelect"] input[role="combobox"],[data-baseweb="select"] > div { color:var(--cb-strong) !important; border-color:var(--cb-field-line) !important; background:var(--cb-field-bg) !important; }
[data-testid="stTextInput"] input { width:100% !important; }
[data-testid="stSelectbox"] [role="group"],[data-testid="stMultiSelect"] [role="group"] { border-color:var(--cb-field-line) !important; background:var(--cb-field-bg) !important; }
[data-testid="stSelectbox"] label,[data-testid="stMultiSelect"] label,[data-testid="stTextInput"] label,[data-testid="stTextArea"] label,[data-testid="stNumberInput"] label,[data-testid="stRadio"] label { color:var(--cb-strong) !important; }
[data-testid="stAppViewContainer"] p,[data-testid="stAppViewContainer"] label,[data-testid="stAppViewContainer"] li { color:var(--cb-strong); }
[data-testid="stCaptionContainer"] p { color:var(--cb-soft) !important; }
[data-testid="stExpander"] { border-color:var(--cb-line); background:var(--cb-card-soft); }
[data-testid="stExpander"] summary { color:var(--cb-strong); }
[data-testid="stAlert"] { border-color:var(--cb-line); border-radius:13px; }
.cb-chat-header { display:flex; align-items:center; justify-content:space-between; gap:16px; max-width:768px; min-height:42px; margin:.1rem auto 1rem; }
.cb-chat-model { display:flex; align-items:center; gap:9px; color:var(--cb-strong); }
.cb-chat-model strong { font-size:15px; font-weight:680; letter-spacing:-.02em; }
.cb-chat-model span { color:var(--cb-soft); font-size:12px; }
.cb-chat-eyebrow { margin-bottom:4px; color:var(--cb-blue); font-size:9px; font-weight:780; letter-spacing:.15em; }
.cb-chat-eyebrow span { padding:0 4px; color:var(--cb-green); }
.cb-chat-language { flex:0 0 auto; padding:7px 10px; border:1px solid var(--cb-line); border-radius:999px; color:var(--cb-blue); font-size:8px; font-weight:780; letter-spacing:.1em; }
.cb-chat-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:min(20vh,220px); padding:.6rem 1rem; text-align:center; animation:cb-rise .35s ease both; }
.cb-chat-empty-mark { display:grid; place-items:center; width:40px; height:40px; margin-bottom:18px; border:1px solid var(--cb-line); border-radius:50%; color:var(--cb-green); font-weight:760; }
.cb-chat-empty-mark span { color:var(--cb-blue); }
.cb-chat-empty h1 { margin:0; color:var(--cb-strong) !important; font-size:clamp(25px,3.8vw,34px); font-weight:620; letter-spacing:-.055em; }
.cb-chat-empty p { margin:.55rem 0 0; color:var(--cb-soft) !important; font-size:14px; }
[data-testid="stPopoverButton"] { width:auto !important; min-height:38px; padding:0 13px !important; color:var(--cb-strong) !important; border:1px solid var(--cb-field-line) !important; border-radius:12px !important; background:var(--cb-field-bg) !important; box-shadow:2px 3px 0 var(--cb-shadow); }
[data-testid="stPopoverButton"]:hover { border-color:var(--cb-green) !important; }
[data-testid="stChatMessage"] { max-width:768px; margin:0 auto; padding:.35rem .2rem; }
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) { justify-content:flex-end; background:transparent !important; }
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) [data-testid="stChatMessageAvatarUser"] { display:none; }
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) [data-testid="stChatMessageContent"] { width:fit-content; max-width:min(78%,680px); flex:0 1 auto; margin-left:auto !important; margin-right:0 !important; padding:.7rem .95rem; border:1px solid var(--cb-line); border-radius:18px; background:var(--cb-card-soft) !important; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { color:var(--cb-strong) !important; line-height:1.65; }
[data-testid="stChatInput"] { max-width:768px; margin:0 auto; border:1px solid var(--cb-field-line) !important; border-radius:23px !important; background:var(--cb-field-bg) !important; box-shadow:0 2px 7px rgba(0,0,0,.045); }
[data-testid="stChatInput"] textarea { color:var(--cb-strong) !important; }
[data-testid="stChatInput"] textarea::placeholder { color:var(--cb-soft) !important; }
[data-testid="stText"] pre { color:var(--cb-strong) !important; background:transparent !important; white-space:pre-wrap; }
.cb-user-message,.cb-recommendation-copy { color:var(--cb-strong) !important; line-height:1.65; white-space:pre-wrap; overflow-wrap:anywhere; }
.cb-chat-plan-heading { margin:.15rem 0 .15rem; color:var(--cb-strong); font-size:18px; font-weight:740; letter-spacing:-.03em; }
.cb-chat-answer { max-width:840px; margin:.55rem 0 1rem; color:var(--cb-strong); font-size:14px; line-height:1.7; white-space:pre-wrap; overflow-wrap:anywhere; }
.cb-recommendation-title { margin:.15rem 0 .55rem; color:var(--cb-strong); font-size:15px; font-weight:720; }
.cb-rationale-label { margin:.8rem 0 .25rem; color:var(--cb-blue); font-size:10px; font-weight:780; letter-spacing:.1em; text-transform:uppercase; }
.stButton > button { transition:transform .18s ease,box-shadow .18s ease,background .18s ease; }
.stButton > button:hover { transform:translateY(-2px); }
@keyframes cb-rise { from { opacity:0; transform:translateY(9px); } to { opacity:1; transform:translateY(0); } }
@keyframes cb-breathe { 0%,100% { box-shadow:0 0 0 3px rgba(36,114,75,.10); } 50% { box-shadow:0 0 0 5px rgba(36,114,75,.2); } }
@keyframes cb-route { to { stroke-dashoffset:-100; } }
@keyframes cb-pulse { 0%,100% { opacity:.85; transform:scale(.9); } 50% { opacity:1; transform:scale(1.18); } }
@keyframes cb-ripple { 0% { opacity:.85; transform:scale(.6); } 85%,100% { opacity:0; transform:scale(1.7); } }
@keyframes cb-orbit { to { transform:rotate(360deg); } }
@media (max-width:800px) {
  [data-testid="stSidebar"] [data-testid="stRadio"] label { min-height:38px; }
  .cb-chat-header { align-items:center; }
  .cb-chat-language { display:none; }
  .cb-home-hero { grid-template-columns:1fr; }
  .cb-pitch-art { min-height:245px; }
  .cb-home-strip { grid-template-columns:1fr; align-items:start; }
  .cb-practice-step { padding:2px 0; }
  .cb-login-art { grid-template-columns:1fr; min-height:0; gap:10px; margin:.35rem 0 .8rem; padding:18px 20px; }
  .cb-login-art h1 { margin:12px 0 8px; font-size:clamp(29px,7.4vw,36px); line-height:1.02; }
  .cb-login-art-copy p { font-size:13px; line-height:1.45; }
  .cb-login-stamp { margin-top:12px; }
  .cb-login-orbit { display:none; }
}
@media (prefers-reduced-motion: reduce) {
  *,*::before,*::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; scroll-behavior:auto !important; transition-duration:.01ms !important; }
}
</style>
"""


_APP_SHELL_DARK_CSS = """
<style>
:root {
  --cb-rail-bg:#0b100d;
  --cb-card-soft:#101612;
  --cb-field-bg:#131a15;
  --cb-field-line:#35453a;
  --cb-strong:#edf3ee;
  --cb-soft:#a5b3a9;
  --cb-shadow:#1b3424;
  --cb-gridline:rgba(255,255,255,.07);
  --cb-art-bg:#0d1510;
  --cb-art-line:rgba(226,244,230,.15);
  --cb-art-soft:#bdc9c0;
  --cb-art-green:#69ce96;
  --cb-art-blue:#83afe3;
  --cb-brand-mark-bg:#1b3a29;
}
[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child { background:var(--cb-rail-bg) !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:var(--cb-soft) !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { color:var(--cb-strong) !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:var(--cb-card-soft); }
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { border-color:var(--cb-line); background:#172119; box-shadow:2px 3px 0 #1b3424; }
[data-testid="stSidebar"] [data-testid="stRadio"] label > div > div:first-child { display:none !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label p,
[data-testid="stSidebar"] [data-testid="stToggle"] label { color:var(--cb-strong) !important; }
.cb-brand,.cb-brand b,.cb-rail-label,.cb-page-heading h1,.cb-home-copy h1,.cb-login-art h1,.cb-login-form-heading,
[data-testid="stSubheader"] h2,[data-testid="stExpander"] summary { color:var(--cb-strong) !important; }
.cb-brand small,.cb-rail-footer,.cb-page-heading p,.cb-home-copy p,.cb-login-art-copy p,
[data-testid="stCaptionContainer"] p { color:var(--cb-soft) !important; }
.cb-home-hero,.cb-login-art { border-color:var(--cb-line); background:linear-gradient(125deg,#131a15,#101612); box-shadow:7px 8px 0 #1b3424,0 20px 45px rgba(0,0,0,.32); }
.cb-home-strip,div[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--cb-line); background:var(--cb-field-bg) !important; box-shadow:4px 5px 0 #1b3424,0 12px 26px rgba(0,0,0,.28); }
.cb-home-strip-title b,.cb-practice-step { color:var(--cb-strong); }
.cb-practice-step i { border-color:var(--cb-line); }
.stTextInput input,.stTextArea textarea,[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] input[role="combobox"],[data-testid="stMultiSelect"] input[role="combobox"],
[data-baseweb="select"] > div,[data-testid="stSelectbox"] [role="group"],
[data-testid="stMultiSelect"] [role="group"] { color:var(--cb-strong) !important; border-color:var(--cb-field-line) !important; background:var(--cb-field-bg) !important; }
.stTextInput input::placeholder,.stTextArea textarea::placeholder { color:#93a196 !important; }
[data-testid="stSelectbox"] label,[data-testid="stMultiSelect"] label,[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,[data-testid="stNumberInput"] label,[data-testid="stRadio"] label,
[data-testid="stToggle"] label,[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] h1,[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3 { color:var(--cb-strong) !important; }
[data-testid="stExpander"] { border-color:var(--cb-line); background:var(--cb-card-soft) !important; }
[data-testid="stAlert"] { border-color:#354c5d; background:#111a20 !important; color:#dbe8f2; }
div[data-baseweb="popover"],ul[role="listbox"] { color:var(--cb-strong) !important; background:#151d17 !important; }
[role="option"] { color:var(--cb-strong) !important; }
[data-testid="stChatInput"] { border-color:var(--cb-field-line) !important; background:var(--cb-field-bg) !important; box-shadow:3px 4px 0 #1b3424,0 8px 22px rgba(0,0,0,.25); }
[data-testid="stChatInput"] textarea { color:var(--cb-strong) !important; }
</style>
"""


_THEME_LOCK = """
<style>
:root { color-scheme: __SCHEME__ !important; --primary-color:__GREEN__ !important; --background-color:__PAGE__ !important; --secondary-background-color:__CARD__ !important; --text-color:__STRONG__ !important; --border-color:__LINE__ !important; --cb-ink:__STRONG__ !important; --cb-muted:__SOFT__ !important; --cb-green:__GREEN__ !important; --cb-blue:__BLUE__ !important; --cb-paper:__CARD__ !important; --cb-page:__PAGE__ !important; --cb-line:__LINE__ !important; --cb-rail-bg:__RAIL__ !important; --cb-card-soft:__CARD_SOFT__ !important; --cb-field-bg:__FIELD__ !important; --cb-field-line:__FIELD_LINE__ !important; --cb-strong:__STRONG__ !important; --cb-soft:__SOFT__ !important; --cb-shadow:__SHADOW__ !important; --cb-action-bg:__ACTION__ !important; --cb-brand-mark-bg:__BRAND_MARK__ !important; }
html,body,[data-testid="stAppViewContainer"] { color-scheme:__SCHEME__ !important; background:__PAGE__ !important; color:__STRONG__ !important; }
[data-testid="stAppViewContainer"] p,[data-testid="stAppViewContainer"] label,[data-testid="stAppViewContainer"] li,[data-testid="stAppViewContainer"] h1,[data-testid="stAppViewContainer"] h2,[data-testid="stAppViewContainer"] h3 { color:__STRONG__ !important; }
[data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] p { color:__STRONG__ !important; }
[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child { background:__RAIL__ !important; color:__STRONG__ !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label,[data-testid="stSidebar"] [data-testid="stRadio"] label p,[data-testid="stSidebar"] [data-testid="stToggle"] label { color:__STRONG__ !important; }
[data-testid="stSidebar"] .cb-brand small,[data-testid="stSidebar"] .cb-rail-label,[data-testid="stSidebar"] .cb-rail-footer { color:__STRONG__ !important; }
[data-testid="stSidebar"] [data-testid="stButton"] > button,[data-testid="stSidebar"] [data-testid="stButton"] > button * { color:__STRONG__ !important; }
[data-testid="stSidebar"] [data-testid="stButton"] > button svg,[data-testid="stAppViewContainer"] [data-testid="stButton"] > button svg,[data-testid="stDownloadButton"] > button svg,[data-testid="stChatInput"] button svg { color:__STRONG__ !important; fill:currentColor !important; stroke:currentColor !important; }
div[data-testid="stVerticalBlockBorderWrapper"],[data-testid="stExpander"] { background:__CARD__ !important; color:__STRONG__ !important; border-color:__LINE__ !important; }
[data-testid="stBottom"],[data-testid="stBottom"] > div { background:__PAGE__ !important; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,[data-testid="stChatMessage"] h1,[data-testid="stChatMessage"] h2,[data-testid="stChatMessage"] h3 { color:__STRONG__ !important; }
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) { justify-content:flex-end; background:transparent !important; }
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) [data-testid="stChatMessageAvatarUser"] { display:none !important; }
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) [data-testid="stChatMessageContent"] { width:fit-content; max-width:min(78%,680px); flex:0 1 auto; margin-left:auto !important; margin-right:0 !important; padding:.7rem .95rem; border:1px solid __LINE__ !important; border-radius:18px; background:__CARD_SOFT__ !important; }
[data-testid="stChatInput"],[data-testid="stChatInput"] > div { color:__STRONG__ !important; background:__FIELD__ !important; border-color:__FIELD_LINE__ !important; }
[data-testid="stChatInput"] textarea { color:__STRONG__ !important; background:transparent !important; }
[data-testid="stChatInput"] textarea::placeholder { color:__SOFT__ !important; }
[data-testid="stChatInput"] button { color:__STRONG__ !important; background:__ACTION__ !important; }
[data-testid="stAppViewContainer"] .cb-brand b,
[data-testid="stAppViewContainer"] .cb-chat-model strong {
  color:__GREEN__;
  animation:cb-title-flow 4.8s ease-in-out infinite alternate;
}
@keyframes cb-title-flow {
  from { color:__GREEN__; text-shadow:0 0 0 rgba(49,95,148,0); }
  to { color:__BLUE__; text-shadow:0 0 9px rgba(49,95,148,.2); }
}
.cb-chat-disclaimer {
  position:fixed; z-index:1000; right:1rem; bottom:.3rem; left:1rem;
  max-width:768px; margin:0 auto; padding:0 .7rem;
  color:__SOFT__ !important; text-align:center; font-size:11px; line-height:1.45;
  pointer-events:none;
}
@media (max-width:600px) { .cb-chat-disclaimer { right:.35rem; left:.35rem; font-size:10px; } }
@media (prefers-reduced-motion:reduce) {
  [data-testid="stAppViewContainer"] .cb-brand b,
  [data-testid="stAppViewContainer"] .cb-chat-model strong { animation:none !important; }
}
[data-testid="stPopoverButton"] { width:auto !important; min-height:38px; padding:0 13px !important; color:__STRONG__ !important; border:1px solid __FIELD_LINE__ !important; border-radius:12px !important; background:__FIELD__ !important; box-shadow:2px 3px 0 __SHADOW__ !important; }
[data-testid="stText"] pre,.cb-user-message,.cb-recommendation-copy,.cb-recommendation-title,.cb-chat-plan-heading,.cb-chat-answer { color:__STRONG__ !important; }
[data-testid="stAppViewContainer"] .cb-login-remember small { color:__STRONG__ !important; }
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stNumberInput"] input,[data-testid="stSelectbox"] input,[data-baseweb="select"] > div { color:__STRONG__ !important; background:__FIELD__ !important; border-color:__FIELD_LINE__ !important; }
.stButton > button,[data-testid="stDownloadButton"] > button { color:__STRONG__ !important; background:__ACTION__ !important; border-color:__LINE__ !important; }
.stButton > button p,.stButton > button span,.stButton > button svg,[data-testid="stDownloadButton"] > button p,[data-testid="stDownloadButton"] > button span { color:__STRONG__ !important; }
.stButton > button svg,[data-testid="stDownloadButton"] > button svg { fill:currentColor !important; stroke:currentColor !important; }
</style>
"""


_AI_STAGE_COMPONENT = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }
html, body { width: 100%; margin: 0; overflow: visible; background: transparent; }
body { color: #17221b; font-family: "Anthropic Sans", "Segoe UI", Arial, sans-serif; }
.stage {
  position: relative; isolation: isolate;
  width: 100%; min-height: 420px;
  display: grid; grid-template-columns: minmax(210px, .82fr) minmax(270px, 1.18fr);
  align-items: center; gap: 18px;
  padding: 23px 27px;
  border: 1px solid #dce3d9; border-radius: 18px;
  background:
    repeating-linear-gradient(0deg, rgba(38,73,50,.012) 0, rgba(38,73,50,.012) 1px, transparent 1px, transparent 5px),
    #fffef9;
  box-shadow: 6px 7px 0 #d9e5db, 0 18px 38px rgba(30,51,37,.10);
  animation: settle .5s cubic-bezier(.2,.75,.25,1) both;
}
.stage-copy { min-width: 0; }
.eyebrow {
  display: flex; align-items: center; gap: 8px;
  color: #315f94; font-size: 10px; font-weight: 760; letter-spacing: .12em;
}
.live-dot {
  width: 7px; height: 7px; border-radius: 50%; background: #24724b;
  box-shadow: 0 0 0 3px rgba(36,114,75,.12);
  animation: pulse 1.8s ease-in-out infinite;
}
h2 {
  margin: 12px 0 7px; color: #17221b;
  font-size: clamp(22px, 2.7vw, 28px); font-weight: 730;
  line-height: 1.12; letter-spacing: -.05em;
}
h2 span { color: #24724b; }
.stage-copy p { max-width: 360px; margin: 0; color: #526259; font-size: 13px; line-height: 1.55; }
.motion-note {
  display: inline-flex; align-items: center; gap: 8px; margin-top: 15px;
  color: #315f94; font-size: 10px; font-weight: 700; letter-spacing: .055em;
  text-transform: uppercase;
}
.motion-note i { width: 4px; height: 4px; border-radius: 50%; background: #24724b; }
.visual {
  position: relative; width: 100%; max-width: 460px; aspect-ratio: 360 / 260;
  justify-self: end;
}
canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 3px rgba(36,114,75,.10); } 50% { box-shadow: 0 0 0 5px rgba(36,114,75,.18); } }
@keyframes settle { from { opacity: 0; transform: translateY(7px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 700px) {
  .stage { grid-template-columns: 1fr; gap: 4px; padding: 20px 19px 15px; }
  .visual { justify-self: center; max-width: 360px; }
  .stage-copy p { max-width: 500px; }
  .motion-note { margin-top: 10px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
}
body[data-theme="black"] .stage {
  border-color: #2c3a30;
  background:
    repeating-linear-gradient(0deg, rgba(255,255,255,.012) 0, rgba(255,255,255,.012) 1px, transparent 1px, transparent 5px),
    #131a15;
  box-shadow: 6px 7px 0 #1d3927, 0 18px 38px rgba(0,0,0,.42);
}
body[data-theme="black"] h2 { color: #edf3ee; }
body[data-theme="black"] h2 span { color: #69ce96; }
body[data-theme="black"] .stage-copy p { color: #bdc9c0; }
body[data-theme="black"] .eyebrow,
body[data-theme="black"] .motion-note { color: #83afe3; }
</style>
</head>
<body data-theme="__THEME__">
<section class="stage" aria-label="CoachBot AI reflection area">
  <div class="stage-copy">
    <div class="eyebrow"><span class="live-dot"></span>COACHBOT WORKSPACE</div>
    <h2>Take a moment.<br><span>Find your next question.</span></h2>
    <p>Your reflection and coach-ready question will appear here after you ask.</p>
    <div class="motion-note"><span>Vertical turn</span><i></i><span>Scatter &amp; reform</span></div>
  </div>
  <div class="visual" aria-hidden="true"><canvas id="particles" width="360" height="260"></canvas></div>
</section>
<script>
(() => {
  const PARTICLE_COUNT = 1200;
  const WORLD_WIDTH = 360;
  const WORLD_HEIGHT = 260;
  const CENTER_X = WORLD_WIDTH / 2;
  const CENTER_Y = WORLD_HEIGHT / 2;
  const FLEXED_ARM = __FLEXED_ARM_POLYGON__;
  const canvas = document.getElementById("particles");
  const ctx = canvas && canvas.getContext("2d", { alpha: true });
  if (!canvas || !ctx) return;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const TAU = Math.PI * 2;
  let seed = 294781;
  const random = () => {
    seed = (seed * 48271) % 2147483647;
    return seed / 2147483647;
  };
  const insidePolygon = (x, y, points) => {
    let inside = false;
    for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
      const [xi, yi] = points[i], [xj, yj] = points[j];
      const crosses = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
      if (crosses) inside = !inside;
    }
    return inside;
  };
  const inDumbbell = (x, y) =>
    (x >= 20 && x <= 52 && y >= 32 && y <= 108) ||
    (x >= 52 && x <= 148 && y >= 61 && y <= 79) ||
    (x >= 148 && x <= 180 && y >= 32 && y <= 108);
  const sampleShape = accepts => {
    const points = [];
    while (points.length < PARTICLE_COUNT) {
      const x = 20 + random() * 168;
      const y = 20 + random() * 104;
      if (accepts(x, y)) points.push({ x: x + 80, y: y + 60 });
    }
    points.sort((a, b) => Math.atan2(a.y - CENTER_Y, a.x - CENTER_X) - Math.atan2(b.y - CENTER_Y, b.x - CENTER_X));
    return points;
  };
  const dumbbell = sampleShape(inDumbbell);
  const maskCanvas = document.createElement("canvas");
  maskCanvas.width = 200;
  maskCanvas.height = 140;
  const maskCtx = maskCanvas.getContext("2d", { willReadFrequently: true });
  let flexedArmMask = null;
  if (maskCtx) {
    maskCtx.font = '112px "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif';
    maskCtx.textAlign = "center";
    maskCtx.textBaseline = "middle";
    maskCtx.fillStyle = "#ffffff";
    maskCtx.fillText("\u{1F4AA}", 100, 70);
    const candidateMask = maskCtx.getImageData(0, 0, 200, 140).data;
    let filledPixels = 0;
    for (let i = 3; i < candidateMask.length; i += 4) if (candidateMask[i] > 70) filledPixels++;
    if (filledPixels > 100) flexedArmMask = candidateMask;
  }
  const flexedArm = sampleShape((x, y) => {
    const px = Math.floor(x), py = Math.floor(y);
    const alpha = flexedArmMask && flexedArmMask[(py * 200 + px) * 4 + 3];
    return flexedArmMask ? alpha > 70 : insidePolygon(x, y, FLEXED_ARM);
  });
  canvas.dataset.particleCount = String(PARTICLE_COUNT);
  canvas.dataset.flexedArmMask = flexedArmMask ? "emoji" : "path";
  const particles = dumbbell.map((from, index) => ({
    from,
    to: flexedArm[index],
    scatterAngle: random() * TAU,
    scatterDistance: 30 + random() * 24,
    scatterLift: (random() - .5) * 16,
    scatterDepth: (random() - .5) * 82,
    depth: (random() - .5) * 28,
    radius: 1.05 + random() * 1.15,
    highlight: .24 + random() * .34,
    alpha: .58 + random() * .40,
  }));
  const resize = () => {
    const box = canvas.getBoundingClientRect();
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.round(box.width * ratio));
    canvas.height = Math.max(1, Math.round(box.height * ratio));
    ctx.setTransform(canvas.width / WORLD_WIDTH, 0, 0, canvas.height / WORLD_HEIGHT, 0, 0);
  };
  new ResizeObserver(resize).observe(canvas);
  resize();
  const smooth = t => t * t * (3 - 2 * t);
  const cycleLength = 14000;
  const phases = [
    { start: 0, end: 900, motion: "hold", pose: "dumbbell", forward: true },
    { start: 900, end: 4900, motion: "rotate", pose: "dumbbell", forward: true },
    { start: 4900, end: 5550, motion: "scatter", pose: "dumbbell", forward: true },
    { start: 5550, end: 6850, motion: "gather", pose: "flexed-arm", forward: true },
    { start: 6850, end: 7850, motion: "hold", pose: "flexed-arm", forward: true },
    { start: 7850, end: 11850, motion: "rotate", pose: "flexed-arm", forward: false },
    { start: 11850, end: 12500, motion: "scatter", pose: "flexed-arm", forward: false },
    { start: 12500, end: 14000, motion: "gather", pose: "dumbbell", forward: false },
  ];
  const start = performance.now();
  const draw = now => {
    ctx.clearRect(0, 0, WORLD_WIDTH, WORLD_HEIGHT);
    const time = reduced ? 0 : ((now - start) % cycleLength);
    const phase = phases.find(item => time >= item.start && time < item.end) || phases[0];
    const progress = (time - phase.start) / (phase.end - phase.start);
    canvas.dataset.phase = phase.motion === "rotate" ? "vertical-rotation-" + phase.pose : phase.motion;
    canvas.dataset.phaseDurationMs = phase.motion === "rotate" ? "4000" : "";
    const forward = phase.forward;
    const sourcePose = forward ? "dumbbell" : "flexed-arm";
    const targetPose = forward ? "flexed-arm" : "dumbbell";
    const burst = phase.motion === "scatter" || phase.motion === "gather" ? Math.sin(Math.PI * progress) : 0;
    const haze = ctx.createRadialGradient(CENTER_X, CENTER_Y, 3, CENTER_X, CENTER_Y, 110);
    haze.addColorStop(0, "rgba(36,114,75," + (.075 * burst) + ")");
    haze.addColorStop(.62, "rgba(49,95,148," + (.028 * burst) + ")");
    haze.addColorStop(1, "rgba(36,114,75,0)");
    ctx.fillStyle = haze;
    ctx.fillRect(25, 10, WORLD_WIDTH - 50, WORLD_HEIGHT - 20);
    for (const particle of particles) {
      let x, y, z = particle.depth;
      if (phase.motion === "hold") {
        const point = phase.pose === "flexed-arm" ? particle.to : particle.from;
        x = point.x; y = point.y;
      } else if (phase.motion === "rotate") {
        const point = phase.pose === "flexed-arm" ? particle.to : particle.from;
        const angle = progress * TAU;
        const dx = point.x - CENTER_X;
        const dz = particle.depth;
        x = CENTER_X + dx * Math.cos(angle) + dz * Math.sin(angle);
        y = point.y;
        z = -dx * Math.sin(angle) + dz * Math.cos(angle);
      } else {
        const from = sourcePose === "flexed-arm" ? particle.to : particle.from;
        const to = targetPose === "flexed-arm" ? particle.to : particle.from;
        const scatter = {
          x: from.x + Math.cos(particle.scatterAngle) * particle.scatterDistance,
          y: from.y + Math.sin(particle.scatterAngle) * particle.scatterDistance * .72 + particle.scatterLift,
        };
        if (phase.motion === "scatter") {
          const blend = smooth(progress);
          x = from.x + (scatter.x - from.x) * blend;
          y = from.y + (scatter.y - from.y) * blend;
          z = particle.depth + (particle.scatterDepth - particle.depth) * blend;
        } else {
          const blend = smooth(progress);
          x = scatter.x + (to.x - scatter.x) * blend;
          y = scatter.y + (to.y - scatter.y) * blend;
          z = particle.scatterDepth + (particle.depth - particle.scatterDepth) * blend;
        }
      }
      const perspective = 240 / (240 - z);
      const px = CENTER_X + (x - CENTER_X) * perspective;
      const py = CENTER_Y + (y - CENTER_Y) * perspective;
      const radius = particle.radius * perspective;
      const light = Math.max(.46, Math.min(1.18, .82 + z / 125));
      const alpha = particle.alpha * (.82 + .18 * burst);
      ctx.globalAlpha = alpha * .34;
      ctx.fillStyle = "#18241c";
      ctx.beginPath();
      ctx.ellipse(px + radius * .48, py + radius * .70, radius * 1.08, radius * .78, 0, 0, TAU);
      ctx.fill();
      ctx.globalAlpha = alpha * light;
      ctx.fillStyle = z > 17 ? "#62b98a" : z < -19 ? "#315f94" : "#24724b";
      ctx.beginPath();
      ctx.arc(px, py, radius * (1 + .10 * burst), 0, TAU);
      ctx.fill();
      ctx.globalAlpha = alpha * particle.highlight * light;
      ctx.fillStyle = "#f5fff7";
      ctx.beginPath();
      ctx.arc(px - radius * .32, py - radius * .34, radius * .31, 0, TAU);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    if (!reduced) requestAnimationFrame(draw);
  };
  draw(start);
})();
</script>
</body>
</html>
"""


def render_theme(black_mode: bool = False) -> None:
    """Apply one complete app and widget palette before rendering page content."""
    st.markdown(_CSS, unsafe_allow_html=True)
    if black_mode:
        st.markdown(_BLACK_CSS, unsafe_allow_html=True)
    st.markdown(_APP_SHELL_CSS, unsafe_allow_html=True)
    if black_mode:
        st.markdown(_APP_SHELL_DARK_CSS, unsafe_allow_html=True)
    palette = {
        "SCHEME": "dark" if black_mode else "light",
        "STRONG": "#edf3ee" if black_mode else "#202123",
        "SOFT": "#a5b3a9" if black_mode else "#5f6368",
        "GREEN": "#54bd83" if black_mode else "#24724b",
        "BLUE": "#83afe3" if black_mode else "#315f94",
        "CARD": "#131a15" if black_mode else "#ffffff",
        "PAGE": "#090d0b" if black_mode else "#ffffff",
        "LINE": "#2c3a30" if black_mode else "#e5e5e5",
        "RAIL": "#0b100d" if black_mode else "#f7f7f8",
        "CARD_SOFT": "#101612" if black_mode else "#f2f3f5",
        "FIELD": "#131a15" if black_mode else "#ffffff",
        "FIELD_LINE": "#35453a" if black_mode else "#d9d9e3",
        "SHADOW": "#1b3424" if black_mode else "#eeeeef",
        "ACTION": "#2b6140" if black_mode else "#9ad8b0",
        "BRAND_MARK": "#1b3a29" if black_mode else "#c5e6cf",
    }
    theme_lock = _THEME_LOCK
    for name, value in palette.items():
        theme_lock = theme_lock.replace(f"__{name}__", value)
    st.markdown(theme_lock, unsafe_allow_html=True)


def render_hero() -> None:
    """Show a simple paper-like CoachBot introduction without a top animation."""
    st.markdown(
        """
        <section class="cb-hero" aria-label="CoachBot AI introduction">
          <div class="cb-hero-meta"><span class="cb-meta-dot"></span>CoachBot AI <span>·</span> Sports reflection</div>
          <h1>Review the play.</h1>
          <p>Look at one moment from practice or a game, then find a useful question to take to your coach.</p>
          <div class="cb-hero-foot"><strong>English by default</strong><span>·</span><span>Private until you ask for suggestions</span></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_ai_stage(black_mode: bool = False, *, compact: bool = False, chat_mode: bool = False) -> None:
    """Render the 1,200-particle motion, with a compact empty-chat treatment."""
    theme_name = "black" if black_mode else "paper"
    html = _AI_STAGE_COMPONENT.replace("__THEME__", theme_name)
    html = html.replace("__FLEXED_ARM_POLYGON__", json.dumps(_FLEXED_ARM_POLYGON))
    if compact:
        compact_styles = """
<style>
.stage.stage-compact { min-height:150px; grid-template-columns:minmax(0,1fr) 165px; gap:10px; padding:12px 18px; }
.stage-compact .stage-copy p,.stage-compact .motion-note { display:none; }
.stage-compact h2 { margin:7px 0 0; font-size:22px; }
.stage-compact .eyebrow { font-size:8px; }
.stage-compact .visual { max-width:165px; }
@media (max-width:700px) {
  .stage.stage-compact { min-height:124px; grid-template-columns:minmax(0,1fr) 115px; gap:5px; padding:10px 13px; }
  .stage-compact h2 { font-size:17px; }
  .stage-compact .visual { max-width:115px; }
}
</style>
"""
        html = html.replace('class="stage"', 'class="stage stage-compact"')
        html = html.replace("</head>", compact_styles + "</head>")
    if chat_mode:
        chat_styles = """
<style>
.stage.stage-chat, body[data-theme="black"] .stage.stage-chat {
  display:block; min-height:0 !important; padding:0 !important; border:0 !important;
  border-radius:0 !important; background:transparent !important; box-shadow:none !important;
  animation:none !important;
}
.stage-chat .stage-copy { display:none !important; }
.stage-chat .visual { width:min(100%,230px); max-width:230px; margin:0 auto; justify-self:center; }
@media (max-width:700px) { .stage-chat .visual { width:min(100%,190px); max-width:190px; } }
</style>
"""
        html = html.replace('class="stage stage-compact"', 'class="stage stage-compact stage-chat"')
        html = html.replace("</head>", chat_styles + "</head>")
    components.html(html, height=175 if compact else 450, scrolling=False, tab_index=-1)
