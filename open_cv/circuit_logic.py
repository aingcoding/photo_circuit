import cv2
import numpy as np
import math
import re
from collections import Counter

class CircuitProcessor:
    def __init__(self):
        pass

    def get_center(self, box):
        if isinstance(box, list) or isinstance(box, np.ndarray):
            box = np.array(box).flatten()
            if len(box) == 4:
                return int((box[0] + box[2]) / 2), int((box[1] + box[3]) / 2)
        return 0, 0

    def calculate_distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def clean_text_value(self, text):
        text = text.replace("O", "0").replace("o", "0") 
        text = text.replace("l", "1").replace("I", "1")
        text = text.replace(" ", "")
        return text

    def is_unit_compatible(self, comp_type, text):
        text = text.lower()
        if comp_type == 'R':
            return any(x in text for x in ['ohm', 'k', 'm', 'r']) or text.replace('.','').isdigit()
        elif comp_type == 'C':
            return any(x in text for x in ['f', 'u', 'n', 'p', 'micro'])
        elif comp_type == 'L':
            return 'h' in text
        elif comp_type == 'V':
            return 'v' in text
        elif comp_type == 'I':
            return 'a' in text
        return True

    def merge_text_and_symbols(self, text_data, yolo_components, threshold=80):
        if not text_data:
            return text_data, yolo_components

        symbols = []
        main_components = []
        unit_keywords = ['micro', 'ohm', 'symbol'] 

        for comp in yolo_components:
            name = comp.get('name', '').lower()
            is_symbol = any(k in name for k in unit_keywords)
            if is_symbol:
                symbols.append(comp)
            else:
                main_components.append(comp)

        for item in text_data:
            txt_center = self.get_center(item['box'])
            current_text = self.clean_text_value(item['text'])
            closest_sym = None
            min_dist = float('inf')

            for sym in symbols:
                sym_center = self.get_center(sym['box'])
                dist = self.calculate_distance(txt_center, sym_center)
                if dist < min_dist:
                    min_dist = dist
                    closest_sym = sym

            if closest_sym and min_dist < threshold:
                sym_name = closest_sym.get('name', '').lower()
                unit_suffix = ""
                if 'micro' in sym_name: unit_suffix = "u"
                elif 'ohm' in sym_name: unit_suffix = "ohm"
                
                if unit_suffix and unit_suffix not in current_text:
                    current_text = f"{current_text}{unit_suffix}"
            
            item['text'] = current_text

        return text_data, main_components

    def process_nodes(self, original_image, components, text_data=None):
        text_data, main_components = self.merge_text_and_symbols(text_data, components)

        img_clean = original_image.copy() 
        final_schematic = original_image.copy() 
        processed_comps = []
        
        def get_spice_info(label):
            label = label.lower()
            if 'resistor' in label: return 'R'
            if 'capacitor' in label: return 'C'
            if 'inductor' in label: return 'L'
            if 'voltage' in label or 'source' in label: return 'V'
            if 'current' in label: return 'I'
            return 'X'

        for i, comp in enumerate(main_components):
            box = list(map(int, comp['box']))
            raw_label = comp.get('name', f"comp_{i}")
            prefix = get_spice_info(raw_label)
            spice_name = f"{prefix}{i+1}"
            
            processed_comps.append({
                "id": i,
                "name": spice_name,
                "type": prefix,
                "box": box,
                "raw_nodes": [],
                "matched_value": None 
            })

        if text_data:
            for comp in processed_comps:
                cx, cy = self.get_center(comp['box'])
                candidates = []
                for item in text_data:
                    tx, ty = self.get_center(item['box'])
                    dist = math.sqrt((cx - tx)**2 + (cy - ty)**2)
                    if dist < 250:
                        text_val = item['text']
                        score = dist
                        if self.is_unit_compatible(comp['type'], text_val):
                            score -= 100 
                        candidates.append({'text': text_val, 'score': score})
                
                candidates.sort(key=lambda x: x['score'])
                if candidates:
                    val_clean = candidates[0]['text'].lower()
                    val_clean = val_clean.replace("ohm", "").replace("f", "").replace("h", "").replace("v", "")
                    comp['matched_value'] = val_clean.upper()

        for c in processed_comps:
            x1, y1, x2, y2 = c["box"]
            cv2.rectangle(img_clean, (x1, y1), (x2, y2), (255, 255, 255), -1)

        if text_data:
            for item in text_data:
                box = item['box']
                if len(box) == 4 and isinstance(box[0], (int, float)):
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(img_clean, (x1, y1), (x2, y2), (255, 255, 255), -1)

        gray = cv2.cvtColor(img_clean, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        mask_dilated = cv2.dilate(binary, np.ones((5,5), np.uint8), iterations=3)
        num_labels, labels_im, stats, centroids = cv2.connectedComponentsWithStats(mask_dilated, connectivity=8)

        margin = 15
        all_detected_nodes = []
        for c in processed_comps:
            x1, y1, x2, y2 = c["box"]
            h_img, w_img = labels_im.shape
            roi = labels_im[max(0, y1-margin):min(h_img, y2+margin), max(0, x1-margin):min(w_img, x2+margin)]
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
            for n in valid_nodes: active_node_ids.add(n)
        
        sorted_node_ids = sorted(list(active_node_ids))
        
        # --- 🔥 FIX: บังคับให้ Node สุดท้ายเป็น '0' (Ground) เสมอ ---
        id_to_name = {}
        for i, nid in enumerate(sorted_node_ids):
            if i == len(sorted_node_ids) - 1:
                id_to_name[nid] = '0' # บังคับเป็นกราวด์
            else:
                id_to_name[nid] = str(i+1)
        # --------------------------------------------------------

        if len(active_node_ids) > 0:
            colors = np.random.randint(0, 255, size=(num_labels, 3), dtype=np.uint8)
            colors[0] = [0, 0, 0] 
            colored_nodes = colors[labels_im]
            colored_nodes[labels_im == 0] = 0
            final_schematic = cv2.addWeighted(final_schematic, 0.7, colored_nodes, 0.3, 0)

        for nid in active_node_ids:
            cx, cy = int(centroids[nid][0]), int(centroids[nid][1])
            cv2.circle(final_schematic, (cx, cy), 15, (0, 0, 255), -1) 
            # แสดงชื่อ Node (ถ้าเป็น 0 ให้เขียน Gnd)
            node_name_show = "Gnd" if id_to_name[nid] == '0' else id_to_name[nid]
            cv2.putText(final_schematic, node_name_show, (cx-7, cy+7), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        for c in processed_comps:
            x1, y1, x2, y2 = c["box"]
            val_show = c['matched_value'] if c['matched_value'] else "?"
            display = f"{c['name']} ({val_show})"
            cv2.rectangle(final_schematic, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(final_schematic, display, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 100, 0), 2)

        netlist_str = "# Auto-Generated Netlist\n"
        for c in processed_comps:
            valid_nodes = [n for n in c["raw_nodes"] if node_counts[n] >= 1]
            node1 = id_to_name.get(valid_nodes[0], "?") if len(valid_nodes) > 0 else "?"
            node2 = id_to_name.get(valid_nodes[1], "0") if len(valid_nodes) > 1 else "0"
            value = c['matched_value'] if c['matched_value'] else "1k"
            netlist_str += f"{c['name']} {node1} {node2} {value}\n"

        return img_clean, final_schematic, netlist_str