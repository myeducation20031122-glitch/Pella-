import streamlit as st
import datetime

# --- මූලික දත්ත ---
NAKSHATRAS = ["අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", "පුනර්වසු", "පුස", "අස්ලීස", "මාඝ", "පුවපල්", "උත්තරපල්", "හත", "සිත", "සාති", "විසා", "අනුර", "දෙට", "මුල", "පුවසල", "උත්තරසල", "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", "උත්තරපුටුප", "රේවතී"]
RASHIS = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]
WEEKDAYS = ["ඉරිදා", "සඳුදා", "අඟහරුවාදා", "බදාදා", "බ්‍රහස්පතින්දා", "සිකුරාදා", "සෙනසුරාදා"]
TITHIS = [f"{i} - {'පුර' if i<=15 else 'අව'} පස" for i in range(1, 31)]

# --- Elite Logic v7 ---

def get_tara_status(birth_idx, target_idx):
    count = (target_idx - birth_idx) % 27
    tara_val = (count % 9) + 1
    tara_data = {
        1: ("ජන්ම", 15), 2: ("සම්පත්", 24), 3: ("විපත්", 0), 4: ("ක්ෂේම", 20),
        5: ("ප්‍රත්‍යාරි", 5), 6: ("සාධක", 28), 7: ("වධ", 0), 8: ("මෛත්‍රී", 20), 9: ("පරම මෛත්‍රී", 28)
    }
    return tara_data[tara_val]

def calculate_best_slots(b_nak, b_rashi, t_nak, t_rashi, t_tithi, t_day):
    results = []
    for lagna in range(1, 13):
        total_p = t_tithi + t_day + (t_nak + 1) + lagna
        rem_p = total_p % 9
        p_score = 25 if rem_p not in [1, 2, 4, 6, 8] else 5
        
        tara_v = ((t_nak - b_nak) % 27 % 9) + 1
        if tara_v in [3, 7]: continue 
        
        c_pos = (t_rashi - b_rashi) % 12 + 1
        c_score = {1:25, 3:30, 6:30, 7:25, 10:30, 11:30}.get(c_pos, 8)
        
        t_name, t_score = get_tara_status(b_nak, t_nak)
        final_score = min(t_score + c_score + p_score + 15, 100)
        
        # Golden Minute Calculation (පළමු විනාඩි 20-40 අතර කාලය සාමාන්‍යයෙන් සුභයි)
        results.append({
            "lagna": lagna,
            "score": final_score,
            "tara": t_name,
            "p_info": "පිරිසිදුයි" if p_score == 25 else "දෝෂ සහිතයි",
            "golden_window": "ලග්නය ආරම්භ වී විනාඩි 15 ත් 45 ත් අතර"
        })
    return sorted(results, key=lambda x: x['score'], reverse=True)

# --- UI Styling ---
st.set_page_config(page_title="මුහුර්ථ AI - Pro Master", page_icon="🔮", layout="centered")

st.markdown("""
<style>
    .stApp { background: linear-gradient(145deg, #0f172a 0%, #1e1b4b 100%); color: white; }
    h1 { text-align: center; background: linear-gradient(135deg, #FDE68A, #F59E0B); -webkit-background-clip: text; color: transparent; font-weight: 800; }
    .custom-card { background: rgba(31,41,55,0.7); border-radius: 20px; padding: 20px; border-left: 5px solid #F59E0B; margin-bottom: 10px; }
    div.stButton > button { background: linear-gradient(90deg, #F59E0B, #D97706); border-radius: 30px; font-weight: bold; width: 100%; height: 50px; }
</style>
""", unsafe_allow_html=True)

st.title("🔮 මුහුර්ථ AI - Pro Master v7")
st.caption("තිථිය හා විනාඩිය දක්වා නිවැරදි ජ්‍යොතිෂ තීරණ පද්ධතිය")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("👤 ඔබේ උපන් විස්තර")
    birth_nak = st.selectbox("උපන් නැකත", range(27), format_func=lambda x: NAKSHATRAS[x], index=7)
    birth_rashi = st.selectbox("උපන් රාශිය", range(12), format_func=lambda x: RASHIS[x], index=4)
    st.divider()
    st.info("💡 දැනට තිථිය හා නැකත ලිතකින් බලා ඇතුළත් කරන්න. ඉදිරි update එකේදී මෙය auto-calculate වනු ඇත.")

# --- Main Inputs ---
st.markdown("### 📅 දිනය හා වේලාව සැකසුම්")
c1, c2 = st.columns(2)
with c1:
    target_date = st.date_input("වැඩේ කරන්න හිතාගෙන ඉන්න දිනය", datetime.date(2026, 5, 21))
    target_nak = st.selectbox("එදිනට අදාළ නැකත", range(27), format_func=lambda x: NAKSHATRAS[x])
with c2:
    tithi_val = st.selectbox("එදිනට අදාළ තිථිය", range(1, 31), format_func=lambda x: TITHIS[x-1])
    target_rashi = st.selectbox("එදින සඳු සිටින රාශිය", range(12), format_func=lambda x: RASHIS[x])

# Auto-get weekday
target_day = target_date.weekday() + 2 # Adjusting for astrology indices
if target_day > 7: target_day = 1

if st.button("🔍 සුභම මොහොත සොයන්න"):
    results = calculate_best_slots(birth_nak, birth_rashi, target_nak, target_rashi, tithi_val, target_day)
    
    if not results:
        st.error("⚠️ මෙම දිනයේ අසුභ තාරා බලපෑම් ඇති බැවින් සුභ වේලාවන් නිර්දේශ කළ නොහැක.")
    else:
        st.balloons()
        st.success(f"ඔබට ගැළපෙන සුභ ලග්න කවුළු {len(results)} ක් හමුවිය.")
        
        for res in results[:5]: # Show top 5
            with st.expander(f"⭐ ලග්න අංකය {res['lagna']} - සාර්ථකත්වය {res['score']}%"):
                st.markdown(f"""
                <div class="custom-card">
                    <p><b>🌟 තාරා බලය:</b> {res['tara']}</p>
                    <p><b>✅ පංචකය:</b> {res['p_info']}</p>
                    <p style="color:#FDE68A;"><b>⏱️ හොඳම විනාඩි (The Golden Minute):</b> {res['golden_window']}</p>
                    <small>මෙම ලග්න කාලය ආරම්භ වූ සැණින් වැඩ කටයුතු ඇරඹීම ඉතා සුභයි.</small>
                </div>
                """, unsafe_allow_html=True)
