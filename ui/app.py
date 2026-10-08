import os
import sys

import requests
import streamlit as st

# Ensure the working directory is the project root so relative paths work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from ai_agent.assistant.agent import AssistantAgent

st.set_page_config(page_title="Supply Chain Intelligence", layout="wide")

# Determine API URL based on environment (Docker or Local)
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")

# Initialize the AI Agent in session state
if "agent" not in st.session_state:
    st.session_state.agent = AssistantAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page", ["AI Assistant", "API Explorer"])

if page == "AI Assistant":
    st.title("Supply Chain AI Assistant")
    st.markdown(
        "Ask questions about your shipments, route statistics, or predict delays!"
    )

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("E.g., What is the status of shipment SHP-1?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"), st.spinner("Thinking..."):
            response = st.session_state.agent.query(
                prompt, session_id="streamlit-session"
            )
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

elif page == "API Explorer":
    st.title("API Explorer")
    st.markdown(
        f"Directly test the FastAPI endpoints. (Using base URL: `{API_BASE_URL}`)"
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Health & DQ", "Shipments", "Route Stats", "Predict Delay"]
    )

    with tab1:
        st.subheader("System Health")
        if st.button("Check Health"):
            try:
                res = requests.get(f"{API_BASE_URL}/health")
                st.json(res.json())
            except Exception as e:
                st.error(f"Error: {e}")

        st.subheader("Data Quality Report")
        if st.button("Get DQ Report"):
            try:
                res = requests.get(f"{API_BASE_URL}/data-quality/report")
                st.json(res.json())
            except Exception as e:
                st.error(f"Error: {e}")

    with tab2:
        st.subheader("List Shipments")
        col1, col2 = st.columns(2)
        page_num = col1.number_input("Page", min_value=1, value=1)
        page_size = col2.number_input("Page Size", min_value=1, max_value=100, value=10)

        col3, col4, col5 = st.columns(3)
        origin = col3.text_input("Origin Port (optional)")
        dest = col4.text_input("Destination Port (optional)")
        status = col5.selectbox(
            "Status",
            ["Any", "In Transit", "Delivered", "Pending", "Cancelled", "Delayed"],
        )

        col6, col7 = st.columns(2)
        start_date = col6.date_input("Start Date (optional)", value=None)
        end_date = col7.date_input("End Date (optional)", value=None)

        if st.button("Fetch Shipments"):
            try:
                params = {"page": page_num, "page_size": page_size}
                if origin:
                    params["origin"] = origin
                if dest:
                    params["destination"] = dest
                if status != "Any":
                    params["status"] = status
                if start_date:
                    params["start_date"] = start_date.isoformat()
                if end_date:
                    params["end_date"] = end_date.isoformat()

                res = requests.get(f"{API_BASE_URL}/shipments", params=params)
                st.json(res.json())
            except Exception as e:
                st.error(f"Error: {e}")

        st.subheader("Get Shipment by ID")
        shp_id = st.text_input("Shipment ID", value="SHP-1")
        if st.button("Fetch Shipment Details"):
            try:
                res = requests.get(f"{API_BASE_URL}/shipments/{shp_id}")
                st.json(res.json())
            except Exception as e:
                st.error(f"Error: {e}")

    with tab3:
        st.subheader("Route Statistics")
        r_origin = st.text_input("Origin", value="CNSHA")
        r_dest = st.text_input("Destination", value="USLAX")
        if st.button("Get Stats"):
            try:
                res = requests.get(f"{API_BASE_URL}/routes/{r_origin}/{r_dest}/stats")
                st.json(res.json())
            except Exception as e:
                st.error(f"Error: {e}")

    with tab4:
        st.subheader("Predict Shipment Delay")
        p_shp_id = st.text_input("Target Shipment ID", value="SHP-1")
        if st.button("Predict"):
            try:
                res = requests.post(
                    f"{API_BASE_URL}/predict-delay", json={"shipment_id": p_shp_id}
                )
                st.json(res.json())
            except Exception as e:
                st.error(f"Error: {e}")
