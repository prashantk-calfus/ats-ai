FROM python:3.13

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["python3", "-m", "streamlit", "run", "frontend.py", "--server.port", "8501", "--server.address", "0.0.0.0"]