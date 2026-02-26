from paddleocr import PaddleOCR
import numpy as np
import math

class CircuitOCR:
    def __init__(self, lang='en'):
        print("Initializing OCR Engine (PaddleOCR)...")
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def calculate_distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def get_center(self, box):
        if not box: return (0,0)
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def get_component_center(self, bbox):
        return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

    def scan_and_filter(self, image_path, components, proximity_threshold=100):
        print(f"OCR Scanning: {image_path}")
        
        try:
            result = self.ocr.ocr(image_path, cls=True)
        except Exception as e:
            print(f"OCR Error: {e}")
            return []
        
        filtered_texts = []

        if not result or result[0] is None:
            print("OCR: No text found.")
            return []

        print(f"OCR found {len(result[0])} text blocks. Filtering...")

        for line in result[0]:
            text_box = line[0]    
            text_str = line[1][0]
            score = line[1][1]    

            
            if score < 0.5: continue

            text_center = self.get_center(text_box)
            is_near = False
            nearest_comp = "None"

            
            for comp in components:
                if isinstance(comp, dict):
                    bbox = comp['box']
                    label = comp.get('label', 'Unknown')
                else:
                    bbox = comp[:4] 
                    label = 'Component'

                comp_center = self.get_component_center(bbox)
                dist = self.calculate_distance(text_center, comp_center)

                if dist < proximity_threshold:
                    is_near = True
                    nearest_comp = label
                    break 

            if is_near:
                filtered_texts.append({
                    'text': text_str,
                    'box': text_box,
                    'conf': score,        
                    'confidence': score,  
                    'near': nearest_comp
                })

        print(f" OCR Filtered: {len(filtered_texts)} texts remain.")
        return filtered_texts