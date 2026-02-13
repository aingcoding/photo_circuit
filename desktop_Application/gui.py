import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import cv2
import os
import threading
import sys

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
    # IMPORT Lcapy Module
    from Lcapy.circuit_analysis import analyze_netlist 
except ImportError as e:
    print(f"Import Error: {e}")

MODEL_PATH = os.path.join(project_root, 'yolo', 'weights', 'best.pt')

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CircuitApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Circuit Recognition & Analysis System")
        self.geometry("1400x800")

        # Initialize Engines
        try:
            self.detector = YoloDetector(MODEL_PATH)
            self.processor = CircuitProcessor()
            self.ocr = CircuitOCR()
            print("System Ready.")
        except Exception as e:
            messagebox.showerror("Init Error", str(e))

        self.current_image_path = None
        self.setup_ui()

    def setup_ui(self):
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Left Panel (Controls) ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.lbl_title = ctk.CTkLabel(self.sidebar, text="Circuit AI", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=20)

        self.btn_upload = ctk.CTkButton(self.sidebar, text="📂 Upload Image", command=self.upload_image)
        self.btn_upload.pack(pady=10)

        self.btn_process = ctk.CTkButton(self.sidebar, text="⚡ Process Circuit", command=self.start_processing, state="disabled")
        self.btn_process.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(self.sidebar, text="Waiting...", text_color="gray")
        self.status_label.pack(pady=20, side="bottom")

        # --- Main Area (Tabs) ---
        self.main_tab = ctk.CTkTabview(self)
        self.main_tab.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.tab_visual = self.main_tab.add("Visualization")
        self.tab_analysis = self.main_tab.add("Circuit Analysis (Lcapy)")

        # === TAB 1: Visualization ===
        self.tab_visual.grid_columnconfigure((0,1,2), weight=1)
        self.lbl_img_detect = self.create_image_label(self.tab_visual, "YOLO Detection", 0)
        self.lbl_img_raw = self.create_image_label(self.tab_visual, "Cleaned Circuit", 1)
        self.lbl_img_schematic = self.create_image_label(self.tab_visual, "Node Analysis", 2)

        # === TAB 2: Analysis ===
        self.tab_analysis.grid_columnconfigure(0, weight=1)
        self.tab_analysis.grid_columnconfigure(1, weight=1)
        self.tab_analysis.grid_rowconfigure(1, weight=1)

        lbl_editor = ctk.CTkLabel(self.tab_analysis, text="📝 Netlist Editor (Editable)", font=("Arial", 14, "bold"))
        lbl_editor.grid(row=0, column=0, pady=5)
        
        self.txt_netlist = ctk.CTkTextbox(self.tab_analysis, font=("Consolas", 14))
        self.txt_netlist.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.txt_netlist.insert("0.0", "# Netlist will appear here after processing...")

        self.btn_calc = ctk.CTkButton(self.tab_analysis, text="▶ Run Analysis", command=self.run_lcapy_analysis, fg_color="green")
        self.btn_calc.grid(row=2, column=0, pady=10)

        lbl_result = ctk.CTkLabel(self.tab_analysis, text="📊 Analysis Results", font=("Arial", 14, "bold"))
        lbl_result.grid(row=0, column=1, pady=5)

        self.txt_result = ctk.CTkTextbox(self.tab_analysis, font=("Consolas", 14), fg_color="#1e1e1e")
        self.txt_result.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        self.txt_result.configure(state="disabled")

    def create_image_label(self, parent, title, col):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        lbl_title = ctk.CTkLabel(frame, text=title)
        lbl_title.pack()
        lbl_img = ctk.CTkLabel(frame, text="")
        lbl_img.pack(expand=True)
        return lbl_img

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.jpeg")])
        if file_path:
            self.current_image_path = file_path
            self.show_image(cv2.imread(file_path), self.lbl_img_detect)
            self.btn_process.configure(state="normal")
            self.status_label.configure(text="Image Loaded")

    def show_image(self, cv_img, label_widget):
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(cv_img)
        h_frame = 300
        w_frame = 400
        ctk_img = ctk.CTkImage(light_image=im_pil, dark_image=im_pil, size=(w_frame, h_frame))
        label_widget.configure(image=ctk_img, text="")
        label_widget.image = ctk_img

    def start_processing(self):
        threading.Thread(target=self.process_thread, daemon=True).start()

    def process_thread(self):
        try:
            self.status_label.configure(text="⏳ Processing...")
            
            # 1. YOLO
            detect_plot, components = self.detector.detect(self.current_image_path)
            
            # 2. OCR (ใช้ OCR อ่านภาพเต็ม แล้วส่งข้อมูลให้ Logic จัดการตัดเอง)
            img = cv2.imread(self.current_image_path)
            full_ocr_results = self.ocr.ocr.ocr(img, cls=True)
            
            formatted_ocr = []
            if full_ocr_results and full_ocr_results[0]:
                for line in full_ocr_results[0]:
                    box_points = line[0]
                    xs = [p[0] for p in box_points]
                    ys = [p[1] for p in box_points]
                    formatted_ocr.append({
                        'text': line[1][0],
                        # แปลงเป็น [x1, y1, x2, y2] เพื่อให้ cv2.rectangle ใช้งานได้
                        'box': [min(xs), min(ys), max(xs), max(ys)],
                        'conf': line[1][1]
                    })

            # 3. Logic & Netlist Generation
            raw_node_vis, final_img, netlist_spice = self.processor.process_nodes(
                img, 
                components, 
                text_data=formatted_ocr
            )

            self.after(0, lambda: self.update_ui_results(detect_plot, raw_node_vis, final_img, netlist_spice))

        except Exception as e:
            # 🔥 FIX: เก็บ Error message ใส่ตัวแปร string ก่อนส่งเข้า lambda
            err_msg = str(e)
            print(f"Error: {err_msg}")
            self.after(0, lambda msg=err_msg: messagebox.showerror("Processing Error", msg))
            self.after(0, lambda: self.status_label.configure(text="Error occurred"))
        finally:
            self.after(0, lambda: self.btn_process.configure(state="normal"))
            self.after(0, lambda: self.status_label.configure(text="Done"))

    def update_ui_results(self, detect_img, raw_img, schematic_img, netlist_text):
        self.show_image(detect_img, self.lbl_img_detect)
        self.show_image(raw_img, self.lbl_img_raw)
        self.show_image(schematic_img, self.lbl_img_schematic)
        
        self.txt_netlist.delete("0.0", "end")
        self.txt_netlist.insert("0.0", netlist_text)
        
        self.main_tab.set("Circuit Analysis (Lcapy)")

    def run_lcapy_analysis(self):
        netlist_str = self.txt_netlist.get("0.0", "end")
        
        self.txt_result.configure(state="normal")
        self.txt_result.delete("0.0", "end")
        self.txt_result.insert("0.0", "⏳ Calculating...\n")
        self.txt_result.configure(state="disabled")

        def run_task():
            result_str = analyze_netlist(netlist_str)
            self.after(0, lambda: self.show_analysis_result(result_str))

        threading.Thread(target=run_task, daemon=True).start()

    def show_analysis_result(self, result_str):
        self.txt_result.configure(state="normal")
        self.txt_result.delete("0.0", "end")
        self.txt_result.insert("0.0", result_str)
        self.txt_result.configure(state="disabled")

if __name__ == "__main__":
    app = CircuitApp()
    app.mainloop()