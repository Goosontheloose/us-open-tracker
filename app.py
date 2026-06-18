import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

# The specific secret name you requested
API_KEY = st.secrets["api_key"]

# --- DATA RAW INPUT ---
RAW_EXCEL_DATA = """
Martin	Bryson DeChambeau	Scottie Scheffler	Rory McIlroy
Wynand	Patrick Cantlay	Xander Schauffele	Ludvig Aberg
Rupert	Collin Morikawa	Hideki Matsuyama	Brooks Koepka
Frederik	Jordan Spieth	Viktor Hovland	Tommy Fleetwood
"""

# --- DATA ENGINE ---
@st.cache_data(ttl=600)
def get_data():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    # Using 2024 US Open Data
    params = {"orgId":"1", "tournId":"026", "year":"2024"}
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json().get('leaderboardRows', [])

def run_app():
    rows = get_data()
    
    # 1. Create simple score lookup
    scores = {}
    for r in rows:
        name = f"{r.get('firstName')} {r.get('lastName')}".strip().lower()
        # Ensure the score is a number, not a string or None
        try:
            val = int(r.get('toParValue', 0))
        except:
            val = 0
        scores[name] = val

    # 2. Calculate Team Totals
    final_results = []
    for line in RAW_EXCEL_DATA.strip().split('\n'):
        parts = line.split('\t')
        user = parts[0]
        picks = parts[1:]
        
        total = 0
        for p in picks:
            total += scores.get(p.lower(), 0)
            
        final_results.append({"User": user, "Total": total})

    # 3. Display Leaderboard
    st.title("🏆 THE SYNDICATE DERBY")
    df = pd.DataFrame(final_results).sort_values("Total")
    
    # Simple table output that worked yesterday
    st.table(df)

run_app()
st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')}")
