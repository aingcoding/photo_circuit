from ultralytics import YOLO
import numpy as np

class YoloDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, image_path):
        results = self.model.predict(image_path, conf=0.4,iou=0.6, verbose=False)[0]
        
        detect_plot = results.plot()
        
        components = []
        class_counters = {}
        
        boxes = results.boxes.xyxy.cpu().numpy().astype(int)
        classes = results.boxes.cls.cpu().numpy().astype(int)
        names = results.names

        for box, cls in zip(boxes, classes):
            x1, y1, x2, y2 = box
            label = names[cls]
            
            if label not in class_counters: 
                class_counters[label] = 0
            class_counters[label] += 1
            
            components.append({
                "name": f"{label}_{class_counters[label]}",
                "box": (x1, y1, x2, y2),
                "raw_nodes": [] 
            })
            
        return detect_plot, components