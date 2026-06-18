import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

# Secure API Key - exactly as requested
try:
    API_KEY = st.secrets["api_key"]
except KeyError:
    st.error("Secret 'api_key' not found. Please add it to your Streamlit Cloud settings.")
    st.stop()

# --- CHAMPIONSHIP BRUTALISM CSS (Restored) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    .stApp { background-color: #F5F5F4; }
    
    .podium-card {
        padding: 1.5rem;
        border: 4px solid #064E3B;
        background-color: white;
        box-shadow: 6px 6px 0px #064E3B;
        margin-bottom: 20px;
    }

    .podium-score {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        color: #064E3B;
        font-size: clamp(2.5rem, 8vw, 4.5rem);
        line-height: 1;
    }

    .podium-card *, .full-field-row * { color: #064E3B !important; }

    @media (max-width: 767px) {
        .stColumn { margin-bottom: 12px; }
        .podium-card { padding: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- USER DATA ---
RAW_EXCEL_DATA = """
Martin	Bryson DeChambeau	Scottie Scheffler	Rory McIlroy
Wynand	Patrick Cantlay	Xander Schauffele	Ludvig Aberg
Rupert	Collin Morikawa	Hideki Matsuyama	Brooks Koepka
Frederik	Jordan Spieth	Viktor Hovland	Tommy Fleetwood
"""

# --- DATA ENGINE ---
@st.cache_data(ttl=600)
def get_leaderboard():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    # Testing with 2024 US Open (Tourn 026)
    params = {"orgId":"1", "tournId":"026", "year":"2024"}
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, params=params)
        return r.json().get('leaderboardRows', [])
    except:
        return []

def run_app():
    rows = get_leaderboard()
    
    # 1. Map Player Names to Scores (Fuzzy Match included)
    pro_data = {}
    for r in rows:
        f = r.get('firstName', '')
        l = r.get('lastName', '')
        full = f"{f} {l}".strip().lower()
        
        # Capture the score - handle 'E' or None safely
        raw_score = r.get('toParValue')
        try:
            val = int(raw_score) if raw_score is not None else 0
        except:
            val = 0
            
        pro_data[full] = {"score": val, "thru": r.get('thru', 'F')}

    # 2. Process Teams
    league_results = []
    all_picks = []
    
    for line in RAW_EXCEL_DATA.strip().split('\n'):
        parts = line.split('\t')
        user = parts[0]
        picks = parts[1:]
        all_picks.extend(picks)
        
        u_total = 0
        u_details = []
        
        for pick in picks:
            # Match the pick name to the API name
            match = pro_data.get(pick.lower(), {"score": 0, "thru": "-"})
            s = match['score']
            u_total += s
            
            # Format display
            sign = "+" if s > 0 else ""
            txt = "E" if s == 0 else f"{sign}{s}"
            u_details.append(f"{pick} {txt} [{match['thru']}]")
            
        league_results.append({
            "User": user, 
            "Total": u_total, 
            "Picks": u_details
        })

    df = pd.DataFrame(league_results).sort_values("Total")
    
    # --- RENDER UI ---
    st.title("🏆 THE SYNDICATE DERBY")
    
    # Top 3 Podium
    st.markdown("### 🥇 CHAMPIONSHIP FLIGHT")
    cols = st.columns(3)
    for i, (_, row) in enumerate(df.head(3).iterrows()):
        with cols[i]:
            score_disp = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
            st.markdown(f"""
                <div class="podium-card">
                    <div style="font-weight:900;">#{i+1} {row['User']}</div>
                    <div class="podium-score">{score_disp}</div>
                    <div style="font-size:0.85rem; line-height:1.4;">{"<br>".join(row['Picks'])}</div>
                </div>
            """, unsafe_allow_html=True)

    # Tabs
    tab1, tab2 = st.tabs(["📊 FULL STANDINGS", "🎯 MARKET SENTIMENT"])
    
    with tab1:
        # Beautifully simple table
        display_df = df[["User", "Total"]].copy()
        display_df["Total"] = display_df["Total"].apply(lambda x: f"+{x}" if x > 0 else ("E" if x == 0 else x))
        st.table(display_df)

    with tab2:
        st.markdown("### MOST PICKED PLAYERS")
        counts = pd.Series(all_picks).value_counts().reset_index()
        counts.columns = ['Player', 'Selections']
        st.bar_chart(data=counts, x='Player', y='Selections', color="#064E3B")

    # Debug Section (Fixed so it doesn't crash)
    with st.expander("🛠️ DEBUG: ENGINE ROOM"):
        if rows:
            st.write("First few names in API database:")
            debug_list = [f"{r.get('firstName')} {r.get('lastName')} | Score: {r.get('toParValue')}" for r in rows[:10]]
            st.write(debug_list)
        else:
            st.write("No API data received.")

run_app()
st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')}")
