# Utilisation d'une image de base légère avec Python 3.13
FROM python:3.13.1-slim

# Installer les dépendances système nécessaires pour OpenCV et Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    libopencv-dev \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'intégralité de l'application
COPY . .

# Créer le dossier d'upload pour éviter les erreurs
RUN mkdir -p uploads

# Exposer le port utilisé par Flask
EXPOSE 5002

# Commande pour démarrer l'application Flask
CMD ["python", "app.py"]
