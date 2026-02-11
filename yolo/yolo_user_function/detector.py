from ultralytics import YOLO
import numpy as np

class YoloDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, image_path):
        # 1. Predict
        results = self.model.predict(image_path, conf=0.5, verbose=False)[0]
        
        # 2. Get Plot Image (รูปที่มีกรอบสี่เหลี่ยมจาก YOLO)
        detect_plot = results.plot()
        
        # 3. Extract Components Data
        components = []
        class_counters = {}
        
        # ดึงข้อมูล Box และ Class
        boxes = results.boxes.xyxy.cpu().numpy().astype(int)
        classes = results.boxes.cls.cpu().numpy().astype(int)
        names = results.names

        for box, cls in zip(boxes, classes):
            x1, y1, x2, y2 = box
            label = names[cls]
            
            # นับจำนวนอุปกรณ์ (เช่น Resistor_1, Resistor_2)
            if label not in class_counters: 
                class_counters[label] = 0
            class_counters[label] += 1
            
            components.append({
                "name": f"{label}_{class_counters[label]}",
                "box": (x1, y1, x2, y2),
                "raw_nodes": [] # เตรียมที่ว่างไว้ใส่ node
            })
            
        return detect_plot, components