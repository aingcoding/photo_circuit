import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import os
import threading
import sys
import re 

# ==========================================
# SMART PATH SETUP
# ==========================================
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir)

project_root = get_base_path()
if project_root not in sys.path:
    sys.path.append(project_root)

# ==========================================
# IMPORT MODULES
# ==========================================
try:
    from yolo.yolo_user_function.detector import YoloDetector
    from open_cv.circuit_logic import CircuitProcessor
    from OCR.ocr_engine import CircuitOCR
    from Lcapy.circuit_analysis import analyze_netlist 
except ImportError as e:
    print(f"Import Error: {e}")

MODEL_PATH = os.path.join(project_root, 'yolo', 'weights', 'best.pt')

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CircuitApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Circuit Recognition & Analysis System Pro")
        
        self.after(0, lambda: self.state('zoomed')) 

        try:
            self.detector = YoloDetector(MODEL_PATH)
            self.processor = CircuitProcessor()
            self.ocr = CircuitOCR()
            print("System Ready.")
        except Exception as e:
            print(f"Init Warning: {e}")

        self.current_image_path = None
        self.netlist_rows = [] 
        self.result_widgets = [] 
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. LEFT SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1) 

        self.lbl_title = ctk.CTkLabel(self.sidebar, text="Circuit VISION", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_title.grid(row=0, column=0, padx=20, pady=(30, 20))

        # --- Navigation Buttons ---
        self.btn_nav_analysis = ctk.CTkButton(self.sidebar, corner_radius=0, height=40, border_spacing=10, 
                                              text="Circuit Analysis",
                                              fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                              anchor="w", command=self.show_analysis_frame)
        self.btn_nav_analysis.grid(row=1, column=0, sticky="ew")

        self.btn_nav_visual = ctk.CTkButton(self.sidebar, corner_radius=0, height=40, border_spacing=10, 
                                            text="Visualization",
                                            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                            anchor="w", command=self.show_visual_frame)
        self.btn_nav_visual.grid(row=2, column=0, sticky="ew")

        #  ปุ่ม Raw Data
        self.btn_nav_raw = ctk.CTkButton(self.sidebar, corner_radius=0, height=40, border_spacing=10, 
                                         text="Raw Data",
                                         fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                         anchor="w", command=self.show_raw_frame)
        self.btn_nav_raw.grid(row=3, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(self.sidebar, text="Waiting for input...", text_color="gray")
        self.status_label.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        # 2. MAIN CONTENT AREA
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # --- Create Frames ---
        self.frame_analysis = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frame_visual = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent", label_text="Processing Steps")
        self.frame_raw = ctk.CTkFrame(self.main_container, fg_color="transparent") 

        self.setup_visual_view()   
        self.setup_analysis_view() 
        self.setup_raw_view() 

        self.show_analysis_frame()

    # ==========================
    # Navigation Logic
    # ==========================
    def show_analysis_frame(self):
        self.frame_visual.grid_forget()
        self.frame_raw.grid_forget()
        self.frame_analysis.grid(row=0, column=0, sticky="nsew")
        self.btn_nav_analysis.configure(fg_color=("gray75", "gray25"))
        self.btn_nav_visual.configure(fg_color="transparent")
        self.btn_nav_raw.configure(fg_color="transparent")

    def show_visual_frame(self):
        self.frame_analysis.grid_forget()
        self.frame_raw.grid_forget()
        self.frame_visual.grid(row=0, column=0, sticky="nsew")
        self.btn_nav_analysis.configure(fg_color="transparent")
        self.btn_nav_visual.configure(fg_color=("gray75", "gray25"))
        self.btn_nav_raw.configure(fg_color="transparent")

    def show_raw_frame(self):
        self.frame_analysis.grid_forget()
        self.frame_visual.grid_forget()
        self.frame_raw.grid(row=0, column=0, sticky="nsew")
        self.btn_nav_analysis.configure(fg_color="transparent")
        self.btn_nav_visual.configure(fg_color="transparent")
        self.btn_nav_raw.configure(fg_color=("gray75", "gray25"))

    # ==========================
    # View Setups
    # ==========================
    def setup_visual_view(self):
        self.frame_visual.grid_columnconfigure(0, weight=1)
        self.lbl_img_detect = self.create_image_label(self.frame_visual, "1. YOLO Detection", 0)
        self.lbl_img_ocr = self.create_image_label(self.frame_visual, "2. OCR Text Detection", 1) 
        self.lbl_img_raw = self.create_image_label(self.frame_visual, "3. Cleaned Circuit", 2)
        self.lbl_img_schematic = self.create_image_label(self.frame_visual, "4. Node Analysis", 3)

    def setup_raw_view(self): #  UI สำหรับ Raw Data (Split View)
        self.frame_raw.grid_columnconfigure(0, weight=1)
        self.frame_raw.grid_columnconfigure(1, weight=1) # 2 Columns
        self.frame_raw.grid_rowconfigure(1, weight=1)

        # --- LEFT: YOLO ---
        ctk.CTkLabel(self.frame_raw, text=" YOLO Components", font=("Arial", 20, "bold")).grid(row=0, column=0, sticky="w", padx=20, pady=20)
        self.yolo_scroll = ctk.CTkScrollableFrame(self.frame_raw, label_text="Detected Components")
        self.yolo_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 20))

        # --- RIGHT: OCR ---
        ctk.CTkLabel(self.frame_raw, text=" OCR Text", font=("Arial", 20, "bold")).grid(row=0, column=1, sticky="w", padx=20, pady=20)
        self.raw_scroll = ctk.CTkScrollableFrame(self.frame_raw, label_text="Detected Text Items")
        self.raw_scroll.grid(row=1, column=1, sticky="nsew", padx=10, pady=(0, 20))
        
        # Init Headers
        self.refresh_yolo_header()
        self.refresh_raw_header()

    def refresh_yolo_header(self):
        for widget in self.yolo_scroll.winfo_children():
            widget.destroy()
        
        header_frame = ctk.CTkFrame(self.yolo_scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(header_frame, text="#", width=30, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Component", width=150, anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkLabel(header_frame, text="Confidence", width=100, font=("Arial", 12, "bold")).pack(side="right", padx=5)
        ctk.CTkFrame(self.yolo_scroll, height=2, fg_color="gray").pack(fill="x", pady=2)

    def refresh_raw_header(self):
        for widget in self.raw_scroll.winfo_children():
            widget.destroy()
            
        header_frame = ctk.CTkFrame(self.raw_scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(header_frame, text="#", width=30, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Detected Text", width=150, anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkLabel(header_frame, text="Confidence", width=100, font=("Arial", 12, "bold")).pack(side="right", padx=5)
        ctk.CTkFrame(self.raw_scroll, height=2, fg_color="gray").pack(fill="x", pady=2)

    def populate_yolo_data(self, components): #  ฟังก์ชันแสดงข้อมูล YOLO
        self.refresh_yolo_header()
        if not components:
            ctk.CTkLabel(self.yolo_scroll, text="No components detected.", text_color="gray").pack(pady=20)
            return

        for i, comp in enumerate(components):
            row = ctk.CTkFrame(self.yolo_scroll)
            row.pack(fill="x", pady=2)
            
            # Index
            ctk.CTkLabel(row, text=str(i+1), width=30).pack(side="left", padx=5)
            
            # Name
            name = comp.get('name', 'Unknown')
            ctk.CTkEntry(row, placeholder_text=name).pack(side="left", padx=5, expand=True, fill="x")
            
            # Confidence (ถ้า detector ส่งมาไม่ได้ จะแสดง -)
            conf = comp.get('conf', None)
            if conf is not None:
                conf_val = conf * 100
                conf_color = "#2ECC71" if conf_val > 80 else "#F1C40F"
                conf_text = f"{conf_val:.1f}%"
            else:
                conf_text = "-" # Detector ปัจจุบันอาจไม่ได้ส่งค่า conf มา
                conf_color = "gray"

            ctk.CTkLabel(row, text=conf_text, width=100, text_color=conf_color).pack(side="right", padx=5)

    def populate_raw_data(self, ocr_data):
        self.refresh_raw_header()
        if not ocr_data:
            ctk.CTkLabel(self.raw_scroll, text="No text detected.", text_color="gray").pack(pady=20)
            return

        for i, item in enumerate(ocr_data):
            row = ctk.CTkFrame(self.raw_scroll)
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=str(i+1), width=30).pack(side="left", padx=5)
            
            txt_val = item.get('text', '')
            e = ctk.CTkEntry(row, placeholder_text=txt_val)
            e.insert(0, txt_val)
            e.configure(state="readonly")
            e.pack(side="left", padx=5, expand=True, fill="x")
            
            conf = item.get('conf', 0) * 100
            conf_color = "#2ECC71" if conf > 80 else "#F1C40F" if conf > 50 else "#E74C3C"
            ctk.CTkLabel(row, text=f"{conf:.1f}%", width=100, text_color=conf_color).pack(side="right", padx=5)

    def setup_analysis_view(self):
        self.frame_analysis.grid_columnconfigure(0, weight=1) 
        self.frame_analysis.grid_columnconfigure(1, weight=1) 
        self.frame_analysis.grid_rowconfigure(0, weight=1)

        self.panel_left_ana = ctk.CTkFrame(self.frame_analysis, fg_color="transparent")
        self.panel_left_ana.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.lbl_title_ana_img = ctk.CTkLabel(self.panel_left_ana, text="Analyzed Circuit Reference", font=("Arial", 16, "bold"))
        self.lbl_title_ana_img.pack(pady=(5, 5))
        
        self.lbl_img_analysis_view = ctk.CTkLabel(self.panel_left_ana, text="No Image Processed")
        self.lbl_img_analysis_view.pack(expand=True, fill="both")

        self.btn_internal_upload = ctk.CTkButton(self.panel_left_ana, text="Upload Image to Analyze", 
                                                 height=50, font=("Arial", 16), command=self.handle_internal_upload)
        self.btn_internal_upload.place(relx=0.5, rely=0.5, anchor="center")

        self.panel_right_ana = ctk.CTkFrame(self.frame_analysis, fg_color="transparent")
        self.panel_right_ana.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.panel_right_ana.grid_columnconfigure(0, weight=1)
        self.panel_right_ana.grid_rowconfigure(1, weight=1) 
        self.panel_right_ana.grid_rowconfigure(4, weight=1) 

        self.lbl_editor_title = ctk.CTkLabel(self.panel_right_ana, text=" Netlist Editor", font=("Arial", 18, "bold"))
        self.lbl_editor_title.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.editor_scroll = ctk.CTkScrollableFrame(self.panel_right_ana, label_text="Component List")
        self.editor_scroll.grid(row=1, column=0, sticky="nsew") 
        
        headers = ["Comp", "Node +", "Node -", "Value", "Unit", "Status"]
        for idx, h in enumerate(headers):
            ctk.CTkLabel(self.editor_scroll, text=h, font=("Arial", 12, "bold"), text_color="#3498DB").grid(row=0, column=idx, padx=5, pady=5)

        self.frame_actions = ctk.CTkFrame(self.panel_right_ana)
        self.frame_actions.grid(row=2, column=0, sticky="ew", pady=15)
        
        self.btn_add_comp = ctk.CTkButton(self.frame_actions, text="+ Add Manual Component", command=self.add_manual_row, fg_color="#5D6D7E", height=35)
        self.btn_add_comp.pack(side="left", padx=5, expand=True, fill="x")
        
        self.btn_calc = ctk.CTkButton(self.frame_actions, text=" RUN ANALYSIS", command=self.run_lcapy_analysis, fg_color="#27AE60", hover_color="#2ECC71", height=35, font=("Arial", 14, "bold"))
        self.btn_calc.pack(side="right", padx=5, expand=True, fill="x")

        self.lbl_result_title = ctk.CTkLabel(self.panel_right_ana, text=" Analysis Results", font=("Arial", 18, "bold"))
        self.lbl_result_title.grid(row=3, column=0, sticky="w", pady=(10, 5))
        
        self.result_scroll = ctk.CTkScrollableFrame(self.panel_right_ana, label_text="Output Parameters")
        self.result_scroll.grid(row=4, column=0, sticky="nsew", pady=5)
        
        self.result_scroll.grid_columnconfigure(0, weight=2)
        self.result_scroll.grid_columnconfigure(1, weight=2)
        self.result_scroll.grid_columnconfigure(2, weight=1)

    def handle_internal_upload(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.jpeg")])
        if file_path:
            self.current_image_path = file_path
            self.btn_internal_upload.place_forget() 
            self.btn_internal_upload.pack(side="bottom", pady=20, fill="x", padx=40)
            self.btn_internal_upload.configure(text=" Change Image")
            self.lbl_img_analysis_view.configure(image=None, text=" Processing... Please wait")
            self.status_label.configure(text="Processing Image...")
            self.populate_editor_from_text("")
            self.clear_results()
            self.start_processing()

    def start_processing(self):
        threading.Thread(target=self.process_thread, daemon=True).start()

    def process_thread(self):
        try:
            # 1. YOLO
            detect_plot, components = self.detector.detect(self.current_image_path)
            
            img = cv2.imread(self.current_image_path)
            
            # --- START: MASKING FOR OCR (ถมขาวทับอุปกรณ์ก่อนส่ง OCR) ---
            # สร้างภาพ copy เพื่อใช้สำหรับ OCR โดยเฉพาะ
            img_for_ocr = img.copy()
            for comp in components:
                # เช็คว่ามี key 'box' และข้อมูลถูกต้อง
                if 'box' in comp:
                    x1, y1, x2, y2 = map(int, comp['box'])
                    # วาดสี่เหลี่ยมสีขาวทับตำแหน่งอุปกรณ์ (-1 คือถมเต็ม)
                    cv2.rectangle(img_for_ocr, (x1, y1), (x2, y2), (255, 255, 255), -1)
            # --- END MASKING ---

            # 2. OCR
            try:
                # ส่ง img_for_ocr แทน img เพื่อให้ OCR อ่านเฉพาะตัวเลขบนพื้นขาว
                full_ocr = self.ocr.ocr.ocr(img_for_ocr, cls=True) 
            except:
                full_ocr = []

            # สร้างภาพสำหรับ Visualization OCR
            ocr_vis_img = img.copy()

            formatted_ocr = []
            if full_ocr and full_ocr[0]:
                for line in full_ocr[0]:
                    pts = line[0]
                    text = line[1][0]
                    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                    x1, y1, x2, y2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
                    
                    # เก็บข้อมูล
                    formatted_ocr.append({'text': text, 'box': [x1, y1, x2, y2], 'conf': line[1][1]})
                    
                    # วาดลงภาพ Visualization (สีน้ำเงิน)
                    cv2.rectangle(ocr_vis_img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(ocr_vis_img, text, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # 3. Process Logic
            # ส่ง img ต้นฉบับ (ที่ยังมีอุปกรณ์และเส้นครบ) ไปให้ Logic ประมวลผลต่อ
            vis, final, netlist = self.processor.process_nodes(img, components, text_data=formatted_ocr)
            
            #  Update: ส่ง components ไปด้วยเพื่อแสดงผล YOLO Raw Data
            self.after(0, lambda: self.update_ui_results(detect_plot, ocr_vis_img, vis, final, netlist, formatted_ocr, components))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self.lbl_img_analysis_view.configure(text="Error Processing"))
        finally:
            self.after(0, lambda: self.status_label.configure(text="Ready"))

    def update_ui_results(self, detect_img, ocr_img, raw_img, schematic_img, netlist_text, ocr_data, yolo_data):
        # Update Images in Scrollable View
        self.show_image(detect_img, self.lbl_img_detect)
        self.show_image(ocr_img, self.lbl_img_ocr) 
        self.show_image(raw_img, self.lbl_img_raw)
        self.show_image(schematic_img, self.lbl_img_schematic)
        
        # Update Analysis View
        self.show_image(schematic_img, self.lbl_img_analysis_view)
        self.populate_editor_from_text(netlist_text)

        #  Update Raw Data View
        self.populate_raw_data(ocr_data)
        self.populate_yolo_data(yolo_data)

    # ==========================
    # Editor Logic
    # ==========================
    def add_netlist_row(self, name, n1, n2, value, unit_val="Ohm", is_ai_generated=False):
        row_idx = len(self.netlist_rows) + 1 
        entries = {}
        
        def make_entry(col, val, width):
            e = ctk.CTkEntry(self.editor_scroll, width=width, font=("Arial", 13))
            e.insert(0, val)
            e.grid(row=row_idx, column=col, padx=3, pady=3)
            return e

        entries['name'] = make_entry(0, name, 80)
        entries['n1']   = make_entry(1, n1, 60)
        entries['n2']   = make_entry(2, n2, 60)
        entries['val']  = make_entry(3, value, 80) 
        
        unit_var = ctk.StringVar(value=unit_val)
        unit_menu = ctk.CTkOptionMenu(self.editor_scroll, variable=unit_var, 
                                      values=["V", "A", "Ohm", "F", "H"], 
                                      width=70, height=28)
        unit_menu.grid(row=row_idx, column=4, padx=3, pady=3)
        
        entries['unit'] = unit_var
        entries['unit_widget'] = unit_menu

        btn_action = None
        if is_ai_generated:
            btn_action = ctk.CTkButton(self.editor_scroll, text="ON", width=50, fg_color="#27AE60",
                                     command=lambda: self.toggle_ai_row(entries, btn_action))
        else:
            btn_action = ctk.CTkButton(self.editor_scroll, text="", width=50, fg_color="#C0392B", 
                                     command=lambda: self.delete_manual_row(entries, btn_action))

        btn_action.grid(row=row_idx, column=5, padx=5, pady=3)
        self.netlist_rows.append({'entries': entries, 'btn': btn_action, 'is_ai': is_ai_generated, 'active': True})

    def add_manual_row(self):
        count = len(self.netlist_rows) + 1
        unique_name = f"R_Manual_{count}"
        self.add_netlist_row(unique_name, "1", "0", "10", "Ohm", is_ai_generated=False)

    def delete_manual_row(self, entries, btn_obj):
        for w in entries.values(): 
            if hasattr(w, 'destroy'): w.destroy()
        btn_obj.destroy()
        for i, row_data in enumerate(self.netlist_rows):
            if row_data['btn'] == btn_obj:
                self.netlist_rows.pop(i)
                break

    def toggle_ai_row(self, entries, btn_obj):
        target_row = next((row for row in self.netlist_rows if row['btn'] == btn_obj), None)
        if target_row:
            state = not target_row['active']
            target_row['active'] = state
            color = "#27AE60" if state else "gray"
            text = "ON" if state else "OFF"
            btn_obj.configure(text=text, fg_color=color)
            for key, entry in entries.items():
                if key == 'unit' or key == 'unit_widget': continue 
                entry.configure(state="normal" if state else "disabled", 
                                text_color="white" if state else "gray")

    def populate_editor_from_text(self, netlist_text):
        for row in self.netlist_rows:
            for w in row['entries'].values(): 
                if hasattr(w, 'destroy'): w.destroy()
            row['btn'].destroy()
        self.netlist_rows.clear()
        
        lines = netlist_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith(('*', '#', '.')) or "Auto-G" in line or "Netlist" in line or "Comp" in line:
                continue

            parts = line.split()
            comp_name = parts[0].upper()
            unit_guess = "Ohm"
            if comp_name.startswith('V'): unit_guess = "V"
            elif comp_name.startswith('I'): unit_guess = "A"
            elif comp_name.startswith('C'): unit_guess = "F"
            elif comp_name.startswith('L'): unit_guess = "H"

            if len(parts) >= 4:
                val_str = " ".join(parts[3:])
                self.add_netlist_row(parts[0], parts[1], parts[2], val_str, unit_guess, is_ai_generated=True)
            elif len(parts) == 3: 
                self.add_netlist_row(parts[0], parts[1], parts[2], "?", unit_guess, is_ai_generated=True)

    def run_lcapy_analysis(self):
        lines = []
        for row in self.netlist_rows:
            if row['active']:
                e = row['entries']
                lines.append(f"{e['name'].get()} {e['n1'].get()} {e['n2'].get()} {e['val'].get()}")
        
        netlist_str = "\n".join(lines)
        self.clear_results()
        
        def run_task():
            try:
                result_str = analyze_netlist(netlist_str)
                self.after(0, lambda: self.populate_results(result_str))
            except Exception as e:
                self.after(0, lambda: self.populate_results(f"Error:\n{e}", is_error=True))

        threading.Thread(target=run_task, daemon=True).start()

    def clear_results(self):
        for widget in self.result_widgets:
            widget.destroy()
        self.result_widgets.clear()
        
        headers = ["Parameter / Node", "Value", "Unit"]
        for idx, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.result_scroll, text=h, font=("Arial", 12, "bold"), text_color="#2ECC71")
            lbl.grid(row=0, column=idx, padx=5, pady=5, sticky="ew")
            self.result_widgets.append(lbl)

    def populate_results(self, text, is_error=False):
        self.clear_results()
        if is_error:
            lbl = ctk.CTkLabel(self.result_scroll, text=text, text_color="#E74C3C", justify="left")
            lbl.grid(row=1, column=0, columnspan=3, sticky="w", padx=10, pady=5)
            self.result_widgets.append(lbl)
            return

        lines = text.split('\n')
        row_idx = 1
        for line in lines:
            line = line.strip()
            if not line: continue
            if "Processing Netlist" in line: continue
            if "=" not in line and ":" not in line:
                if len(line.split()) >= 3: continue
            
            match = re.match(r"(.+?)\s*[=:]\s*(.+)", line)
            if match:
                param_name = match.group(1).strip()
                raw_value = match.group(2).strip()
                parts = raw_value.split(' ')
                val_display = raw_value
                unit_display = "-"
                if len(parts) > 1 and parts[-1].isalpha():
                    val_display = " ".join(parts[:-1])
                    unit_display = parts[-1]
                self.add_result_row_widget(row_idx, param_name, val_display, unit_display)
                row_idx += 1
            else:
                if line.endswith(':'): 
                    lbl = ctk.CTkLabel(self.result_scroll, text=line, font=("Arial", 12, "bold"), text_color="#3498DB")
                    lbl.grid(row=row_idx, column=0, columnspan=3, sticky="w", pady=(10,2), padx=5)
                    self.result_widgets.append(lbl)
                    row_idx += 1

    def add_result_row_widget(self, row, param, val, unit):
        e_param = ctk.CTkEntry(self.result_scroll, width=120, font=("Arial", 13, "bold"))
        e_param.insert(0, param)
        e_param.configure(state="readonly")
        e_param.grid(row=row, column=0, padx=3, pady=3, sticky="ew")
        e_val = ctk.CTkEntry(self.result_scroll, width=120, font=("Consolas", 13, "bold"), text_color="#2ECC71")
        e_val.insert(0, val)
        e_val.configure(state="readonly")
        e_val.grid(row=row, column=1, padx=3, pady=3, sticky="ew")
        l_unit = ctk.CTkLabel(self.result_scroll, text=unit, font=("Arial", 12))
        l_unit.grid(row=row, column=2, padx=3, pady=3)
        self.result_widgets.extend([e_param, e_val, l_unit])

    def create_image_label(self, parent, title, row_idx):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row_idx, column=0, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(frame, text=title, font=("Arial", 12, "bold")).pack(pady=5)
        lbl_img = ctk.CTkLabel(frame, text="")
        lbl_img.pack(expand=True)
        return lbl_img

    def show_image(self, cv_img, label_widget):
        if cv_img is None: return
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(cv_img)
        h_frame = 400 
        w_frame = 500
        ctk_img = ctk.CTkImage(light_image=im_pil, dark_image=im_pil, size=(w_frame, h_frame))
        label_widget.configure(image=ctk_img, text="")
        label_widget.image = ctk_img

if __name__ == "__main__":
    app = CircuitApp()
    app.mainloop()