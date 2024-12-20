import os
import cv2
import pytesseract
import json
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Configurer le chemin vers Tesseract (à adapter selon votre installation)
pytesseract.pytesseract.tesseract_cmd = r'F:\emsi5S1\PFA\Tesseract-OCR\tesseract.exe'

# Initialisation de Flask
app = Flask(__name__)

# Configuration du dossier pour stocker les images uploadées
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Dimensions fixes pour toutes les images
FIXED_WIDTH = 800
FIXED_HEIGHT = int(FIXED_WIDTH / 1.586)

# Charger les zones depuis le fichier JSON
ZONES_FILE = 'zones.json'

def resize_image(image):
    """
    Redimensionne l'image aux dimensions fixes définies.
    """
    return cv2.resize(image, (FIXED_WIDTH, FIXED_HEIGHT))

def load_zones(zones_file):
    if not os.path.exists(zones_file):
        raise FileNotFoundError(f"Le fichier de zones {zones_file} est introuvable.")
    with open(zones_file, 'r') as f:
        zones = json.load(f)
    return zones

def extract_data(image_path, zones):
    # Charger l'image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Image non valide ou introuvable.")

    print(f"[DEBUG] Dimensions d'origine de l'image : {image.shape}")

    # Redimensionner l'image aux dimensions fixes
    image = resize_image(image)
    print(f"[DEBUG] Dimensions de l'image redimensionnée : {image.shape}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)  # Améliorer le contraste

    result = {}
    for zone in zones:
        field = zone.get("label")
        x1, y1, x2, y2 = zone.get("x1"), zone.get("y1"), zone.get("x2"), zone.get("y2")

        # Vérification des limites
        if x1 < 0 or y1 < 0 or x2 > gray.shape[1] or y2 > gray.shape[0]:
            raise ValueError(f"Les coordonnées de la région {field} sont invalides par rapport à l'image redimensionnée.")

        roi = gray[y1:y2, x1:x2]
        if roi.size == 0:
            raise ValueError(f"ROI vide pour {field}.")

        # Sauvegarder le ROI pour débogage
        roi_filename = f"debug_{field}_roi.jpg"
        cv2.imwrite(roi_filename, roi)
        print(f"[DEBUG] ROI {field} sauvegardé sous {roi_filename}")

        # Appliquer un seuillage pour améliorer l'OCR
        roi = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        # Effectuer l'OCR
        if field.endswith("_AR"):
            # OCR pour le texte en arabe
            text = pytesseract.image_to_string(roi, lang='ara', config='--psm 10')
        else:
            # OCR pour le texte en anglais ou autre
            text = pytesseract.image_to_string(roi, lang='eng', config='--psm 10')
        print(f"[DEBUG] OCR {field}: {text.strip()}")  # Afficher le texte brut
        result[field] = text.strip()

    return result

@app.route('/upload_cin', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "Aucune image n'a été envoyée"}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": "Aucun fichier sélectionné"}), 400

    # Sauvegarde du fichier
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    print(f"[DEBUG] Image sauvegardée sous {file_path}")

    try:
        zones = load_zones(ZONES_FILE)
        print(f"[DEBUG] Zones chargées depuis {ZONES_FILE}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500

    try:
        extracted_data = extract_data(file_path, zones)
        print(f"[DEBUG] Données extraites : {extracted_data}")
        return jsonify({"data": extracted_data})
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[DEBUG] Image supprimée {file_path}")

if __name__ == '__main__':
    app.run(debug=True)
