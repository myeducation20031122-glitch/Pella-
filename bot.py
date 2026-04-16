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

# --- ප්‍රධාන තර්කන පද්ධතිය (Elite Logic) ---

def get_tara_status(birth_idx, target_idx):
    count = (target_idx - birth_idx) % 27
    tara_val = (count % 9) + 1
    # තාරා බලය සහ ලකුණු (0-30)
    tara_data = {
        1: ("ජන්ම", 15), 2: ("සම්පත්", 24), 3: ("විපත්", 0),
        4: ("ක්ෂේම", 20), 5: ("ප්‍රත්‍යාරි", 5), 6: ("සාධක", 28),
        7: ("වධ", 0), 8: ("මෛත්‍රී", 20), 9: ("පරම මෛත්‍රී", 28)
    }
    return tara_data[tara_val]

def calculate_best_slots(b_nak, b_rashi, t_nak, t_rashi, t_tithi, t_day):
    results = []
    for lagna in range(1, 13):
        # 1. පංචක පරීක්ෂාව (Panchaka Hard Filter)
        total_p = t_tithi + t_day + (t_nak + 1) + lagna
        rem_p = total_p % 9
        if rem_p in [1, 2, 4, 6, 8]: continue 
        
        # 2. තාරා බල පරීක්ෂාව (Tara Hard Filter)
        tara_v = ((t_nak - b_nak) % 27 % 9) + 1
        if tara_v in [3, 7]: continue 
        
        # 3. චන්ද්‍ර බලය (Moon Strength)
        c_pos = (t_rashi - b_rashi) % 12 + 1
        c_scores = {1:25, 3:30, 6:30, 7:25, 10:30, 11:30}
        c_score = c_scores.get(c_pos, 5)
        
        if c_score <= 5: continue # චන්ද්‍ර බලය දුර්වල නම් ඉවත් කරයි
        
        # ලකුණු එකතුව
        t_name, t_score = get_tara_status(b_nak, t_nak)
        final_score = min(t_score + c_score + 20, 100) # මූලික ලකුණු සමඟ
        
        results.append({
            "lagna": lagna,
            "score": final_score,
            "tara": t_name
        })
    return sorted(results, key=lambda x: x['score'], reverse=True)

# --- පිටු වින්‍යාසය සහ අභිරුචි CSS (Custom Styling) ---
st.set_page_config(page_title="මුහුර්ථ AI - Elite", page_icon="🔮", layout="centered")

# අභිරුචි CSS
st.markdown("""
<style>
    /* Main background and fonts */
    .stApp {
        background: linear-gradient(145deg, #0f172a 0%, #1e1b4b 100%);
        font-family: 'Segoe UI', 'Poppins', 'Inter', sans-serif;
    }
    
    /* Title styling */
    h1 {
        text-align: center;
        background: linear-gradient(135deg, #FDE68A, #F59E0B);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
        text-shadow: 0px 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(30, 27, 75, 0.85);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(245, 158, 11, 0.3);
        box-shadow: 5px 0 20px rgba(0,0,0,0.3);
    }
    
    [data-testid="stSidebar"] .stSelectbox label, 
    [data-testid="stSidebar"] .stNumberInput label {
        color: #FDE68A;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    /* Custom card style for expander results */
    .streamlit-expanderHeader {
        background: linear-gradient(95deg, #1f2937, #111827);
        border-radius: 20px;
        color: #FDE68A;
        font-weight: bold;
        border: 1px solid rgba(245,158,11,0.3);
        transition: all 0.2s ease;
    }
    .streamlit-expanderHeader:hover {
        transform: scale(1.01);
        background: linear-gradient(95deg, #2d3a4a, #1a1f2e);
        border-color: #F59E0B;
    }
    
    /* Button styling */
    div.stButton > button {
        background: linear-gradient(90deg, #F59E0B, #D97706);
        color: #0f172a;
        font-weight: bold;
        font-size: 1.2rem;
        border: none;
        border-radius: 40px;
        padding: 0.6rem 1.8rem;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(245,158,11,0.4);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        background: linear-gradient(90deg, #FBBF24, #F59E0B);
        box-shadow: 0 8px 20px rgba(245,158,11,0.6);
        color: #000;
    }
    
    /* Input fields */
    .stSelectbox > div, .stNumberInput > div {
        background-color: #1e293b;
        border-radius: 20px;
        border: 1px solid #4b5563;
        transition: 0.2s;
    }
    .stSelectbox > div:hover, .stNumberInput > div:hover {
        border-color: #F59E0B;
    }
    
    /* Success/Error boxes */
    .stAlert {
        border-radius: 20px;
        backdrop-filter: blur(5px);
        font-weight: 500;
    }
    
    /* Metric or any extra style */
    .custom-card {
        background: rgba(31,41,55,0.6);
        backdrop-filter: blur(8px);
        border-radius: 28px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 5px solid #F59E0B;
    }
    
    /* Footer */
    footer {
        visibility: visible;
        text-align: center;
        color: #94a3b8;
        font-size: 0.8rem;
        margin-top: 2rem;
        padding: 1rem;
        border-top: 1px solid #334155;
    }
    
    hr {
        margin: 1.5rem 0;
        border-color: #334155;
    }
    
    /* Label beautify */
    .stMarkdown h3, .stMarkdown h4 {
        color: #FDE68A;
    }
    
    /* columns inside expander */
    .expander-content {
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# --- පරිශීලක මුහුණත (User Interface) ---

st.title("🔮 අති නවීන ජ්‍යොතිෂ මුහුර්ථ පද්ධතිය")
st.caption("v6 · පංචක, තාරා හා චන්ද්‍ර බලය සමගින් නිරවුල් සුභ මොහොත")
st.markdown("---")

# දත්ත ඇතුළත් කිරීම
with st.sidebar:
    st.markdown("## 👤 ඔබේ උපන් විස්තර")
    birth_nak = st.selectbox("✨ උපන් නැකත", range(27), format_func=lambda x: NAKSHATRAS[x], index=7)
    birth_rashi = st.selectbox("🌟 උපන් රාශිය", range(12), format_func=lambda x: RASHIS[x], index=4)
    st.markdown("---")
    st.caption("🪷 නිවැරදි ප්‍රතිඵල සඳහා නිවැරදි නැකත හා රාශිය තෝරන්න.")

st.markdown("## 📅 අදාළ දිනයේ දත්ත")
col1, col2, col3 = st.columns(3, gap="medium")
target_nak = col1.selectbox("🌙 දිනයේ නැකත", range(27), format_func=lambda x: NAKSHATRAS[x])
target_rashi = col2.selectbox("🌝 සඳු සිටින රාශිය", range(12), format_func=lambda x: RASHIS[x])
target_tithi = col3.number_input("📆 තිථිය (1-30)", 1, 30, 10)
target_day = st.selectbox("📅 සතියේ දිනය", range(1, 8), format_func=lambda x: WEEKDAYS[x-1])

st.markdown("---")

if st.button("🔍 සාර්ථක වේලාවන් සොයන්න", use_container_width=True):
    with st.spinner("ගණනය කරමින්... කරුණාකර රැඳී සිටින්න 🌟"):
        final_results = calculate_best_slots(birth_nak, birth_rashi, target_nak, target_rashi, target_tithi, target_day)
    
    if not final_results:
        st.error("⚠️ කණගාටුයි! මෙම දිනයේ ඔබට ගැළපෙන කිසිදු සුභ වේලාවක් (පංචක/තාරා දෝෂ නිසා) හමු නොවීය.")
        st.info("💡 උපදෙස්: වෙනත් දිනයක් හෝ වෙනත් නැකත් පරීක්ෂා කරන්න.")
    else:
        st.balloons()
        st.success(f"🎉 ඔබට ගැළපෙන සුභ වේලාවන් (ලග්න කවුළු) **{len(final_results)}** ක් හමුවිය!")
        
        for idx, res in enumerate(final_results):
            # Score-based color and icon
            if res['score'] >= 80:
                badge = "🏆 අතිශය සුභ"
                color = "gold"
            elif res['score'] >= 60:
                badge = "✨ සුභ"
                color = "lightgreen"
            else:
                badge = "🍀 මධ්‍යස්ථ"
                color = "orange"
            
            with st.expander(f"⭐ ලග්න අංකය: {res['lagna']}  |  සාර්ථකත්වය: {res['score']}%  |  {badge}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**🌟 තාරා බලය:** `{res['tara']}`")
                    st.markdown(f"**📊 ගුණත්වය:** {badge}")
                with col_b:
                    st.markdown(f"**✅ තත්ත්වය:** පංචක දෝෂ රහිත පිරිසිදු වේලාවකි.")
                    st.progress(res['score']/100, text="සමස්ත යෝග්‍යතාව")
                st.caption("💎 මෙම ලග්න කාලය තුළ කටයුතු ආරම්භ කිරීම වඩාත් සුදුසුය.")
        
        # Additional metrics
        best = final_results[0]
        st.markdown("---")
        st.markdown(f"""
        <div class="custom-card">
            <h4 style="margin:0;">🏅 වඩාත්ම සුභ ලග්නය</h4>
            <p style="font-size:1.4rem; font-weight:bold;">ලග්න අංක {best['lagna']} · සාර්ථකත්වය {best['score']}%</p>
            <p>තාරා බලය: {best['tara']} · දෝෂ රහිත පිරිසිදු මොහොතකි</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.85rem;">
    <span>🕉️ මුහුර්ථ AI · ප්‍රාචීන ජ්‍යොතිෂය හා නවීන තාක්ෂණයේ එකතුවකි</span><br>
    <span>© 2025 · සියලුම ගණනය කිරීම් නිරවද්‍යතාවයෙන් යුක්තයි</span>
</div>
""", unsafe_allow_html=True)
