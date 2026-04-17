import streamlit as st
import swisseph as swe
import pandas as pd
from datetime import datetime, timedelta

# --- GLOBAL SETTINGS ---
swe.set_sid_mode(swe.SIDM_LAHIRI)

st.set_page_config(page_title="Vedic Engine V5", layout="wide")

# --- STYLES ---
st.markdown("""
<style>
.astro-card {
    border:1px solid #ddd;
    border-radius:10px;
    padding:12px;
    background:#fff;
    text-align:center;
}
</style>
""", unsafe_allow_html=True)

st.title("🔮 Vedic Astrology Engine V5 (Pro)")

# --- CONSTANTS ---
SIGNS = ["මේෂ","වෘෂභ","මිථුන","කටක","සිංහ","කන්‍යා","තුලා","වෘශ්චික","ධනු","මකර","කුම්භ","මීන"]

NAKSHATRAS = [
"අස්විද","බෙරණ","කැති","රෝහිණී","මුවසිරස","අද","පුනාවස","පුෂ","අස්ලස",
"මා","පුවපල්","උත්තරපල්","හත","සිත","සා","විසා","අනුර","දෙට",
"මූල","පුවසල","උත්තරසල","සවණ","දෙණට","සියාවස","පුවපුටුප","උත්තරපුටුප","රේවතී"
]

DASHA_LORDS = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
DASHA_YEARS = [7,20,6,10,7,18,16,19,17]

# --- INPUT ---
st.sidebar.header("📍 Birth Details")

lat = st.sidebar.number_input("Latitude", value=6.9271)
lon = st.sidebar.number_input("Longitude", value=79.8612)
tz = st.sidebar.number_input("Timezone", value=5.5)

date = st.sidebar.date_input("Date", datetime(2008,4,13))
time = st.sidebar.time_input("Time", datetime.strptime("12:00","%H:%M").time())

# --- CORE ENGINE ---
@st.cache_data
def calculate_chart(date, time, lat, lon, tz):
    utc = time.hour + time.minute/60 - tz
    jd = swe.julday(date.year, date.month, date.day, utc)

    houses, ascmc = swe.houses_ex(jd, lat, lon, b'W')
    lagna_long = ascmc[0]
    lagna_idx = int(lagna_long / 30)

    planets = []
    p_ids = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
        "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS, "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE
    }

    for name, pid in p_ids.items():
        res = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
        lon_p = res[0][0]
        speed = res[0][3]

        sign = int(lon_p / 30)
        house = (sign - lagna_idx + 12) % 12 + 1
        nak = int(lon_p / (360/27)) % 27
        pada = int((lon_p % (360/27)) / (360/108)) + 1

        planets.append({
            "Planet": name,
            "Long": lon_p,
            "Sign": SIGNS[sign],
            "House": house,
            "Nakshatra": NAKSHATRAS[nak],
            "Pada": pada,
            "Retro": True if name == "Rahu" else speed < 0
        })

    # --- Ketu ---
    rahu = next(p for p in planets if p['Planet'] == "Rahu")
    k_long = (rahu['Long'] + 180) % 360
    k_sign = int(k_long / 30)

    planets.append({
        "Planet": "Ketu",
        "Long": k_long,
        "Sign": SIGNS[k_sign],
        "House": (k_sign - lagna_idx + 12) % 12 + 1,
        "Nakshatra": NAKSHATRAS[int(k_long / (360/27)) % 27],
        "Pada": int((k_long % (360/27)) / (360/108)) + 1,
        "Retro": True
    })

    return lagna_long, lagna_idx, planets

# --- DASHA ---
def calc_dasha(moon_long, birth_dt):
    total = 360/27
    nak = int(moon_long / total) % 27
    lord_idx = nak % 9

    passed = moon_long % total
    rem_ratio = 1 - (passed / total)

    seq = []
    current = birth_dt

    for i in range(9):
        idx = (lord_idx + i) % 9
        years = DASHA_YEARS[idx]

        if i == 0:
            years *= rem_ratio

        end = current + timedelta(days=years * 365.25)

        seq.append({
            "lord": DASHA_LORDS[idx],
            "start": current,
            "end": end,
            "years": years
        })

        current = end

    return seq

# --- FIXED ANTARDASHA ---
def calc_antardasha(d):
    out = []
    main_idx = DASHA_LORDS.index(d['lord'])
    start = d['start']

    main_years_full = DASHA_YEARS[main_idx]

    for i in range(9):
        idx = (main_idx + i) % 9

        sub_years = (main_years_full * DASHA_YEARS[idx]) / 120
        end = start + timedelta(days=sub_years * 365.25)

        out.append({
            "lord": DASHA_LORDS[idx],
            "start": start,
            "end": end
        })

        start = end

    return out

# --- INTERPRETATION ---
RULES = [
    {"planet":"Saturn","house":10,"text":"🛡️ Strong career discipline"},
    {"planet":"Jupiter","house":5,"text":"🎓 Education and wisdom"},
    {"planet":"Mars","house":7,"text":"🔥 Relationship tension"}
]

def interpret(planets):
    res = []
    for r in RULES:
        for p in planets:
            if p['Planet'] == r['planet'] and p['House'] == r['house']:
                res.append(r['text'])
    return res

# --- RUN ---
lagna_long, lagna_idx, planets = calculate_chart(date, time, lat, lon, tz)

col1, col2 = st.columns([1,2])

# --- LEFT ---
with col1:
    st.metric("Ascendant", f"{SIGNS[lagna_idx]} ({lagna_long%30:.2f}°)")
    st.dataframe(pd.DataFrame(planets)[["Planet","Sign","House","Nakshatra","Pada"]])

# --- RIGHT ---
with col2:
    st.subheader("⏳ Dasha Timeline")

    moon = next(p for p in planets if p['Planet']=="Moon")
    dasha = calc_dasha(moon['Long'], datetime.combine(date, time))

    for d in dasha:
        st.write(f"{d['lord']} | {d['start'].date()} → {d['end'].date()}")

        with st.expander("Antardasha"):
            subs = calc_antardasha(d)
            for s in subs:
                st.write(f"- {s['lord']} {s['start'].date()} → {s['end'].date()}")

# --- KUNDLI CHART ---
st.subheader("🪐 Kundli Chart")

chart = {i: [] for i in range(1,13)}

for p in planets:
    chart[p['House']].append(p['Planet'][0])

layout = [
    [12,1,2],
    [11,"",3],
    [10,"",4],
    [9,8,7]
]

for row in layout:
    cols = st.columns(3)
    for i, cell in enumerate(row):
        with cols[i]:
            if cell != "":
                st.markdown(f"""
                <div class="astro-card">
                    <b>{cell}</b><br>
                    {" ".join(chart[cell]) if chart[cell] else "-"}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.write("")

# --- INTERPRETATION ---
st.subheader("📜 Interpretation")

notes = interpret(planets)

if notes:
    for n in notes:
        st.write(n)
else:
    st.write("Add more rules for deeper analysis")

st.success("✅ V5 Ready: Chart + Dasha + Antardasha + Kundli")
