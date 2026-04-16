import streamlit as st

# --- මූලික දත්ත (Global Data) ---
NAKSHATRAS = [
    "අස්විද", "බෙරණ", "කැති", "රෙහෙන", "මුවසිරස", "අද", 
    "පුනර්වසු", "පුස", "අස්ලීස", "මාඝ", "පුවපල්", 
    "උත්තරපල්", "හත", "සිත", "සාති", "විසා", 
    "අනුර", "දෙට", "මුල", "පුවසල", "උත්තරසල", 
    "සුවණ", "දෙනට", "සියාවස", "පුවපුටුප", 
    "උත්තරපුටුප", "රේවතී"
]

RASHIS = ["මේෂ", "වෘෂභ", "මිථුන", "කටක", "සිංහ", "කන්‍යා", "තුලා", "වෘශ්චික", "ධනු", "මකර", "කුම්භ", "මීන"]

WEEKDAYS = ["ඉරිදා", "සඳුදා", "අඟහරුවාදා", "බදාදා", "බ්‍රහස්පතින්දා", "සිකුරාදා", "සෙනසුරාදා"]

# --- ප්‍රධාන තර්කන පද්ධතිය (Improved Elite Logic) ---

def get_tara_status(birth_idx, target_idx):
    count = (target_idx - birth_idx) % 27
    tara_val = (count % 9) + 1
    tara_data = {
        1: ("ජන්ම", 15), 2: ("සම්පත්", 24), 3: ("විපත්", 0),
        4: ("ක්ෂේම", 20), 5: ("ප්‍රත්‍යාරි", 5), 6: ("සාධක", 28),
        7: ("වධ", 0), 8: ("මෛත්‍රී", 20), 9: ("පරම මෛත්‍රී", 28)
    }
    return tara_data[tara_val]

def calculate_best_slots(b_nak, b_rashi, t_nak, t_rashi, t_tithi, t_day):
    results = []
    for lagna in range(1, 13):
        # 1. පංචක පරීක්ෂාව (Score based - more flexible)
        total_p = t_tithi + t_day + (t_nak + 1) + lagna
        rem_p = total_p % 9
        p_score = 25
        p_status = "පිරිසිදුයි"
        if rem_p in [1, 2, 4, 6, 8]: 
            p_score = 5 # දෝෂ සහිත නම් ලකුණු අඩු කරයි
            p_status = "දෝෂ සහිතයි"
        
        # 2. තාරා බල පරීක්ෂාව (Hard Filter for Vipat/Vadha only)
        tara_v = ((t_nak - b_nak) % 27 % 9) + 1
        if tara_v in [3, 7]: continue 
        
        # 3. චන්ද්‍ර බලය (Flexible range)
        c_pos = (t_rashi - b_rashi) % 12 + 1
        c_scores = {1:25, 3:30, 6:30, 7:25, 10:30, 11:30}
        c_val = c_scores.get(c_pos, 8) # අවම අගය 8 ලෙස සලකයි
        
        # ලකුණු එකතුව
        t_name, t_score = get_tara_status(b_nak, t_nak)
        final_score = min(t_score + c_val + p_score + 15, 100)
        
        results.append({
            "lagna": lagna,
            "score": final_score,
            "tara": t_name,
            "p_info": p_status
        })
    return sorted(results, key=lambda x: x['score'], reverse=True)

# --- පිටු වින්‍යාසය සහ අභිරුචි CSS ---
st.set_page_config(page_title="මුහුර්ථ AI - Elite", page_icon="🔮", layout="centered")

# උඹ දීපු පට්ට CSS ටික මෙතන තියෙනවා
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(145deg, #0f172a 0%, #1e1b4b 100%);
        font-family: 'Segoe UI', sans-serif;
    }
    h1 {
        text-align: center;
        background: linear-gradient(135deg, #FDE68A, #F59E0B);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
    }
    [data-testid="stSidebar"] {
        background: rgba(30, 27, 75, 0.85);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(245, 158, 11, 0.3);
    }
    .streamlit-expanderHeader {
        background: linear-gradient(95deg, #1f2937, #111827);
        border-radius: 20px;
        color: #FDE68A !important;
        border: 1px solid rgba(245,158,11,0.3);
    }
    div.stButton > button {
        background: linear-gradient(90deg, #F59E0B, #D97706);
        color: #0f172a;
        font-weight: bold;
        border-radius: 40px;
        box-shadow: 0 4px 12px rgba(245,158,11,0.4);
    }
    .custom-card {
        background: rgba(31,41,55,0.6);
        backdrop-filter: blur(8px);
        border-radius: 28px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 5px solid #F59E0B;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- පරිශීලක මුහුණත ---

st.title("🔮 අති නවීන ජ්‍යොතිෂ මුහුර්ථ පද්ධතිය")
st.caption("v6.1 · පංචක, තාරා හා චන්ද්‍ර බලය සහිත වෘත්තීය මට්ටමේ ගණනය කිරීම්")
st.markdown("---")

with st.sidebar:
    st.markdown("## 👤 ඔබේ උපන් විස්තර")
    birth_nak = st.selectbox("✨ උපන් නැකත", range(27), format_func=lambda x: NAKSHATRAS[x], index=7)
    birth_rashi = st.selectbox("🌟 උපන් රාශිය", range(12), format_func=lambda x: RASHIS[x], index=4)
    st.markdown("---")
    st.caption("🪷 ඔබේ උපන් නැකත සහ රාශිය නිවැරදිව ඇතුළත් කරන්න.")

st.markdown("## 📅 අදාළ දිනයේ දත්ත")
col1, col2, col3 = st.columns(3, gap="medium")
target_nak = col1.selectbox("🌙 දිනයේ නැකත", range(27), format_func=lambda x: NAKSHATRAS[x])
target_rashi = col2.selectbox("🌝 සඳු සිටින රාශිය", range(12), format_func=lambda x: RASHIS[x])
target_tithi = col3.number_input("📆 තිථිය (1-30)", 1, 30, 10)
target_day = st.selectbox("📅 සතියේ දිනය", range(1, 8), format_func=lambda x: WEEKDAYS[x-1])

st.markdown("---")

if st.button("🔍 සාර්ථක වේලාවන් සොයන්න", use_container_width=True):
    with st.spinner("ගණනය කරමින්..."):
        final_results = calculate_best_slots(birth_nak, birth_rashi, target_nak, target_rashi, target_tithi, target_day)
    
    if not final_results:
        st.error("⚠️ කණගාටුයි! මෙම දිනයේ ඔබට ගැළපෙන කිසිදු සුභ වේලාවක් හමු නොවීය.")
    else:
        st.balloons()
        st.success(f"🎉 ඔබට ගැළපෙන සුභ වේලාවන් **{len(final_results)}** ක් හමුවිය!")
        
        for res in final_results:
            badge = "🏆 අතිශය සුභ" if res['score'] >= 80 else "✨ සුභ" if res['score'] >= 60 else "🍀 මධ්‍යස්ථ"
            with st.expander(f"⭐ ලග්න අංකය: {res['lagna']}  |  සාර්ථකත්වය: {res['score']}%  |  {badge}"):
                c_a, c_b = st.columns(2)
                c_a.markdown(f"**🌟 තාරා බලය:** `{res['tara']}`")
                c_b.markdown(f"**✅ පංචක තත්ත්වය:** {res['p_info']}")
                st.progress(res['score']/100)
        
        # වඩාත්ම සුභ එක (Best Choice)
        best = final_results[0]
        st.markdown(f"""
        <div class="custom-card">
            <h4 style="margin:0; color:#FDE68A;">🏅 නිර්දේශිත හොඳම ලග්න කවුළුව</h4>
            <p style="font-size:1.4rem; font-weight:bold;">ලග්න අංක {best['lagna']} · සාර්ථකත්වය {best['score']}%</p>
            <p>තාරා බලය: {best['tara']} · පංචකය {best['p_info']}</p>
        </div>
        """, unsafe_allow_html=True)
