"""
RAGSPRO UI Helpers — Common UI functions for Streamlit pages
"""

import streamlit as st


def copy_to_clipboard(text, label="Content"):
    """
    Copy text to clipboard with fallback
    Usage: copy_to_clipboard(content, "LinkedIn Post")
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        st.toast(f"✅ {label} copied to clipboard!", icon="✓")
        return True
    except ImportError:
        st.warning("⚠️ pyperclip not installed. Install with: `pip install pyperclip`")
        st.code(text, language="text")
        return False
    except Exception as e:
        st.error(f"❌ Copy failed: {e}")
        return False


def copy_button(text, label="Copy", key="copy_btn"):
    """
    Render a copy button that actually copies to clipboard
    Usage: copy_button(content, "📋 Copy LinkedIn", "copy_li")
    """
    if st.button(label, key=key, use_container_width=True):
        return copy_to_clipboard(text, label.replace("📋 ", "").replace("Copy ", ""))
    return False


def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_required_fields(fields):
    """
    Validate required fields
    fields: dict of {field_name: field_value}
    Returns: (is_valid, error_message)
    """
    missing = [name for name, value in fields.items() if not value or str(value).strip() == ""]
    if missing:
        return False, f"Required fields missing: {', '.join(missing)}"
    return True, ""


def show_loading_spinner(func):
    """Decorator to show loading spinner"""
    def wrapper(*args, **kwargs):
        with st.spinner("Processing..."):
            return func(*args, **kwargs)
    return wrapper
