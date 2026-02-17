import sys
import os

# ---  FIX PATH SYSTEM (ส่วนสำคัญที่สุด) ---
# 1. หาตำแหน่งของไฟล์ main_run.py ปัจจุบัน (.../main/main_run.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. ถอยหลัง 1 ขั้น เพื่อไปหาโฟลเดอร์ 'application_program' (Project Root)
project_root = os.path.dirname(current_dir)

# 3. บอก Python ว่า "เฮ้ย ถ้าหาไฟล์ไหนไม่เจอ ให้มาหาใน application_program นะ"
if project_root not in sys.path:
    sys.path.append(project_root)
    
# (Debug) ปริ้นท์ออกมาดูว่า Path ถูกไหม
print(f"Project Root added: {project_root}")
# ------------------------------------------

# ตอนนี้ Python จะรู้จัก desktop_Application, yolo, open_cv แล้ว
from desktop_Application.gui import CircuitApp

if __name__ == "__main__":
    app = CircuitApp()
    app.mainloop()