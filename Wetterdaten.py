import streamlit as st
import pandas as pd
import requests
import datetime as dt
import matplotlib.pyplot as plt

st.set_page_config(page_title="Normaußentemperatur nach PLZ", layout="wide")

st.title("Normaußentemperatur in Deutschland")

# Eingabeparameter
plz = st.text_input("Postleitzahl eingeben:", "10115")
end_date = dt.date.today()
start_date = end_date - dt.timedelta(days=365*10)

col1, col2 = st.columns(2)
with col1:
    start = st.date_input("Startdatum", start_date)
with col2:
    end = st.date_input("Enddatum", end_date)

if st.button("Daten abrufen"):
    try:
        # Schritt 1: Geocoding für PLZ über Nominatim (OpenStreetMap)
        geo_url = f"https://nominatim.openstreetmap.org/search?postalcode={plz}&country=Germany&format=json&limit=1"
        geo = requests.get(geo_url, headers={"User-Agent": "StreamlitApp"}).json()

        if not geo:
            st.error("Keine deutsche Koordinate gefunden. Bitte PLZ prüfen.")
            st.stop()

        lat = float(geo[0]["lat"])
        lon = float(geo[0]["lon"])
        location = geo[0]["display_name"]

        # Schritt 2: Open-Meteo Historical API abrufen
        url = (
            f"https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lon}"
            f"&start_date={start}&end_date={end}"
            f"&hourly=temperature_2m"
            f"&timezone=Europe/Berlin"
        )
        data = requests.get(url).json()

        if "hourly" not in data:
            st.error("Keine Wetterdaten verfügbar.")
            st.stop()

        df = pd.DataFrame({
            "time": pd.to_datetime(data["hourly"]["time"]),
            "temperature_2m": data["hourly"]["temperature_2m"]
        })

        # Schritt 3: Tages- und Wochenmittel berechnen
        df = df.set_index("time")
        daily = df.resample("D").mean().rename(columns={"temperature_2m": "t_mean"}).reset_index()

        daily["iso_year"] = daily["time"].dt.isocalendar().year
        daily["iso_week"] = daily["time"].dt.isocalendar().week
        weekly = daily.groupby(["iso_year", "iso_week"])["t_mean"].mean().reset_index()

        # Schritt 4: Darstellung
        st.subheader(f"Ergebnisse für {location} (PLZ {plz})")
        st.write("Tägliche Mitteltemperatur (Normaußentemperatur)")

        fig1, ax1 = plt.subplots(figsize=(10,4))
        ax1.plot(daily["time"], daily["t_mean"], linewidth=0.5)
        ax1.set_ylabel("°C")
        ax1.set_title("Tägliche Mitteltemperatur")
        st.pyplot(fig1)

        st.write("Wöchentliche Mitteltemperatur")
        weekly["week_str"] = weekly["iso_year"].astype(str) + "-W" + weekly["iso_week"].astype(str)

        fig2, ax2 = plt.subplots(figsize=(10,4))
        ax2.plot(weekly["week_str"], weekly["t_mean"], linewidth=0.8)
        ax2.set_ylabel("°C")
        ax2.set_title("Wöchentliche Mitteltemperatur")
        ax2.tick_params(axis='x', labelrotation=90)
        st.pyplot(fig2)

        st.subheader("📅 Datentabellen")
        st.write("Tägliche Werte:")
        st.dataframe(daily.head(50))
        st.write("Wöchentliche Werte:")
        st.dataframe(weekly.head(50))

    except Exception as e:
        st.error(f"Fehler: {e}")
