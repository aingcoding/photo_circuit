import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import os
import threading
import sys
import re 

# --- Path Setup ---
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir)

project_root = get_base_path()
if project_root not in sys.path:
    sys.path.append(project_root)

# --- Imports ---
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
        
        # 1. SET FULL SCREEN STARTUP
        self.after(0, lambda: self.state('zoomed')) 

        # Initialize Engines
        try:
            self.detector = YoloDetector(MODEL_PATH)
            self.processor = CircuitProcessor()
            self.ocr = CircuitOCR()
            print("System Ready.")
        except Exception as e:
            messagebox.showerror("Init Error", str(e))

        self.current_image_path = None
        self.netlist_rows = [] 
        self.result_widgets = [] # เก็บ Widget ของผลลัพธ์เพื่อลบภายหลัง
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Left Panel (Controls) ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.lbl_title = ctk.CTkLabel(self.sidebar, text="⚡ Circuit AI", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_title.pack(pady=(30, 20))

        self.btn_upload = ctk.CTkButton(self.sidebar, text="📂 Upload Image", height=40, command=self.upload_image)
        self.btn_upload.pack(pady=10, padx=20, fill="x")

        self.btn_process = ctk.CTkButton(self.sidebar, text="⚙️ Process Circuit", height=40, command=self.start_processing, state="disabled", fg_color="#D35400")
        self.btn_process.pack(pady=10, padx=20, fill="x")
        
        self.status_label = ctk.CTkLabel(self.sidebar, text="Waiting for input...", text_color="gray")
        self.status_label.pack(pady=20, side="bottom")

        # --- Main Area (Tabs) ---
        self.main_tab = ctk.CTkTabview(self)
        self.main_tab.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.tab_visual = self.main_tab.add("Visualization")
        self.tab_analysis = self.main_tab.add("Circuit Analysis")

        # === TAB 1: Visualization ===
        self.tab_visual.grid_columnconfigure((0,1,2), weight=1)
        self.tab_visual.grid_rowconfigure(0, weight=1)
        self.lbl_img_detect = self.create_image_label(self.tab_visual, "YOLO Detection", 0)
        self.lbl_img_raw = self.create_image_label(self.tab_visual, "Cleaned Circuit", 1)
        self.lbl_img_schematic = self.create_image_label(self.tab_visual, "Node Analysis", 2)

        # === TAB 2: Analysis ===
        self.setup_analysis_tab()

    def setup_analysis_tab(self):
        self.tab_analysis.grid_columnconfigure(0, weight=1) 
        self.tab_analysis.grid_columnconfigure(1, weight=1) 
        self.tab_analysis.grid_rowconfigure(0, weight=1)

        # --- Left Side: Final Image ---
        self.frame_analysis_img = ctk.CTkFrame(self.tab_analysis, fg_color="transparent")
        self.frame_analysis_img.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.lbl_title_ana_img = ctk.CTkLabel(self.frame_analysis_img, text="Analyzed Circuit Reference", font=("Arial", 16, "bold"))
        self.lbl_title_ana_img.pack(pady=(5, 5))
        
        self.lbl_img_analysis_view = ctk.CTkLabel(self.frame_analysis_img, text="No Image processed")
        self.lbl_img_analysis_view.pack(expand=True, fill="both")

        # --- Right Side: Editor & Results ---
        self.frame_analysis_tools = ctk.CTkFrame(self.tab_analysis, fg_color="transparent")
        self.frame_analysis_tools.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.frame_analysis_tools.grid_columnconfigure(0, weight=1)
        self.frame_analysis_tools.grid_rowconfigure(1, weight=1) # Editor ยืด
        self.frame_analysis_tools.grid_rowconfigure(4, weight=1) # Results ยืด

        # 1. Netlist Editor Section
        self.lbl_editor_title = ctk.CTkLabel(self.frame_analysis_tools, text="📝 Netlist Editor", font=("Arial", 18, "bold"))
        self.lbl_editor_title.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.editor_scroll = ctk.CTkScrollableFrame(self.frame_analysis_tools, label_text="Component List")
        self.editor_scroll.grid(row=1, column=0, sticky="nsew") 
        
        # Headers Editor
        headers = ["Comp", "Node +", "Node -", "Value", "Status"]
        for idx, h in enumerate(headers):
            ctk.CTkLabel(self.editor_scroll, text=h, font=("Arial", 12, "bold"), text_color="#3498DB").grid(row=0, column=idx, padx=5, pady=5)

        # 2. Actions
        self.frame_actions = ctk.CTkFrame(self.frame_analysis_tools)
        self.frame_actions.grid(row=2, column=0, sticky="ew", pady=15)
        
        self.btn_add_comp = ctk.CTkButton(self.frame_actions, text="+ Add Manual Component", command=self.add_manual_row, fg_color="#5D6D7E", height=35)
        self.btn_add_comp.pack(side="left", padx=5, expand=True, fill="x")
        
        self.btn_calc = ctk.CTkButton(self.frame_actions, text="▶ RUN ANALYSIS", command=self.run_lcapy_analysis, fg_color="#27AE60", hover_color="#2ECC71", height=35, font=("Arial", 14, "bold"))
        self.btn_calc.pack(side="right", padx=5, expand=True, fill="x")

        # 3. Results Section
        self.lbl_result_title = ctk.CTkLabel(self.frame_analysis_tools, text="📊 Analysis Results", font=("Arial", 18, "bold"))
        self.lbl_result_title.grid(row=3, column=0, sticky="w", pady=(10, 5))
        
        # ใช้ ScrollableFrame แทน Textbox เพื่อทำเป็นตาราง
        self.result_scroll = ctk.CTkScrollableFrame(self.frame_analysis_tools, label_text="Output Parameters")
        self.result_scroll.grid(row=4, column=0, sticky="nsew", pady=5)
        
        # ตั้งค่า Column Grid ของ Result
        self.result_scroll.grid_columnconfigure(0, weight=2) # Parameter Name (กว้างหน่อย)
        self.result_scroll.grid_columnconfigure(1, weight=2) # Value (กว้างหน่อย)
        self.result_scroll.grid_columnconfigure(2, weight=1) # Unit (แคบหน่อย)

    # ==========================
    # Editor Logic
    # ==========================
    def add_netlist_row(self, name, n1, n2, value, is_ai_generated=False):
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
        entries['val']  = make_entry(3, value, 100)
        
        # Action Button
        btn_action = None
        if is_ai_generated:
            btn_action = ctk.CTkButton(self.editor_scroll, text="ON", width=50, fg_color="#27AE60",
                                       command=lambda: self.toggle_ai_row(entries, btn_action))
        else:
            btn_action = ctk.CTkButton(self.editor_scroll, text="❌", width=50, fg_color="#C0392B", 
                                       command=lambda: self.delete_manual_row(entries, btn_action))

        btn_action.grid(row=row_idx, column=4, padx=5, pady=3)
        self.netlist_rows.append({'entries': entries, 'btn': btn_action, 'is_ai': is_ai_generated, 'active': True})

    def add_manual_row(self):
        self.add_netlist_row("R_new", "1", "0", "1k", is_ai_generated=False)

    def delete_manual_row(self, entries, btn_obj):
        for widget in entries.values(): widget.destroy()
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
            for entry in entries.values():
                entry.configure(state="normal" if state else "disabled", 
                                text_color="white" if state else "gray")

    def populate_editor_from_text(self, netlist_text):
        for row in self.netlist_rows:
            for w in row['entries'].values(): w.destroy()
            row['btn'].destroy()
        self.netlist_rows.clear()
        
        lines = netlist_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith(('*', '#', '.')) or "Auto-G" in line or "Netlist" in line or "Comp" in line:
                continue

            parts = line.split()
            if len(parts) >= 4:
                self.add_netlist_row(parts[0], parts[1], parts[2], " ".join(parts[3:]), is_ai_generated=True)
            elif len(parts) == 3: 
                self.add_netlist_row(parts[0], parts[1], parts[2], "?", is_ai_generated=True)

    # ==========================
    # Logic & Pretty Result Display
    # ==========================
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
            
            # --- FILTER SECTION: กรองบรรทัดที่ไม่ต้องการออก ---
            # 1. ข้ามบรรทัด Processing Netlist
            if "Processing Netlist" in line:
                continue
            
            # 2. ข้ามบรรทัดที่เป็น Netlist (เช่น C1 1 2 4.7)
            # หลักการ: ถ้าไม่มีเครื่องหมาย '=' หรือ ':' และมีส่วนประกอบมากกว่า 2 ส่วน -> ให้ถือว่าเป็น Netlist และข้ามไป
            if "=" not in line and ":" not in line:
                if len(line.split()) >= 3: 
                    continue
            # ------------------------------------------------
            
            # Parsing Logic (เฉพาะบรรทัดที่เป็นผลลัพธ์)
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
                # กรณีที่เป็น Header (มี :) ให้แสดง
                if line.endswith(':'): 
                    lbl = ctk.CTkLabel(self.result_scroll, text=line, font=("Arial", 12, "bold"), text_color="#3498DB")
                    lbl.grid(row=row_idx, column=0, columnspan=3, sticky="w", pady=(10,2), padx=5)
                    self.result_widgets.append(lbl)
                    row_idx += 1
                else:
                    # กรณีอื่นๆ ที่ไม่ใช่ Netlist แต่หลุดมา (ถ้ามี)
                    pass 

    def add_result_row_widget(self, row, param, val, unit):
        # 1. Parameter Name (Entry Readonly)
        e_param = ctk.CTkEntry(self.result_scroll, width=120, font=("Arial", 13, "bold"))
        e_param.insert(0, param)
        e_param.configure(state="readonly")
        e_param.grid(row=row, column=0, padx=3, pady=3, sticky="ew")
        
        # 2. Value (Entry Readonly - Green Color)
        e_val = ctk.CTkEntry(self.result_scroll, width=120, font=("Consolas", 13, "bold"), text_color="#2ECC71")
        e_val.insert(0, val)
        e_val.configure(state="readonly")
        e_val.grid(row=row, column=1, padx=3, pady=3, sticky="ew")
        
        # 3. Unit (Label)
        l_unit = ctk.CTkLabel(self.result_scroll, text=unit, font=("Arial", 12))
        l_unit.grid(row=row, column=2, padx=3, pady=3)
        
        self.result_widgets.extend([e_param, e_val, l_unit])

    # ==========================
    # Image & Main Process
    # ==========================
    def create_image_label(self, parent, title, col):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(frame, text=title, font=("Arial", 12, "bold")).pack(pady=5)
        lbl_img = ctk.CTkLabel(frame, text="")
        lbl_img.pack(expand=True)
        return lbl_img

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.jpeg")])
        if file_path:
            self.current_image_path = file_path
            self.show_image(cv2.imread(file_path), self.lbl_img_detect)
            self.btn_process.configure(state="normal", fg_color="#D35400")
            self.status_label.configure(text="Image Loaded")
            self.lbl_img_analysis_view.configure(image=None, text="Pending Process...")
            self.populate_editor_from_text("")
            self.clear_results()

    def show_image(self, cv_img, label_widget):
        if cv_img is None: return
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(cv_img)
        
        h_frame = 400 
        w_frame = 500
        ctk_img = ctk.CTkImage(light_image=im_pil, dark_image=im_pil, size=(w_frame, h_frame))
        label_widget.configure(image=ctk_img, text="")
        label_widget.image = ctk_img

    def start_processing(self):
        threading.Thread(target=self.process_thread, daemon=True).start()

    def process_thread(self):
        try:
            self.status_label.configure(text="⏳ Processing AI...")
            detect_plot, components = self.detector.detect(self.current_image_path)
            
            img = cv2.imread(self.current_image_path)
            full_ocr = self.ocr.ocr.ocr(img, cls=True) 
            formatted_ocr = []
            if full_ocr and full_ocr[0]:
                for line in full_ocr[0]:
                    pts = line[0]
                    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                    formatted_ocr.append({'text': line[1][0], 'box': [min(xs), min(ys), max(xs), max(ys)], 'conf': line[1][1]})

            vis, final, netlist = self.processor.process_nodes(img, components, text_data=formatted_ocr)
            self.after(0, lambda: self.update_ui_results(detect_plot, vis, final, netlist))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.btn_process.configure(state="normal"))
            self.after(0, lambda: self.status_label.configure(text="Ready"))

    def update_ui_results(self, detect_img, raw_img, schematic_img, netlist_text):
        self.show_image(detect_img, self.lbl_img_detect)
        self.show_image(raw_img, self.lbl_img_raw)
        self.show_image(schematic_img, self.lbl_img_schematic)
        self.show_image(schematic_img, self.lbl_img_analysis_view)
        self.populate_editor_from_text(netlist_text)
        self.main_tab.set("Circuit Analysis")

if __name__ == "__main__":
    app = CircuitApp()
    app.mainloop()