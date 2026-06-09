import streamlit as st
import googlemaps
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURATION ---
CSV_FILE = "mileage_log.csv"
DEFAULT_START = "Your Home Address, City, State, ZIP" # Pre-fill your default starting point
# --- CONFIGURATION ---
CSV_FILE = "mileage_log.csv"
DEFAULT_START = "Your Home Address, City, State, ZIP"

# Initialize Google Maps Client directly from Streamlit Secrets
API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
gmaps = googlemaps.Client(key=API_KEY)

# --- HELPER FUNCTIONS ---
def init_csv():
    """Initializes the CSV file with headers if it doesn't exist."""
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=["Date", "Purpose", "Start Location", "End Location", "Distance (Miles)", "Status"])
        df.to_csv(CSV_FILE, index=False)

def get_mileage(start, end):
    """Calculates mileage between two points using Google Maps Matrix API."""
    try:
        matrix = gmaps.distance_matrix(start, end, mode="driving", units="imperial")
        # Extract distance in meters and convert to miles
        element = matrix['rows'][0]['elements'][0]
        if element['status'] == 'OK':
            distance_meters = element['distance']['value']
            distance_miles = round(distance_meters * 0.000621371, 2)
            return distance_miles
        else:
            return None
    except Exception as e:
        st.error(f"Error connecting to Google Maps: {e}")
        return None

# --- UI APP INTERFACE ---
st.set_page_config(page_title="BizTrip Logger", page_icon="🚗", layout="centered")

# Custom styling to make it look like a native iPhone App
st.markdown("""
    <style>
    .main .block-container { max-width: 450px; padding-top: 2rem; }
    div.stButton > button:first-child { width: 100%; background-color: #2e7d32; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚗 Business Trip Logger")
st.write("Record consulting trips instantly.")

init_csv()

# Input Form
with st.form("trip_form", clear_on_submit=True):
    date_input = st.date_input("Trip Date", datetime.now())
    purpose = st.text_input("Business Purpose / Client Name")
    start_loc = st.text_input("Starting From", value=DEFAULT_START)
    end_loc = st.text_input("Destination Address")
    submit_button = st.form_submit_button("Calculate & Record Trip")

# Logic Handle
if submit_button:
    if not purpose or not end_loc:
        st.warning("Please fill out the Purpose and Destination fields.")
    else:
        with st.spinner("Consulting Google Maps for distance..."):
            miles = get_mileage(start_loc, end_loc)
            
        if miles is not None:
            # Create new row
            new_trip = {
                "Date": date_input.strftime("%Y-%m-%d"),
                "Purpose": purpose,
                "Start Location": start_loc,
                "End Location": end_loc,
                "Distance (Miles)": miles,
                "Status": "Recorded"
            }
            
            # Append to CSV
            df_new = pd.DataFrame([new_trip])
            df_new.to_csv(CSV_FILE, mode='a', header=False, index=False)
            
            st.success(f"Successfully logged! Distance: **{miles} miles** added to log.")
        else:
            st.error("Could not calculate distance. Please check the addresses and try again.")

# --- HISTORICAL LOG VIEW ---
st.write("---")
st.subheader("Recent Trips")
try:
    df_log = pd.read_csv(CSV_FILE)
    if not df_log.empty:
        # Show last 5 logs reversed so newest is at top
        st.dataframe(df_log.tail(5).iloc[::-1], use_container_width=True)
        
        # Download button for the CSV file directly to your phone
        with open(CSV_FILE, "rb") as file:
            st.download_button(
                label="📥 Download Full CSV Log",
                data=file,
                file_name=f"mileage_log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No trips logged yet.")
except Exception as e:
    st.error(f"Error loading log: {e}")
