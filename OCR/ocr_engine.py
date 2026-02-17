from paddleocr import PaddleOCR
import numpy as np
import math

class CircuitOCR:
    def __init__(self, lang='en'):
        # โหลดโมเดล OCR เตรียมไว้ (โหลดครั้งเดียว)
        print("Initializing OCR Engine (PaddleOCR)...")
        # use_angle_cls=True ช่วยให้อ่านตัวหนังสือเอียงๆ หรือแนวตั้งได้ดีขึ้น
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def calculate_distance(self, p1, p2):
        """คำนวณระยะห่างระหว่างจุด 2 จุด"""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def get_center(self, box):
        """หาจุดกึ่งกลางของกล่องข้อความ"""
        # box = [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        if not box: return (0,0)
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def get_component_center(self, bbox):
        """หาจุดกึ่งกลางของ Component (x1, y1, x2, y2)"""
        return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

    def scan_and_filter(self, image_path, components, proximity_threshold=100):
        """
        Scan หาตัวหนังสือ และกรองเฉพาะที่อยู่ใกล้ Component
        proximity_threshold: ระยะห่างสูงสุด (pixel) ที่ยอมรับได้
        """
        print(f"OCR Scanning: {image_path}")
        
        # เริ่มสแกนภาพ
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
            text_box = line[0]    # พิกัด 4 จุด
            text_str = line[1][0]
            score = line[1][1]    # ค่าความมั่นใจ (Confidence)

            # 1. กรองความมั่นใจต่ำกว่า 50%
            if score < 0.5: continue

            text_center = self.get_center(text_box)
            is_near = False
            nearest_comp = "None"

            # 2. เช็คระยะห่างกับ Component ทุกตัว
            for comp in components:
                # จัดการ Format ข้อมูล (รองรับทั้ง Dict และ List)
                if isinstance(comp, dict):
                    bbox = comp['box']
                    label = comp.get('label', 'Unknown')
                else:
                    bbox = comp[:4] # [x1, y1, x2, y2]
                    label = 'Component'

                comp_center = self.get_component_center(bbox)
                dist = self.calculate_distance(text_center, comp_center)

                if dist < proximity_threshold:
                    is_near = True
                    nearest_comp = label
                    break  # เจอตัวใกล้แล้ว หยุดเช็คตัวอื่น

            # 3. ถ้าผ่านเกณฑ์ เก็บข้อมูลไว้
            if is_near:
                filtered_texts.append({
                    'text': text_str,
                    'box': text_box,
                    'conf': score,        #  แก้ชื่อ Key ตรงนี้เป็น 'conf' ให้ตรงกับ circuit_logic.py
                    'confidence': score,  # เก็บชื่อเดิมไว้ด้วยเผื่อส่วนอื่นใช้
                    'near': nearest_comp
                })

        print(f" OCR Filtered: {len(filtered_texts)} texts remain.")
        return filtered_texts