import cv2
import numpy as np
import math
import re
from collections import Counter

class CircuitProcessor:
    def __init__(self):
        pass

    def get_center(self, box):
        """ช่วยคำนวณจุดกึ่งกลางของกล่อง"""
        if isinstance(box, list) or isinstance(box, np.ndarray):
            box = np.array(box).flatten()
            if len(box) == 4: # x1, y1, x2, y2
                return int((box[0] + box[2]) / 2), int((box[1] + box[3]) / 2)
            elif len(box) >= 8: # Polygon
                pts = box.reshape(-1, 2)
                return int(np.mean(pts[:, 0])), int(np.mean(pts[:, 1]))
        return 0, 0

    def check_unit_match(self, text, label):
        """
        ตรวจสอบว่า Text มีหน่วยตรงกับชนิดอุปกรณ์หรือไม่
        Return: True ถ้าหน่วยตรง, False ถ้าไม่ตรง
        """
        text = text.lower().strip()
        label = label.lower()
        
        # กรอง Text ที่ไม่มีตัวเลขเลยออกไปก่อน (ค่าอุปกรณ์ต้องมีตัวเลข เช่น 10k, 5V)
        if not any(char.isdigit() for char in text):
            return False

        # กฎการเช็คหน่วยตามชนิดอุปกรณ์
        if "capacitor" in label:
            # ต้องลงท้ายด้วย f (เช่น 10uf, 100nf) หรือมี f ในคำ
            return bool(re.search(r'[fF]$', text)) or 'f' in text
        
        elif "inductor" in label:
            # ต้องมี h (เช่น 1mh, 10uh)
            return 'h' in text
        
        elif "voltage" in label or "source" in label: # Voltage Source
            # ต้องมี v (เช่น 5v, 12v)
            return 'v' in text
            
        elif "current" in label: # Current Source
            # ต้องมี a (เช่น 1a, 20ma)
            return 'a' in text
            
        elif "resistor" in label:
            # Resistor ยังไม่มีหน่วยโอห์มให้เช็ค 
            # ให้ผ่านตลอดถ้ามีตัวเลข (Logic ข้างนอกจะเลือกตัวที่ใกล้ที่สุดเอง)
            return True
            
        return False # อุปกรณ์อื่นๆ

    def process_nodes(self, original_image, components, text_data=None):
        """
        Input: ภาพต้นฉบับ, ข้อมูล Components (YOLO), ข้อมูล Text (OCR)
        Output: ภาพ Clean, ภาพผลลัพธ์ (Schematic), Netlist Text
        """
        
        # 1. เตรียมข้อมูล & โครงสร้าง
        img_clean = original_image.copy() 
        final_schematic = original_image.copy() 
        
        processed_comps = []
        for i, comp in enumerate(components):
            if isinstance(comp, dict):
                box = list(map(int, comp['box']))
                if 'name' in comp:
                    comp_name = comp['name']
                    label = comp.get('label', comp_name.split('_')[0]) # ดึง label ดิบออกมา (เช่น resistor)
                else:
                    label = comp.get('label', 'comp')
                    comp_name = f"{label}_{i+1}"
            else:
                box = list(map(int, comp[:4]))
                label = 'comp'
                comp_name = f"comp_{i+1}"
            
            processed_comps.append({
                "id": i,
                "name": comp_name,
                "label": label, # เก็บ label ไว้เช็คหน่วย
                "box": box,
                "raw_nodes": [],
                "matched_value": None # เก็บค่าที่ Smart Match ได้
            })

        # =========================================================
        # 🔥 STEP: Smart Value Matching (จับคู่ค่าตามหน่วย)
        # =========================================================
        if text_data:
            used_text_indices = set() # กันไม่ให้ text ซ้ำ (ถ้าจำเป็น)

            for comp in processed_comps:
                cx, cy = self.get_center(comp['box'])
                candidates = []

                # 1. หาระยะห่างของ Text ทุกตัวกับ Component นี้
                for t_idx, item in enumerate(text_data):
                    tx, ty = self.get_center(item['box'])
                    dist = math.sqrt((cx - tx)**2 + (cy - ty)**2)
                    
                    # ถ้าระยะห่างไม่เกิน 200 pixel (ปรับได้)
                    if dist < 200:
                        candidates.append({
                            'text': item['text'],
                            'dist': dist,
                            'idx': t_idx
                        })
                
                # 2. เรียงลำดับตามความใกล้ (ใกล้สุดขึ้นก่อน)
                candidates.sort(key=lambda x: x['dist'])

                # 3. วนหาตัวแรกที่ "หน่วยถูกต้อง"
                for cand in candidates:
                    if self.check_unit_match(cand['text'], comp['label']):
                        comp['matched_value'] = cand['text']
                        # used_text_indices.add(cand['idx']) # ถ้าไม่อยากให้ใช้ซ้ำให้ uncomment
                        break # เจอแล้วหยุดเลย เอาตัวที่ใกล้ที่สุดที่หน่วยตรง

        # =========================================================
        # STEP 1: Masking
        # =========================================================
        for c in processed_comps:
            x1, y1, x2, y2 = c["box"]
            cv2.rectangle(img_clean, (x1, y1), (x2, y2), (255, 255, 255), -1)

        if text_data:
            for item in text_data:
                box = np.array(item['box']).astype(np.int32)
                cv2.fillPoly(img_clean, [box], (255, 255, 255))

        # =========================================================
        # STEP 2: Image Processing
        # =========================================================
        gray = cv2.cvtColor(img_clean, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        mask_dilated = cv2.dilate(binary, np.ones((5,5), np.uint8), iterations=3)

        num_labels, labels_im, stats, centroids = cv2.connectedComponentsWithStats(mask_dilated, connectivity=8)

        # =========================================================
        # STEP 3: Mapping & Filtering Logic
        # =========================================================
        margin = 15
        all_detected_nodes = [] 
        
        for c in processed_comps:
            x1, y1, x2, y2 = c["box"]
            h_img, w_img = labels_im.shape
            
            roi = labels_im[max(0, y1-margin):min(h_img, y2+margin), 
                            max(0, x1-margin):min(w_img, x2+margin)]
            
            unique_ids = np.unique(roi)
            
            for nid in unique_ids:
                if nid == 0: continue 
                if stats[nid, cv2.CC_STAT_AREA] > 300:
                    c["raw_nodes"].append(nid)
                    all_detected_nodes.append(nid)

        node_counts = Counter(all_detected_nodes)
        active_node_ids = set()
        
        for c in processed_comps:
            valid_nodes = [n for n in c["raw_nodes"] if node_counts[n] >= 1] 
            c["raw_nodes"] = valid_nodes
            for n in valid_nodes:
                active_node_ids.add(n)

        # =========================================================
        # STEP 4: Visualization
        # =========================================================
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        sorted_node_ids = sorted(list(active_node_ids))
        
        id_to_name = {}
        for i, nid in enumerate(sorted_node_ids):
            suffix = str(i // len(alphabet)) if i >= len(alphabet) else ""
            name = alphabet[i % len(alphabet)] + suffix
            id_to_name[nid] = name

        # วาดเส้น Node
        if len(active_node_ids) > 0:
            colors = np.random.randint(0, 255, size=(num_labels, 3), dtype=np.uint8)
            colors[0] = [0, 0, 0] 
            colored_nodes = colors[labels_im]
            colored_nodes[labels_im == 0] = 0
            final_schematic = cv2.addWeighted(final_schematic, 0.7, colored_nodes, 0.3, 0)

        # วาดชื่อ Node
        for nid in active_node_ids:
            cx, cy = int(centroids[nid][0]), int(centroids[nid][1])
            name = id_to_name[nid]
            cv2.circle(final_schematic, (cx, cy), 15, (0, 0, 255), -1) 
            cv2.putText(final_schematic, name, (cx-7, cy+7), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # วาดชื่ออุปกรณ์
        for c in processed_comps:
            x1, y1, x2, y2 = c["box"]
            cv2.rectangle(final_schematic, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(final_schematic, c["name"], (x1, y1-5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 100, 0), 2)

        if text_data:
            for item in text_data:
                box = np.array(item['box']).astype(np.int32)
                cv2.polylines(final_schematic, [box], True, (255, 0, 0), 2)

        # =========================================================
        # STEP 5: Netlist Report Generation
        # =========================================================
        netlist_str = "=== 🔌 Circuit Netlist ===\n\n"
        
        # 5.1 Nodes Connection
        netlist_str += "--- Connections ---\n"
        for c in processed_comps:
            node_names = [id_to_name[nid] for nid in c["raw_nodes"] if nid in id_to_name]
            node_names = sorted(list(set(node_names))) 
            node_str = f"[{', '.join(node_names)}]" if node_names else "[Not Connected]"
            netlist_str += f"{c['name']} -> Nodes: {node_str}\n"

        # 5.2 (NEW) Smart Values Matching
        netlist_str += "\n" + "="*35 + "\n"
        netlist_str += "🔹 Smart Component Values (Auto Match)\n"
        netlist_str += "="*35 + "\n"
        
        found_val = False
        for c in processed_comps:
            if c['matched_value']:
                netlist_str += f"✅ {c['name']} \t= {c['matched_value']}\n"
                found_val = True
            else:
                # กรณีหาไม่เจอ ลองแสดงตัวที่ใกล้ที่สุดแบบไม่มีหน่วยดู (เผื่อ Resistor)
                pass 
        
        if not found_val:
            netlist_str += "No values matched with correct units.\n"

        # 5.3 Raw OCR Data
        netlist_str += "\n" + "-"*35 + "\n"
        netlist_str += "📝 Raw OCR Data (All Detected)\n"
        netlist_str += "-"*35 + "\n"
        
        if text_data:
            for i, item in enumerate(text_data):
                conf = item.get('conf', 0)
                conf_str = f"{conf:.2f}" if isinstance(conf, (float, int)) else "N/A"
                netlist_str += f"{i+1}. {item['text']} (Conf: {conf_str})\n"
        else:
            netlist_str += "No text detected.\n"

        return img_clean, final_schematic, netlist_str