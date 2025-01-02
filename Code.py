from pathlib import Path
import cv2
import pytesseract
import json
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS  # Importer CORS

# Configurer le chemin vers Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialisation de Flask
app = Flask(__name__)
CORS(app)

# Configuration du dossier pour stocker les images uploadées
UPLOAD_FOLDER = Path('uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)  # Crée le dossier s'il n'existe pas

# Dimensions fixes pour toutes les images
FIXED_WIDTH = 800
FIXED_HEIGHT = int(FIXED_WIDTH / 1.586)

# Charger les zones depuis le fichier JSON
ZONES_FILE = Path('zones.json')


def resize_image(image):
    return cv2.resize(image, (FIXED_WIDTH, FIXED_HEIGHT))


def load_zones(zones_file):
    if not zones_file.exists():
        raise FileNotFoundError(f"Le fichier de zones {zones_file} est introuvable.")
    with zones_file.open('r') as f:
        zones = json.load(f)
    return zones


def extract_data(image_path, zones):
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError("Image non valide ou introuvable.")

    print(f"[DEBUG] Dimensions d'origine de l'image : {image.shape}")

    image = resize_image(image)
    print(f"[DEBUG] Dimensions de l'image redimensionnée : {image.shape}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    result = {}
    for zone in zones:
        field = zone.get("label")
        x1, y1, x2, y2 = zone.get("x1"), zone.get("y1"), zone.get("x2"), zone.get("y2")

        if x1 < 0 or y1 < 0 or x2 > gray.shape[1] or y2 > gray.shape[0]:
            raise ValueError(f"Les coordonnées de la région {field} sont invalides par rapport à l'image redimensionnée.")

        roi = gray[y1:y2, x1:x2]
        if roi.size == 0:
            raise ValueError(f"ROI vide pour {field}.")

        roi_filename = UPLOAD_FOLDER / f"debug_{field}_roi.jpg"
        cv2.imwrite(str(roi_filename), roi)
        print(f"[DEBUG] ROI {field} sauvegardé sous {roi_filename}")

        roi = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        if field.endswith("_AR"):
            text = pytesseract.image_to_string(roi, lang='ara', config='--psm 10')
        else:
            text = pytesseract.image_to_string(roi, lang='eng', config='--psm 10')
        print(f"[DEBUG] OCR {field}: {text.strip()}")
        result[field] = text.strip()

    return result

@app.route('/upload_cin', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "Aucune image n'a été envoyée"}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": "Aucun fichier sélectionné"}), 400

    filename = secure_filename(file.filename)
    file_path = UPLOAD_FOLDER / filename
    file.save(str(file_path))
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
        return jsonify(extracted_data)  # Renvoie directement l'objet JSON
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if file_path.exists():
            file_path.unlink()
            print(f"[DEBUG] Image supprimée {file_path}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
