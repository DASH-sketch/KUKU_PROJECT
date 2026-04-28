# KEY UI FIXES APPLIED:
# - Replaced emoji icons with SVG (Lucide-style inline SVG)
# - Fixed sidebar overflow into header
# - Removed green background from all icons
# - Only ACTIVE tab is highlighted
# - Improved spacing and alignment

import streamlit as st

# ========== SVG ICONS (Lucide style) ==========
ICONS = {
    "overview": """<svg width='20' height='20' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><path d='M3 3v18h18'/><path d='M7 14l4-4 4 4 5-5'/></svg>""",
    "insights": """<svg width='20' height='20' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><path d='M9 18h6'/><path d='M10 22h4'/><path d='M12 2a7 7 0 00-4 12c.5.5 1 1.5 1 2h6c0-.5.5-1.5 1-2a7 7 0 00-4-12z'/></svg>""",
    "financial": """<svg width='20' height='20' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><rect x='2' y='6' width='20' height='12' rx='2'/><path d='M16 12h.01'/><path d='M12 12h.01'/><path d='M8 12h.01'/></svg>""",
    "operations": """<svg width='20' height='20' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><circle cx='12' cy='12' r='3'/><path d='M19.4 15a1.65 1.65 0 000-6l2.1-1.2-2-3.4-2.5 1a1.65 1.65 0 00-2.8-1.6l-.4-2.7h-4l-.4 2.7a1.65 1.65 0 00-2.8 1.6l-2.5-1-2 3.4 2.1 1.2a1.65 1.65 0 000 6l-2.1 1.2 2 3.4 2.5-1a1.65 1.65 0 002.8 1.6l.4 2.7h4l.4-2.7a1.65 1.65 0 002.8-1.6l2.5 1 2-3.4-2.1-1.2z'/></svg>"""
}

# ========== CSS FIXES ==========
st.markdown("""
<style>
[data-testid="stSidebar"] {
    width: 80px !important;
    overflow: hidden;
}

.sidebar-btn {
    width: 48px;
    height: 48px;
    margin: 10px auto;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #8b949e;
    background: transparent;
    border: 1px solid transparent;
    transition: all 0.2s ease;
}

.sidebar-btn:hover {
    color: #e6edf3;
    border-color: #30363d;
}

.sidebar-btn.active {
    background: rgba(16,185,129,0.15);
    color: #10b981;
    border-color: rgba(16,185,129,0.4);
}

/* FIX HEADER OVERLAP */
header {
    z-index: 999 !important;
}

section.main > div {
    padding-top: 1rem;
}

</style>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
if "tab" not in st.session_state:
    st.session_state.tab = "overview"

with st.sidebar:
    for key in ICONS:
        active = "active" if st.session_state.tab == key else ""
        if st.markdown(f"""
        <div class='sidebar-btn {active}' onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: '{key}'}}, '*')">
            {ICONS[key]}
        </div>
        """, unsafe_allow_html=True):
            st.session_state.tab = key

# ========== HEADER ==========
st.markdown("""
<h1 style='margin-top:10px;'>KUKU Farm Dashboard</h1>
<p style='color:#8b949e;'>Premium farm analytics system</p>
""", unsafe_allow_html=True)

st.divider()

# ========== CONTENT ==========
st.write(f"Current tab: {st.session_state.tab}")

# NOTE:
# You will merge this sidebar system into your main code.
# This fixes:
# - icon style
# - active state
# - spacing
# - visual quality
