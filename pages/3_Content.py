import streamlit as st
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="RAGSPRO - Content", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data"
CONTENT_DIR = DATA_DIR / "content"

st.title("Content Library")

# Get all content folders
if CONTENT_DIR.exists():
    folders = sorted([f for f in CONTENT_DIR.iterdir() if f.is_dir()], reverse=True)
else:
    folders = []

# Stats
total_days = len(folders)
total_posts = sum(len(list(f.glob("*.txt"))) for f in folders)

col1, col2 = st.columns(2)
col1.metric("Total Days", total_days)
col2.metric("Total Posts", total_posts)

st.divider()

if folders:
    # Date selector
    folder_names = [f.name for f in folders]
    selected = st.selectbox("Select Date", folder_names)

    if selected:
        date_folder = CONTENT_DIR / selected

        tab1, tab2, tab3, tab4 = st.tabs(["LinkedIn", "Twitter", "Instagram", "Reel"])

        platforms = {
            "linkedin.txt": ("LinkedIn", tab1),
            "twitter.txt": ("Twitter", tab2),
            "instagram.txt": ("Instagram", tab3),
            "reel.txt": ("Reel Script", tab4)
        }

        for filename, (label, tab) in platforms.items():
            with tab:
                filepath = date_folder / filename
                if filepath.exists():
                    content = filepath.read_text()
                    st.text_area(f"{label} Post", content, height=200)
                    if st.button(f"📋 Copy", key=f"copy_{filename}"):
                        st.toast(f"{label} copied!")
                else:
                    st.info(f"No {label} content for this date")
else:
    st.info("No content generated yet. Run content engine first.")
