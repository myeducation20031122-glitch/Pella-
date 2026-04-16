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

# --- පරිශීලක මුහුණත (User Interface) ---

st.set_page_config(page_title="මුහුර්ථ AI - Elite", page_icon="🔮")
st.title("🔮 අති නවීන ජ්‍යොතිෂ මුහුර්ථ පද්ධතිය (v6)")
st.markdown("---")

# දත්ත ඇතුළත් කිරීම
with st.sidebar:
    st.header("👤 ඔබේ උපන් විස්තර")
    birth_nak = st.selectbox("උපන් නැකත", range(27), format_func=lambda x: NAKSHATRAS[x], index=7)
    birth_rashi = st.selectbox("උපන් රාශිය", range(12), format_func=lambda x: RASHIS[x], index=4)

st.header("📅 අදාළ දිනයේ දත්ත")
col1, col2, col3 = st.columns(3)
target_nak = col1.selectbox("දිනයේ නැකත", range(27), format_func=lambda x: NAKSHATRAS[x])
target_rashi = col2.selectbox("සඳු සිටින රාශිය", range(12), format_func=lambda x: RASHIS[x])
target_tithi = col3.number_input("තිථිය (1-30)", 1, 30, 10)
target_day = st.selectbox("සතියේ දිනය", range(1, 8), format_func=lambda x: ["ඉරිදා", "සඳුදා", "අඟහරුවාදා", "බදාදා", "බ්‍රහස්පතින්දා", "සිකුරාදා", "සෙනසුරාදා"][x-1])

if st.button("🔍 සාර්ථක වේලාවන් සොයන්න"):
    final_results = calculate_best_slots(birth_nak, birth_rashi, target_nak, target_rashi, target_tithi, target_day)
    
    if not final_results:
        st.error("⚠️ කණගාටුයි! මෙම දිනයේ ඔබට ගැළපෙන කිසිදු සුභ වේලාවක් (පංචක/තාරා දෝෂ නිසා) හමු නොවීය.")
    else:
        st.success(f"ඔබට ගැළපෙන සුභ වේලාවන් (ලග්න කවුළු) {len(final_results)} ක් හමුවිය!")
        for res in final_results:
            color = "blue" if res['score'] >= 80 else "green"
            with st.expander(f"⭐ ලග්න අංකය: {res['lagna']} (සාර්ථකත්වය: {res['score']}%)"):
                st.write(f"**තාරා බලය:** {res['tara']}")
                st.write(f"**තත්ත්වය:** පංචක දෝෂ රහිත පිරිසිදු වේලාවකි.")
