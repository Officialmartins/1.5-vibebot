import streamlit as st
import pandas as pd
import math
import requests
from datetime import datetime

# --- UI SETTINGS ---
st.set_page_config(page_title="VibeBot 25/26 Pro", layout="wide", page_icon="⚽")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .value-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(0, 255, 163, 0.3);
        border-radius: 12px; padding: 15px; margin-bottom: 15px;
    }
    .update-tag {
        font-size: 0.8em; color: #888; float: right;
    }
    .confidence-bar {
        height: 4px; background: #333; border-radius: 2px; margin-top: 8px;
    }
    .confidence-fill {
        height: 100%; border-radius: 2px; background: linear-gradient(90deg, #00FFA3, #00D1FF);
    }
    </style>
    """, unsafe_allow_html=True)

# --- API CORE ---
def get_data(endpoint, params=None):
    headers = {
        'x-apisports-key': st.secrets["FOOTBALL_API_KEY"],
        'x-apisports-host': 'v3.football.api-sports.io'
    }
    url = f"https://v3.football.api-sports.io/{endpoint}"
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        return r.json()
    except:
        return {}

# --- SIDEBAR & BANKROLL ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Match', 'Odds', 'Stake', 'Result', 'Profit'])

with st.sidebar:
    st.title("💰 25/26 Wallet")
    bank = st.number_input("Balance ($)", value=1000.0)
    if not st.session_state.history.empty:
        st.metric("Total P&L", f"${st.session_state.history['Profit'].sum():,.2f}")

# --- MAIN APP ---
st.title("⚽ Today's Value Scan")
st.caption(f"Season 2025/2026 | {datetime.now().strftime('%H:%M Local Time')}")

if st.button("🔥 REFRESH LIVE ODDS & FIXTURES"):
    today = datetime.now().strftime('%Y-%m-%d')
    leagues = {39: "Premier League", 40: "Championship", 41: "League One"}
    
    with st.spinner("Syncing with 25/26 Match Servers..."):
        # We fetch all fixtures for today in the specified leagues
        found_any = False
        for lid, l_name in leagues.items():
            data = get_data("fixtures", {"league": lid, "date": today, "season": 2025})
            
            for f in data.get('response', []):
                f_id = f['fixture']['id']
                
                # Fetch Predictions & Odds
                pred = get_data("predictions", {"fixture": f_id})
                odds_raw = get_data("odds", {"fixture": f_id, "bet": 5})
                
                try:
                    prob_pct = int(pred['response'][0]['predictions']['percent']['goals'].replace('%',''))
                    bookies = odds_raw['response'][0]['bookmakers'][0]['bets'][0]['values']
                    over_odds = next(float(v['odd']) for v in bookies if v['value'] == 'Over 1.5')
                    
                    # FILTER: Only show high-probability value
                    if prob_pct >= 80 and over_odds <= 1.50:
                        found_any = True
                        h_team = f['teams']['home']['name']
                        a_team = f['teams']['away']['name']
                        
                        # Kelly Logic
                        b = over_odds - 1
                        pr = prob_pct / 100
                        stake = max(0, round(bank * (((b * pr) - (1 - pr)) / b) * 0.25, 2))
                        
                        # THE UPDATED UI CARD
                        st.markdown(f"""
                            <div class="value-card">
                                <span class="update-tag">Last Updated: {datetime.now().strftime('%H:%M:%S')}</span>
                                <small style="color: #00FFA3;">{l_name}</small>
                                <h3 style="margin: 5px 0;">{h_team} vs {a_team}</h3>
                                <p style="margin-bottom: 5px;">
                                    <b>🎯 Confidence: {prob_pct}%</b> | <b>💹 Odds: {over_odds}</b> | <b>💰 Stake: ${stake}</b>
                                </p>
                                <div class="confidence-bar">
                                    <div class="confidence-fill" style="width: {prob_pct}%;"></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # ACTION BUTTONS
                        c1, c2, c3 = st.columns([1,1,2])
                        c1.link_button("🚀 BC.Game", f"https://bc.game/sports/search/{h_team}+vs+{a_team}")
                        c2.link_button("📈 Bet365", f"https://www.google.com/search?q=bet365+{h_team}+vs+{a_team}")
                        with c3.expander("📝 Log"):
                            # Logging logic...
                            pass
                except:
                    continue
        
        if not found_any:
            st.warning("No matches today pass the Over 1.5 Value Filter.")
              
