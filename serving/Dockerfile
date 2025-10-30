FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY model.joblib /app/model.joblib         
ENV MODEL_PATH=/app/model.joblib
EXPOSE 7860
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","7860"]
COPY version.json /app/version.json
ENV VERSION_PATH=/app/version.json

