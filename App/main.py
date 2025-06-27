import streamlit as st
from config import PAGE_CONFIG

# --- PAGE SETUP ---
evaluation_page = st.Page(
    page="pages/evaluation.py",
    title="CandidateEvaluation",
    default=True
)

find_candidates_page = st.Page(
    page="pages/search.py",
    title="Find Candidates"
)
dbms_page = st.Page(
    page="pages/dbms.py",
    title="Database Management"
)

# --- PAGE CONFIG ---
st.set_page_config(**PAGE_CONFIG)

# --- NAVIGATION SETUP ---
pg = st.navigation(pages=[evaluation_page, find_candidates_page, dbms_page])

# --- SHARED ON ALL PAGES ---
st.logo("assets/noBgBlack.png")

# --- RUN APP ---
pg.run()