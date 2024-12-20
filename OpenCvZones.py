import cv2
import json

zones = []
current_zone = {}
drawing = False

IMAGE_PATH = "F:/emsi5S1/PFA/Image.jpeg"
OUTPUT_FILE = "zones.json"
FIXED_WIDTH = 800
FIXED_HEIGHT = int(FIXED_WIDTH / 1.586)

def draw_rectangle(event, x, y, flags, param):
    global drawing, current_zone, zones, display_img_copy

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        current_zone = {"start": (x, y)}

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            display_img_copy = display_img.copy()
            cv2.rectangle(display_img_copy, current_zone["start"], (x, y), (0, 255, 0), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        current_zone["end"] = (x, y)
        cv2.rectangle(display_img_copy, current_zone["start"], current_zone["end"], (0, 255, 0), 2)
        label = input("Enter label for this zone: ").strip()
        if label:
            x1, y1 = current_zone["start"]
            x2, y2 = current_zone["end"]
            zones.append({"label": label, "x1": x1, "y1": y1, "x2": x2, "y2": y2})

def save_zones(output_file, zones):
    with open(output_file, 'w') as f:
        json.dump(zones, f, indent=4)
    print(f"Zones saved to {output_file}")

if __name__ == "__main__":
    img = cv2.imread(IMAGE_PATH)
    if img is None:
        print(f"Error: Unable to load image from {IMAGE_PATH}")
        exit(1)

    # Resize the image to the fixed dimensions
    display_img = cv2.resize(img, (FIXED_WIDTH, FIXED_HEIGHT))
    display_img_copy = display_img.copy()

    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", draw_rectangle)

    print("Draw rectangles to select zones. Press ESC to finish.")
    while True:
        cv2.imshow("Image", display_img_copy)
        key = cv2.waitKey(1)

        if key == 27:  # ESC key to exit
            break

    cv2.destroyAllWindows()
    save_zones(OUTPUT_FILE, zones)
