import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. SETTINGS ---
st.set_page_config(page_title="The Syndicate Derby", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
    .stApp { background-color: #F5F5F4; }
    .podium-card { padding: 1.2rem; border: 4px solid #064E3B; background-color: white; box-shadow: 8px 8px 0px #064E3B; margin-bottom: 20px; }
    .podium-score { font-family: 'Inter', sans-serif; font-weight: 900; color: #064E3B; font-size: clamp(2.5rem, 8vw, 4.5rem); line-height: 1; margin: 5px 0; }
    .user-name { font-family: 'Inter', sans-serif; text-transform: uppercase; font-weight: 900; color: #064E3B; font-size: 1.1rem; }
    .player-row { font-size: 0.85rem; display: flex; justify-content: space-between; border-bottom: 1px solid #eee; padding: 4px 0; }
</style>
""", unsafe_allow_html=True)

RAW_EXCEL_DATA = """
Martin	Bryson DeChambeau	Scottie Scheffler	Rory McIlroy
Wynand	Patrick Cantlay	Xander Schauffele	Ludvig Aberg
Rupert	Collin Morikawa	Hideki Matsuyama	Brooks Koepka
Frederik	Jordan Spieth	Viktor Hovland	Tommy Fleetwood
"""

# --- 2. DATA FETCHING ---
@st.cache_data(ttl=600)
def get_leaderboard():
    url = "https://live-golf-data.p.rapidapi.com/leaderboard"
    params = {"orgId":"1", "tournId":"026", "year":"2024"}
    headers = {"X-RapidAPI-Key": st.secrets["api_key"], "X-RapidAPI-Host": "live-golf-data.p.rapidapi.com"}
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get('leaderboardRows', [])
    except Exception as e:
        st.error(f"API Error: {e}")
        return []

def run_app():
    api_data = get_leaderboard()
    
    # 3. BUILD A CLEAN PLAYER MAP
    master_scores = {}
    for row in api_data:
        full_name = f"{row.get('firstName', '')} {row.get('lastName', '')}".strip().lower()
        # Use toParValue (integer) if it exists, otherwise try to parse toPar string
        raw_score = row.get('toParValue')
        if raw_score is None:
            tp = str(row.get('toPar', '0')).upper()
            raw_score = 0 if tp == 'E' or tp == '' else int(tp.replace('+', ''))
        
        master_scores[full_name] = {
            "score": int(raw_score),
            "thru": row.get('thru', '-')
        }

    # 4. PROCESS TEAMS WITH FUZZY MATCHING
    results = []
    match_diagnostics = []

    for line in RAW_EXCEL_DATA.strip().split('\n'):
        parts = line.split('\t')
        user = parts[0]
        picks = parts[1:]
        
        total_score = 0
        html_details = []
        
        for pick in picks:
            pick_clean = pick.strip().lower()
            found_data = None
            
            # Look for the pick in our master list (Fuzzy Match)
            for api_name, data in master_scores.items():
                if pick_clean in api_name or api_name in pick_clean:
                    found_data = data
                    match_diagnostics.append({"Pick": pick, "Status": "✅ Found", "Matched As": api_name})
                    break
            
            if not found_data:
                found_data = {"score": 0, "thru": "N/A"}
                match_diagnostics.append({"Pick": pick, "Status": "❌ NOT FOUND", "Matched As": "None"})

            s = found_data['score']
            total_score += s
            s_str = "E" if s == 0 else f"{'+' if s > 0 else ''}{s}"
            html_details.append(f'<div class="player-row"><span>{pick}</span><span><b>{s_str}</b> [{found_data["thru"]}]</span></div>')
            
        results.append({"User": user, "Total": total_score, "HTML": "".join(html_details)})

    # --- 5. UI DISPLAY ---
    df = pd.DataFrame(results).sort_values("Total")
    st.markdown("<h1 style='color:#064E3B; font-family:Inter; font-weight:900;'>🏆 THE SYNDICATE DERBY</h1>", unsafe_allow_html=True)

    cols = st.columns(3)
    for i, (_, row) in enumerate(df.head(3).iterrows()):
        with cols[i]:
            disp = "E" if row['Total'] == 0 else f"{'+' if row['Total'] > 0 else ''}{row['Total']}"
            st.markdown(f"""
                <div class="podium-card">
                    <div class="user-name">#{i+1} {row['User']}</div>
                    <div class="podium-score">{disp}</div>
                    {row['HTML']}
                </div>
            """, unsafe_allow_html=True)

    st.markdown("### FULL STANDINGS")
    st.table(df[["User", "Total"]].set_index("User"))

    # --- 6. TRUTH CHECK ---
    with st.expander("🛠 DATA MATCHING STATUS (Check here if scores are 'E')"):
        st.write("This shows if the app successfully connected your Excel names to the live API names.")
        st.table(pd.DataFrame(match_diagnostics))

run_app()
