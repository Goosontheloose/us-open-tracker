import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. CORE SETUP
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

# API Key - Using the exact key name from your secrets
try:
    API_KEY = st.secrets["api_key"]
except:
    st.error("API Key not found in Streamlit Secrets.")
    st.stop()

# 2. CHAMPIONSHIP BRUTALISM CSS (Restored & Fixed for Mobile)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    .stApp { background-color: #F5F5F4; }
    
    .podium-card {
        padding: 1.5rem;
        border: 4px solid #064E3B;
        background-color: white;
        box-shadow: 8px 8px 0px #064E3B;
        margin-bottom: 25px;
    }

    .podium-score {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        color: #064E3B;
        font-size: clamp(3rem, 10vw, 5rem);
        line-height: 1;
        margin: 10px 0;
    }

    .user-name {
        font-family: 'Inter', sans-serif;
        text-transform: uppercase;
        font-weight: 900;
        color: #064E3B;
    }

    .player-row {
        font-size: 0.85rem;
        color: #111;
        border-bottom: 1px solid #ddd;
        padding: 5px 0;
        display: flex;
        justify-content: space-between;
    }

    @media (max-width: 767px) {
        .podium-card { padding: 1rem; box-shadow: 4px 4px 0px #064E3B; }
        .podium-score { font-size: 3.5rem; }
    }
</style>
""", unsafe_allow_html=True)

# 3. USER DATA
RAW_EXCEL_DATA = """
Martin	Bryson DeChambeau	Scottie Scheffler	Rory McIlroy
Wynand	Patrick Cantlay	Xander Schauffele	Ludvig Aberg
Rupert	Collin Morikawa	Hideki Matsuyama	Brooks Koepka
Frederik	Jordan Spieth	Viktor Hovland	Tommy Fleetwood
"""

# 4. DATA ENGINE (No experiments, just the data)
@st.cache_data(ttl=600)
def get_data():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId":"1", "tournId":"026", "year":"2024"}
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        r = requests.get(url, headers=headers, params=params)
        return r.json().get('leaderboardRows', [])
    except:
        return []

def main():
    rows = get_data()
    
    # Map API data to a simple lookup dictionary
    pro_lookup = {}
    for r in rows:
        name = f"{r.get('firstName', '')} {r.get('lastName', '')}".strip().lower()
        
        # Robust Score Handling
        raw_score = r.get('toParValue')
        try:
            score_int = int(raw_score) if raw_score is not None else 0
        except:
            score_int = 0
            
        pro_lookup[name] = {
            "score": score_int,
            "thru": r.get('thru', 'F')
        }

    # Process Syndicate Teams
    leaderboard = []
    all_picks = []
    
    for line in RAW_EXCEL_DATA.strip().split('\n'):
        parts = line.split('\t')
        user = parts[0]
        picks = parts[1:]
        all_picks.extend(picks)
        
        team_total = 0
        team_html = ""
        
        for p in picks:
            data = pro_lookup.get(p.lower(), {"score": 0, "thru": "-"})
            s = data['score']
            team_total += s
            
            score_str = "E" if s == 0 else f"{'+' if s > 0 else ''}{s}"
            team_html += f'<div class="player-row"><span>{p}</span><span><b>{score_str}</b> [{data["thru"]}]</span></div>'
            
        leaderboard.append({"User": user, "Total": team_total, "HTML": team_html})

    df = pd.DataFrame(leaderboard).sort_values("Total")

    # 5. UI RENDERING
    st.markdown("<h1 style='color:#064E3B; font-family:Inter; font-weight:900;'>🏆 THE SYNDICATE DERBY</h1>", unsafe_allow_html=True)
    
    # Top 3 Cards
    cols = st.columns(3)
    for i, (_, row) in enumerate(df.head(3).iterrows()):
        with cols[i]:
            total_disp = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
            st.markdown(f"""
                <div class="podium-card">
                    <div class="user-name">#{i+1} {row['User']}</div>
                    <div class="podium-score">{total_disp}</div>
                    <div>{row['HTML']}</div>
                </div>
            """, unsafe_allow_html=True)

    # Standings & Ownership Tabs
    tab1, tab2 = st.tabs(["📊 STANDINGS", "🎯 MARKET SENTIMENT"])
    
    with tab1:
        final_df = df[["User", "Total"]].copy()
        final_df["Total"] = final_df["Total"].apply(lambda x: f"+{x}" if x > 0 else ("E" if x == 0 else x))
        st.table(final_df.set_index("User"))

    with tab2:
        st.markdown("### MOST PICKED PLAYERS")
        counts = pd.Series(all_picks).value_counts().reset_index()
        counts.columns = ['Player', 'Picks']
        st.bar_chart(data=counts, x='Player', y='Picks', color="#064E3B")

if __name__ == "__main__":
    main()
    st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')}")
