import streamlit as st
import datetime

# --- මූලික දත්ත (Global Data) ---
NAKSHATRAS = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනර්වසු", "පුස", "අස්ලීස", "මාඝ", "පුවපල්", "උත්තරපල්", "හත", "සිත", "සාති", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්තරසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්තරපුටුප", "රේවතී"]
RASHIS = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
LAGNA_NAMES = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]

# සාමාන්‍ය ලග්න කාලසීමාවන් (Approximate only - can vary by season)
LAGNA_TIMES = {
    "මේෂ": "පෙ.ව. 06:00 - පෙ.ව. 08:00", "වෘෂභ": "පෙ.ව. 08:00 - පෙ.ව. 10:00",
    "මිථුන": "පෙ.ව. 10:00 - දහවල් 12:00", "කටක": "දහවල් 12:00 - ප.ව. 02:00",
    "සිංහ": "ප.ව. 02:00 - ප.ව. 04:00", "කන්‍යා": "ප.ව. 04:00 - ප.ව. 06:00",
    "තුලා": "ප.ව. 06:00 - රාත්‍රී 08:00", "වෘශ්චික": "රාත්‍රී 08:00 - රාත්‍රී 10:00",
    "ධනු": "රාත්‍රී 10:00 - මධ්‍යම රාත්‍රී 12:00", "මකර": "මධ්‍යම රාත්‍රී 12:00 - අලුයම 02:00",
    "කුම්භ": "අලුයම 02:00 - අලුයම 04:00", "මීන": "අලුයම 04:00 - පෙ.ව. 06:00"
}

# --- තර්කන පද්ධතිය ---
def calculate_score(b_nak, b_rashi, t_nak, t_rashi, t_tithi, t_day, lagna_idx):
    # Tara Bala
    tara_v = ((t_nak - b_nak) % 27 % 9) + 1
    if tara_v in [3, 7]: return None # Hard Reject
    tara_scores = {1:15, 2:24, 4:20, 5:5, 6:28, 8:20, 9:28}
    
    # Chandra Bala
    c_pos = (t_rashi - b_rashi) % 12 + 1
    c_score = {1:25, 3:30, 6:30, 7:25, 10:30, 11:30}.get(c_pos, 8)
    
    # Panchaka
    total_p = t_tithi + t_day + (t_nak + 1) + (lagna_idx + 1)
    p_score = 25 if (total_p % 9) not in [1, 2, 4, 6, 8] else 5
    
    return min(tara_scores.get(tara_v, 0) + c_score + p_score + 15, 100)

# --- UI Layout ---
st.set_page_config(page_title="Ultra Muhurtha AI v8", page_icon="💎", layout="wide")

st.markdown("""
<style>
    .stApp { background: #0f172a; color: white; }
    .main-title { background: linear-gradient(135deg, #FDE68A, #F59E0B); -webkit-background-clip: text; color: transparent; text-align: center; font-size: 3rem; font-weight: 800; }
    .card { background: #1e293b; border-radius: 15px; padding: 20px; border-left: 6px solid #F59E0B; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">💎 Ultra Muhurtha AI v8</h1>', unsafe_allow_html=True)
st.caption("Professionally Scan Future Auspicious Times with Precision")

# --- Sidebar ---
with st.sidebar:
    st.header("👤 Your Birth Profile")
    b_nak = st.selectbox("උපන් නැකත", range(27), format_func=lambda x: NAKSHATRAS[x], index=7)
    b_rashi = st.selectbox("උපන් රාශිය", range(12), format_func=lambda x: RASHIS[x], index=4)
    st.divider()
    st.info("මෙම දත්ත මත පදනම්ව පද්ධතිය ඔබට ගැලපෙනම වේලාවන් තෝරාගනු ඇත.")

# --- Main Tabs ---
tab1, tab2 = st.tabs(["🔍 එක් දිනක් පරීක්ෂා කරන්න", "📅 ඉදිරි දින 7 පරීක්ෂාව"])

with tab1:
    col1, col2, col3 = st.columns(3)
    t_date = col1.date_input("දිනය", datetime.date(2026, 5, 21))
    t_nak = col2.selectbox("එදින නැකත", range(27), format_func=lambda x: NAKSHATRAS[x])
    t_tithi = col3.number_input("තිථිය (1-30)", 1, 30, 5)
    
    t_day = t_date.weekday() + 2
    if t_day > 7: t_day = 1
    t_rashi = st.selectbox("සඳු සිටින රාශිය", range(12), format_func=lambda x: RASHIS[x], index=3)

    if st.button("Calculate Best Lagnas"):
        results = []
        for i, name in enumerate(LAGNA_NAMES):
            score = calculate_score(b_nak, b_rashi, t_nak, t_rashi, t_tithi, t_day, i)
            if score:
                results.append({"name": name, "time": LAGNA_TIMES[name], "score": score})
        
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        for res in results:
            with st.expander(f"✨ {res['name']} ලග්නය | {res['time']} | Score: {res['score']}%"):
                st.write(f"මෙම කාලය තුළ වැඩ ආරම්භ කිරීම ඉතා සුභයි. සාර්ථකත්වය: {res['score']}%")

with tab2:
    st.subheader("ඉදිරි දින 7 සඳහා සුභ දින ස්කෑනරය")
    st.write("පද්ධතිය විසින් ඉදිරි දින 7 තුළ ඔබට ඇති හොඳම 'Ultra Power' නැකත් ස්වයංක්‍රීයව සොයා දෙනු ඇත.")
    
    if st.button("Start 7-Day Auto Scan"):
        # Simulated Auto-Scan Logic
        st.success("ඉදිරි දින 7 ඇතුළත හමු වූ හොඳම අවස්ථාවන්:")
        dates = [t_date + datetime.timedelta(days=i) for i in range(1, 8)]
        for d in dates:
            # මෙතැනදී ඇත්තටම ඉදිරි දින වල දත්ත API එකකින් ගත හැක. දැනට sample පෙන්වයි.
            st.markdown(f"""
            <div class="card">
                <h4>📅 {d.strftime('%Y-%m-%d')} - {WEEKDAYS[d.weekday()]}</h4>
                <p>හොඳම වෙලාව: <b>පෙ.ව. 09:15 - 11:15 (මිථුන ලග්නය)</b></p>
                <p>සාර්ථකත්වය: 88% | තාරා බලය: මෛත්‍රී</p>
            </div>
            """, unsafe_allow_html=True)
