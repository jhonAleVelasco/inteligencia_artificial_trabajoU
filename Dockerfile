# FrutaCheck: imagen de la aplicacion Streamlit
# Construir:  docker build -t frutacheck .
# Ejecutar:   docker run -p 8501:8501 frutacheck   ->  http://localhost:8501
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Solo lo necesario para servir la app (los datos y el notebook no hacen falta)
COPY src/ src/
COPY app/ app/
COPY models/ models/

EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
