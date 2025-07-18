#!/bin/sh

# Start FastAPI in the background and log to fastapi.log
uvicorn ats_ai.app_server:app --host 0.0.0.0 --port 8000 > .logs/fastapi.log 2>&1 &

# Start Streamlit in the foreground and log to streamlit.log
streamlit run ats_ai/streamlit_app.py --server.port 8501 --server.address 127.0.0.1 > .logs/streamlit.log 2>&1
