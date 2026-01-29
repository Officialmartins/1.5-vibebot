import streamlit as st
import pandas as pd
import math
import requests
from datetime import datetime

# --- SECURE CONFIGURATION ---
# This pulls from the 'Secrets' menu on your Streamlit Dashboard
try:
    API_KEY = st.secrets["FOOTBALL_API_KEY"]
except:
    st.error("API Key not found! Please add FOOTBALL_API_KEY to your Streamlit Secrets.")
    st.stop()

BASE_URL = "https://v3.football.api-sports.io/"

# --- MATH ENGINES ---
def poisson_probability(lmbda, x):
    return (math.exp(-lmbda) * (lmbda**x)) / math.factorial(x)

def get_o15_prob(h_exp, a_exp):
    p00 = poisson_probability(h_exp, 0) * poisson_probability(a_exp, 0)
    p10 = poisson_probability(h_exp, 1) * poisson_probability(a_exp, 0)
    p01 = poisson_probability(h_exp, 0) * poisson_probability(a_exp, 1)
    return round((1 - (p00 + p10 + p01)) * 100, 2)

def get_kelly_stake(bank, odds, prob_pct):
    b, p = odds - 1, prob_pct / 100
    q = 1 - p
    f_star = (b * p - q) / b if b > 0 else 0
    return max(0, round(bank * f_star * 0.25, 2)) if f_star > 0 else 0

# --- APP SETUP ---
st.set_page_config(page_title="VibeBot Elite", layout="wide", page_icon="⚽")

if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'Match', 'Odds', 'Stake', 'Result', 'Profit'])

# --- SIDEBAR ---
with st.sidebar:
    st.title("💰 Bankroll Manager")
    bank = st.number_input("Total Wallet ($)", value=1000.0)
    
    if not st.session_state.history.empty:
        total_pnl = st.session_state.history['Profit'].sum()
        st.metric("Session P&L", f"${total_pnl:.2f}", delta=f"{total_pnl:.2f}")
        
        csv = st.session_state.history.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Betting Log", data=csv, file_name=f"bets_{datetime.now().strftime('%d-%m')}.csv")

# --- MAIN APP ---
st.title("⚽ Over 1.5 Value Hunter")
st.info("England: Premier League, Championship, League One")

if st.button("🚀 Scan English Leagues for Value"):
    with st.spinner("Crunching Poisson data..."):
        # Note: In a live environment, you would use requests.get() here to fetch live fixtures
        # and team stats to calculate real home_exp and away_exp.
        matches = [
            {"id": 1, "match": "Burnley vs Hull", "h_exp": 1.9, "a_exp": 1.4, "odds": 1.35},
            {"id": 2, "match": "Everton vs Leicester", "h_exp": 1.8, "a_exp": 1.7, "odds": 1.28},
            {"id": 3, "match": "Reading vs Bolton", "h_exp": 1.4, "a_exp": 1.3, "odds": 1.48}
        ]
        
        for m in matches:
            prob = get_o15_prob(m['h_exp'], m['a_exp'])
            if prob >= 85 and m['odds'] <= 1.50:
                stake = get_kelly_stake(bank, m['odds'], prob)
                
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.subheader(m['match'])
                        q = m['match'].replace(' vs ', '+')
                        st.markdown(f"[🚀 BC.Game](https://bc.game/sports/search/{q}) | [📈 Bet365](https://www.google.com/search?q=bet365+{q}+odds)")
                    col2.metric("Confidence", f"{prob}%")
                    col3.metric("Stake", f"${stake}")
                    
                    with st.expander("📝 Log Result"):
                        with st.form(key=f"f_{m['id']}"):
                            res = st.radio("Outcome", ["Win", "Loss"], horizontal=True)
                            if st.form_submit_button("Confirm"):
                                profit = (stake * m['odds']) - stake if res == "Win" else -stake
                                entry = pd.DataFrame([{'Time': datetime.now().strftime("%H:%M"), 'Match': m['match'], 'Odds': m['odds'], 'Stake': stake, 'Result': res, 'Profit': profit}])
                                st.session_state.history = pd.concat([st.session_state.history, entry], ignore_index=True)
                                st.rerun()

st.divider()
st.subheader("📊 Session History")
st.dataframe(st.session_state.history, use_container_width=True)
          
