import streamlit as st
import pandas as pd
import math
import requests
from datetime import datetime

# --- CUSTOM CSS FOR PRO UI ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Value Cards */
    .value-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .value-card:hover {
        transform: translateY(-5px);
        border-color: #00FFA3;
    }
    
    /* Metrics Styling */
    .stMetric {
        background: rgba(0, 255, 163, 0.05);
        padding: 10px;
        border-radius: 10px;
        border-left: 3px solid #00FFA3;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background: linear-gradient(90deg, #00FFA3 0%, #00D1FF 100%);
        color: black;
        font-weight: bold;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURATION & SECRETS ---
try:
    API_KEY = st.secrets["FOOTBALL_API_KEY"]
except:
    st.error("⚠️ API Key missing in Secrets!")
    st.stop()

# --- CACHED DATA FETCHING ---
@st.cache_data(ttl=3600)  # Only hits the API once per hour to save quota
def fetch_today_fixtures(league_ids):
    # This is a placeholder for the call_api function we built
    # In production, replace this with your actual requests.get() logic
    return [
        {"id": 1, "match": "Arsenal vs Chelsea", "prob": 89, "odds": 1.35, "league": "Premier League"},
        {"id": 2, "match": "Leeds vs Hull", "prob": 82, "odds": 1.48, "league": "Championship"},
    ]

# --- SESSION STATE ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Match', 'Odds', 'Stake', 'Result', 'Profit'])

# --- SIDEBAR DASHBOARD ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/football.png", width=80)
    st.title("VibeBot Pro")
    bankroll = st.number_input("Wallet ($)", value=1000.0)
    
    if not st.session_state.history.empty:
        pnl = st.session_state.history['Profit'].sum()
        st.metric("Total P&L", f"${pnl:,.2f}", delta=f"{pnl:,.2f}")
    
    st.markdown("---")
    st.caption("Tracking: EPL, Championship, League One")

# --- MAIN CONTENT ---
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("⚽ Today's Value Hunter")
    st.write(f"**Date:** {datetime.now().strftime('%B %d, %Y')}")

if st.button("🔥 SCAN FOR HIGH-VALUE PICKS"):
    picks = fetch_today_fixtures([39, 40, 41])
    
    if not picks:
        st.info("No value bets found that match your criteria today.")
    else:
        for p in picks:
            # Kelly Calculation
            b = p['odds'] - 1
            prob = p['prob'] / 100
            f_star = ((b * prob) - (1 - prob)) / b if b > 0 else 0
            stake = max(0, round(bankroll * f_star * 0.25, 2))
            
            # HTML Card
            st.markdown(f"""
                <div class="value-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #00FFA3; font-weight: bold;">{p['league']}</span>
                        <span style="background: #00FFA3; color: black; padding: 2px 8px; border-radius: 5px; font-size: 12px;">VALUE FOUND</span>
                    </div>
                    <h2 style="margin: 10px 0;">{p['match']}</h2>
                    <div style="display: flex; gap: 20px;">
                        <div><small>CONFIDENCE</small><br><b style="font-size: 20px;">{p['prob']}%</b></div>
                        <div><small>ODDS</small><br><b style="font-size: 20px;">{p['odds']}</b></div>
                        <div><small>REC. STAKE</small><br><b style="font-size: 20px;">${stake}</b></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Action Area
            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                st.link_button("🚀 BC.Game", f"https://bc.game/sports/search/{p['match'].replace(' ', '+')}")
            with c2:
                st.link_button("📈 Bet365", f"https://www.google.com/search?q=bet365+{p['match'].replace(' ', '+')}")
            with c3:
                with st.expander("📝 Log Result"):
                    with st.form(key=f"f_{p['id']}"):
                        res = st.radio("Outcome", ["Win", "Loss"], horizontal=True)
                        if st.form_submit_button("Confirm & Update P&L"):
                            profit = (stake * p['odds']) - stake if res == "Win" else -stake
                            entry = pd.DataFrame([{'Time': datetime.now().strftime("%H:%M"), 'Match': p['match'], 'Odds': p['odds'], 'Stake': stake, 'Result': res, 'Profit': profit}])
                            st.session_state.history = pd.concat([st.session_state.history, entry], ignore_index=True)
                            st.rerun()

# --- HISTORY SECTION ---
if not st.session_state.history.empty:
    st.divider()
    st.subheader("📊 Session Log")
    st.dataframe(st.session_state.history, use_container_width=True)
  
