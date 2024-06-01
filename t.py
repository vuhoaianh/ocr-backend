from ultralytics import YOLO


model = YOLO("model/weights/last.pt")
results = model.predict(r"C:\Users\Sondv\Documents\Đỗ Văn Sơn\backend-ocr-pdf\z5443404922712_8de4c99581389e39fce0245c0c1586b3.jpg", save=True, save_conf=True)