import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import cv2
import os
import threading
import sys

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
    # Import OCR Module
    from OCR.ocr_engine import CircuitOCR 
except ImportError as e:
    print(f"Import Error: {e}")

# ==========================================
# ⚙️ MODEL CONFIGURATION
# ==========================================
MODEL_PATH = os.path.join(project_root, 'yolo', 'weights', 'best.pt')

# ==========================================
# GUI CLASS
# ==========================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CircuitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Setup Logic Class ---
        self.detector = None 
        self.ocr_engine = None  # ตัวแปรสำหรับ OCR
        self.processor = CircuitProcessor()

        # --- Setup Window ---
        self.title("AI Circuit Analyzer Pro (OCR Integration)")
        self.geometry("1300x850")
        
        self.current_image_path = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === Sidebar ===
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="🔌 Circuit AI Pro", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.pack(padx=20, pady=(20, 10))

        self.btn_upload = ctk.CTkButton(self.sidebar, text="📂 เลือกรูปภาพ", command=self.select_image)
        self.btn_upload.pack(padx=20, pady=10)

        self.btn_process = ctk.CTkButton(self.sidebar, text="🚀 วิเคราะห์วงจร", command=self.start_processing_thread, state="disabled", fg_color="green")
        self.btn_process.pack(padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.sidebar, text="รอเลือกรูป...", text_color="gray")
        self.status_label.pack(padx=20, pady=10)

        self.netlist_label = ctk.CTkLabel(self.sidebar, text="📝 Netlist / Values:", anchor="w")
        self.netlist_label.pack(padx=20, pady=(30, 5), anchor="w")
        
        self.textbox = ctk.CTkTextbox(self.sidebar, width=230)
        self.textbox.pack(padx=10, pady=5, fill="y", expand=True)

        # === Main Area (Tabs) ===
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.tab_orig = self.tabview.add("Original Image")
        self.tab_detect = self.tabview.add("AI Detection")
        self.tab_raw = self.tabview.add("Cleaned (OCR Masked)") # เปลี่ยนชื่อ Tab ให้สื่อความหมาย
        self.tab_schematic = self.tabview.add("Final Schematic")
        
        self.lbl_img_orig = self.create_image_label(self.tab_orig)
        self.lbl_img_detect = self.create_image_label(self.tab_detect)
        self.lbl_img_raw = self.create_image_label(self.tab_raw)
        self.lbl_img_schematic = self.create_image_label(self.tab_schematic)

    def create_image_label(self, parent):
        lbl = ctk.CTkLabel(parent, text="รอประมวลผล...")
        lbl.pack(expand=True)
        return lbl

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.jpeg")])
        if file_path:
            self.current_image_path = file_path
            self.status_label.configure(text=f"เลือก: {os.path.basename(file_path)}")
            self.btn_process.configure(state="normal")
            self.show_image(file_path, self.lbl_img_orig)
            
            # Reset UI
            self.lbl_img_detect.configure(image=None, text="รอประมวลผล...")
            self.lbl_img_raw.configure(image=None, text="รอประมวลผล...")
            self.lbl_img_schematic.configure(image=None, text="รอประมวลผล...")
            self.textbox.delete("0.0", "end")

    def show_image(self, img_source, label_widget):
        if isinstance(img_source, str):
            img = Image.open(img_source)
        else:
            img = cv2.cvtColor(img_source, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            
        w, h = img.size
        ratio = min(900/w, 700/h)
        new_w, new_h = int(w*ratio), int(h*ratio)
        
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
        label_widget.configure(image=ctk_img, text="")
        label_widget.image = ctk_img

    def start_processing_thread(self):
        self.status_label.configure(text="⏳ กำลังวิเคราะห์...", text_color="orange")
        self.btn_process.configure(state="disabled")
        threading.Thread(target=self.process_logic, daemon=True).start()

    def process_logic(self):
        try:
            # 1. Load Model & Run YOLO
            if self.detector is None:
                if not os.path.exists(MODEL_PATH):
                     raise FileNotFoundError(f"Model not found at: {MODEL_PATH}")
                self.detector = YoloDetector(MODEL_PATH)
            
            detect_plot, components = self.detector.detect(self.current_image_path)
            
            # ==================================================
            # 2. Run OCR (อ่านค่า + กรองตัวใกล้)
            # ==================================================
            self.status_label.configure(text="⏳ กำลังอ่าน OCR...")
            
            if self.ocr_engine is None:
                self.ocr_engine = CircuitOCR() # โหลดครั้งเดียว
            
            # ส่ง components ไปให้ OCR ช่วยกรอง
            ocr_results = self.ocr_engine.scan_and_filter(self.current_image_path, components)
            
            # ==================================================
            # 3. Run OpenCV Logic (ส่ง Text Data ไปด้วย)
            # ==================================================
            self.status_label.configure(text="⏳ กำลังประมวลผลวงจร...")
            original_img = cv2.imread(self.current_image_path)
            
            # ส่ง ocr_results เข้าไปให้ processor ถมขาว
            raw_node_vis, final_img, netlist_text = self.processor.process_nodes(
                original_img, 
                components, 
                text_data=ocr_results # <--- ส่งข้อมูล Text ตรงนี้
            )

            # 4. Update UI
            self.after(0, lambda: self.update_ui_results(detect_plot, raw_node_vis, final_img, netlist_text))

        except Exception as e:
            print(f"Error: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"เกิดข้อผิดพลาด:\n{str(e)}"))
            self.after(0, lambda: self.btn_process.configure(state="normal"))

    def update_ui_results(self, detect_img, raw_img, schematic_img, netlist_text):
        self.show_image(detect_img, self.lbl_img_detect)
        self.show_image(raw_img, self.lbl_img_raw)
        self.show_image(schematic_img, self.lbl_img_schematic)
        
        self.textbox.insert("0.0", netlist_text)
        self.status_label.configure(text="✅ เสร็จสิ้น", text_color="green")
        self.btn_process.configure(state="normal")
        self.tabview.set("Cleaned (OCR Masked)") # สลับไปดู Tab นี้เพื่อเช็คการถมขาว

if __name__ == "__main__":
    app = CircuitApp()
    app.mainloop()