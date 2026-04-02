import streamlit as st
from pathlib import Path
from datetime import datetime
import subprocess
import sys

st.set_page_config(page_title="RAGSPRO - Content", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data"
CONTENT_DIR = DATA_DIR / "content"
ENGINE_DIR = Path(__file__).parent.parent / "engine"
sys.path.insert(0, str(ENGINE_DIR))

# Custom CSS for platform boxes
st.markdown("""
<style>
    .platform-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #2d3748;
    }
    .platform-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }
    .platform-icon {
        font-size: 1.5rem;
    }
    .platform-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #fff;
    }
    .char-count {
        font-size: 0.75rem;
        color: #a0aec0;
        margin-left: auto;
    }
    .content-preview {
        background: #0d1117;
        border-radius: 8px;
        padding: 1rem;
        font-family: monospace;
        font-size: 0.85rem;
        color: #e6edf3;
        min-height: 120px;
        max-height: 250px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        margin-bottom: 1rem;
    }
    .timestamp {
        font-size: 0.7rem;
        color: #718096;
        margin-top: 0.5rem;
    }
    .action-btn {
        background: #3182ce;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-size: 0.85rem;
        cursor: pointer;
        margin-right: 0.5rem;
    }
    .action-btn:hover {
        background: #2c5282;
    }
    .linkedin-box { border-left: 4px solid #0077b5; }
    .twitter-box { border-left: 4px solid #1da1f2; }
    .instagram-box { border-left: 4px solid #e4405f; }
    .reel-box { border-left: 4px solid #833ab4; }
</style>
""", unsafe_allow_html=True)

st.title("📝 Content Dashboard")
st.caption("Daily content for all platforms — LinkedIn, Twitter/X, Instagram, Reels")

# Get all content folders
if CONTENT_DIR.exists():
    folders = sorted([f for f in CONTENT_DIR.iterdir() if f.is_dir()], reverse=True)
else:
    folders = []

# Stats row
col1, col2, col3, col4 = st.columns(4)
col1.metric("📅 Days", len(folders))
col2.metric("📊 Total Posts", sum(len(list(f.glob("*.txt"))) for f in folders))

# Count content by platform
today = datetime.now().strftime("%Y-%m-%d")
today_folder = CONTENT_DIR / today
linkedin_count = len([f for f in folders if (f / "linkedin.txt").exists()])
twitter_count = len([f for f in folders if (f / "twitter.txt").exists()])
instagram_count = len([f for f in folders if (f / "instagram.txt").exists()])
reel_count = len([f for f in folders if (f / "reel.txt").exists()])

col3.metric("✅ Today's", "Yes" if today_folder.exists() else "No")
col4.metric("🔄 Last Gen", folders[0].name if folders else "Never")

st.divider()

# Generate new content button
if st.button("🚀 Generate Today's Content", use_container_width=True, type="primary"):
    with st.spinner("Generating content for all platforms..."):
        try:
            result = subprocess.run(
                [sys.executable, str(ENGINE_DIR / "content_engine.py")],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                st.success("✅ Content generated successfully!")
                st.rerun()
            else:
                st.error(f"Error: {result.stderr}")
        except Exception as e:
            st.error(f"Failed to generate content: {e}")

st.divider()

if folders:
    # Date selector
    folder_names = [f.name for f in folders]
    selected = st.selectbox("📅 Select Date", folder_names, index=0)

    if selected:
        date_folder = CONTENT_DIR / selected

        # Platform configuration
        platforms = {
            "linkedin.txt": {
                "name": "LinkedIn",
                "icon": "💼",
                "color": "linkedin-box",
                "max_chars": 3000,
                "ideal_chars": "250-350 words"
            },
            "twitter.txt": {
                "name": "Twitter/X",
                "icon": "🐦",
                "color": "twitter-box",
                "max_chars": 280,
                "ideal_chars": "Under 280 chars"
            },
            "instagram.txt": {
                "name": "Instagram",
                "icon": "📸",
                "color": "instagram-box",
                "max_chars": 2200,
                "ideal_chars": "100-150 words"
            },
            "reel.txt": {
                "name": "Reel Script",
                "icon": "🎬",
                "color": "reel-box",
                "max_chars": 1000,
                "ideal_chars": "30-60 seconds"
            }
        }

        # Create 2x2 grid
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)

        platform_positions = [
            ("linkedin.txt", row1_col1),
            ("twitter.txt", row1_col2),
            ("instagram.txt", row2_col1),
            ("reel.txt", row2_col2)
        ]

        for filename, col in platform_positions:
            config = platforms[filename]
            filepath = date_folder / filename

            with col:
                st.markdown(f"""
                <div class="platform-box {config['color']}">
                    <div class="platform-header">
                        <span class="platform-icon">{config['icon']}</span>
                        <span class="platform-name">{config['name']}</span>
                    </div>
                """, unsafe_allow_html=True)

                if filepath.exists():
                    content = filepath.read_text()
                    char_count = len(content)
                    mod_time = datetime.fromtimestamp(filepath.stat().st_mtime)

                    st.markdown(f'<div class="content-preview">{content}</div>', unsafe_allow_html=True)

                    # Char count with color coding
                    char_color = "#48bb78" if char_count <= config['max_chars'] else "#fc8181"
                    st.markdown(f'<div class="char-count" style="color: {char_color};">{char_count} chars | Ideal: {config["ideal_chars"]}</div>', unsafe_allow_html=True)

                    # Action buttons
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button(f"📋 Copy", key=f"copy_{filename}", use_container_width=True):
                            try:
                                import pyperclip
                                pyperclip.copy(content)
                                st.toast(f"✅ {config['name']} copied to clipboard!")
                            except ImportError:
                                st.toast(f"📋 {config['name']} content ready (install pyperclip for auto-copy)")
                                st.code(content, language="text")
                    with btn_col2:
                        if st.button(f"🔄 Regenerate", key=f"regen_{filename}", use_container_width=True):
                            st.info(f"Regenerate {config['name']} — use AI Assistant page for custom generation")

                    st.markdown(f'<div class="timestamp">Generated: {mod_time.strftime("%I:%M %p")}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="content-preview" style="color: #718096; text-align: center; display: flex; align-items: center; justify-content: center;">No content yet</div>', unsafe_allow_html=True)
                    if st.button(f"✨ Generate {config['name']}", key=f"gen_{filename}", use_container_width=True):
                        st.info("Click 'Generate Today\'s Content' above to create all platform content")

                st.markdown("</div>", unsafe_allow_html=True)

        # Bulk actions
        st.divider()
        st.markdown("### 📤 Bulk Actions")
        bulk_col1, bulk_col2, bulk_col3 = st.columns(3)

        with bulk_col1:
            if st.button("📋 Copy All", use_container_width=True):
                all_content = {}
                for filename, config in platforms.items():
                    filepath = date_folder / filename
                    if filepath.exists():
                        all_content[config['name']] = filepath.read_text()

                if all_content:
                    formatted = "\n\n" + "="*50 + "\n\n".join([f"**{k}**:\n\n{v}" for k, v in all_content.items()])
                    try:
                        import pyperclip
                        pyperclip.copy(formatted)
                        st.toast("✅ All content copied!")
                    except:
                        st.code(formatted, language="text")

        with bulk_col2:
            if st.button("📱 Share to Telegram", use_container_width=True):
                st.info("Use AI Assistant page to send content brief to Telegram")

        with bulk_col3:
            if st.button("📧 Email Content", use_container_width=True):
                st.info("Feature coming soon — Email daily content digest")

else:
    st.info("No content generated yet. Click 'Generate Today's Content' to create your first posts!")
