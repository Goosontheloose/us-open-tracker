
import streamlit as st
import requests
import pandas as pd

# ==========================================
# 1. CONFIGURATION & SCALING
# ==========================================
st.set_page_config(page_title="US Open: The Syndicate Derby", layout="wide")

# API Setup
API_KEY = st.secrets["api_key"]
URL = "https://live-golf-data.p.rapidapi.com/leaderboard"

# Tournament Parameters (Set to 2024 for testing, update to 2026 when live)
PARAMS = {"orgId": "1", "tournId": "026", "year": "2024"} 
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}

# ==========================================
# 2. THE SYNDICATE DATA (Paste your 100 people here)
# ==========================================
RAW_EXCEL_DATA = """
Frederik	Bryson DeChambeau	Russel Henley	Colin Morikawa
Wynand	Rory Mcllroy	Sam Burns	Tommy Fleetwood
Jason	Tony Finau	Corey Connors	Akshay Bhatia
Martin	Patrick Cantlay	Thomas Detry	Sergio Garcia
Frederik  2	Thomas Detry	Sam Burns	Corey Connors
Jason 2	Bryson DeChambeau	Thomas Detry	Sergio Garcia
Wynand 2	Patrick Cantlay	Tony Finau	Akshay Bhatia
Martin 2	Tony Finau	Tommy Fleetwood	Russel Henley
Rupert	Patrick Cantlay	Tony Finau	Tommy Fleetwood
Rupert 3	Akshay Bhatia	Sergio Garcia	Bryson DeChambeau

""" # Add all 100 names here following this tab-separated format

# ==========================================
# 3. CHAMPIONSHIP BRUTALISM STYLING
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&family=JetBrains+Mono:wght@500&display=swap');
    
    :root {
        --fairway: #064E3B;
        --gold: #EAB308;
        --bunker: #F5F5F4;
    }

    .stApp { background-color: var(--bunker); background-image: radial-gradient(#000 1px, transparent 0); background-size: 30px 30px; }
    
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; font-weight: 900 !important; text-transform: uppercase; color: #000; }
    
    .podium-card {
        background: white;
        border: 4px solid #000;
        padding: 25px;
        box-shadow: 10px 10px 0px #000;
        margin-bottom: 30px;
    }

    .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 3rem; font-weight: bold; }
    
    .marquee {
        background: var(--fairway);
        color: var(--gold);
        padding: 10px 0;
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        border-bottom: 4px solid #000;
        margin-bottom: 40px;
    }
    
    .player-row {
        background: white;
        border: 2px solid #000;
        padding: 10px 20px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. CORE ENGINE (API & LOGIC)
# ==========================================

@st.cache_data(ttl=600) # Refreshes every 10 minutes to save API credits
def get_live_scores():
    try:
        response = requests.get(URL, headers=HEADERS, params=PARAMS)
        data = response.json()
        rows = data.get('leaderboardRows', [])
        
        score_map = {}
        for r in rows:
            name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower()
            score = r.get('toParValue', 0)
            if score == "E": score = 0
            score_map[name] = int(score)
        return score_map, rows
    except Exception as e:
        st.error(f"Engine Failure: {e}")
        return {}, []

def parse_syndicate_teams(raw_data):
    teams = []
    lines = raw_data.strip().split('\n')
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 4:
            teams.append({
                "owner": parts[0],
                "players": [p.strip().lower() for p in parts[1:4]]
            })
    return teams
# ==========================================
# 5. PRO MASTER BOARD (REPAIRED & ROBUST)
# ==========================================
with st.expander("📊 VIEW OFFICIAL TOURNAMENT MASTER BOARD"):
    st.write("Live Professional Field at Shinnecock Hills")
    
    if pro_rows and len(pro_rows) > 0:
        # Create the dataframe
        pro_df = pd.DataFrame(pro_rows)
        
        # Define the columns we want to show
        target_cols = ['position', 'firstName', 'lastName', 'thru', 'toParValue']
        
        # Only select columns that actually exist in the API response
        available_cols = [col for col in target_cols if col in pro_df.columns]
        
        if available_cols:
            display_df = pro_df[available_cols]
            st.table(display_df)
        else:
            st.warning("Data found, but expected columns are missing. Showing raw data instead.")
            st.write(pro_df.head())
    else:
        st.error("No professional leaderboard data found. Check your API connection in the 'Engine Room' below.")

