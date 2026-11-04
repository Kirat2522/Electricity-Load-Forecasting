import streamlit as st
import requests
from datetime import datetime, time

# --- Configuration & Constants ---
st.set_page_config(
    page_title="Load Forecaster", 
    page_icon=":material/bolt:", 
    layout="centered"
)

BASE_URL = "https://probing-unlinked-early.ngrok-free.dev"
HEADERS = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true"
}

# --- Google Material UI Custom CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Google Sans', Roboto, sans-serif;
        }
        
        /* Material 3 Button Styling */
        div.stButton > button {
            background-color: #1a73e8; /* Google Blue */
            color: white;
            border-radius: 24px;
            padding: 10px 24px;
            border: none;
            font-weight: 500;
            transition: background-color 0.2s ease-in-out;
        }
        div.stButton > button:hover {
            background-color: #1557b0;
            color: white;
            border-color: transparent;
        }
        
        /* Smooth Metric Colors */
        [data-testid="stMetricValue"] {
            color: #202124;
            font-weight: 700;
        }
    </style>
""", unsafe_allow_html=True)

# --- Header & Health Check ---
st.title(":material/bolt: Electricity Demand Forecaster")

@st.cache_data(ttl=60) # Cache to avoid pinging on every UI interaction
def check_backend_status():
    try:
        response = requests.get(f"{BASE_URL}/health", headers=HEADERS, timeout=5)
        if response.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        return False
    return False

# Display Status Badge
is_connected = check_backend_status()
if is_connected:
    st.success(":material/check_circle: **Backend Connected** (API is live)", icon=None)
else:
    st.error(":material/error: **Backend Disconnected** (Check Colab runtime and ngrok)", icon=None)

# --- Input Form Card ---
st.markdown("### Forecast Parameters")
with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        input_date = st.date_input(
            "Target Date", 
            value=datetime.today(),
            help="Select the date for the forecast"
        )
    with col2:
        input_time = st.time_input(
            "Target Time", 
            value=time(12, 0),
            help="Select the time of day"
        )
        
    input_temp = st.slider(
        "Temperature Forecast (°C)", 
        min_value=-10.0, 
        max_value=50.0, 
        value=28.5, 
        step=0.1
    )

# --- Submission & Prediction Logic ---
if st.button(":material/online_prediction: Generate Forecast", disabled=not is_connected):
    # Format payload exactly as the FastAPI backend expects
    payload = {
        "date": input_date.strftime("%Y-%m-%d"),
        "time": input_time.strftime("%H:%M:%S"),
        "temperature": input_temp
    }
    
    with st.spinner("Calculating forecast..."):
        try:
            response = requests.post(
                f"{BASE_URL}/predict", 
                json=payload, 
                headers=HEADERS,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            # --- Output Card ---
            if data.get("status") == "success":
                st.markdown("### Forecast Result")
                with st.container(border=True):
                    prediction = data.get("prediction_mw", 0.0)
                    # Display a clean metric
                    st.metric(
                        label="Projected Load", 
                        value=f"{prediction:,.2f} MW",
                        delta=f"{input_temp} °C Input"
                    )
            else:
                st.warning(f"Unexpected response format: {data}")
                
        except requests.exceptions.HTTPError as err_http:
            st.error(f":material/warning: **API Error:** {err_http.response.text}")
        except requests.exceptions.RequestException as e:
            st.error(f":material/wifi_off: **Connection Error:** Could not reach the backend. \n\nDetails: {e}")
