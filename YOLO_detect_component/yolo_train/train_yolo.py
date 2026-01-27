from ultralytics import YOLO

def main():
    # 1. โหลดโมเดล
    model = YOLO('yolov8n-cls.pt') 

    # 2. สั่งเทรน (Training)
    results = model.train(
        data=r'C:\Users\ACER\OneDrive\Desktop\AI_project\symbol',
        epochs=50,
        imgsz=128,
        batch=16,
        augment=True,
        
        # --- ส่วนที่เพิ่มเข้ามา ---
        # กำหนดโฟลเดอร์ปลายทางที่ต้องการเก็บผลลัพธ์ (อย่าลืมใส่ r ข้างหน้า)
        project=r"C:\Users\ACER\Downloads\Screenshot 2026-01-27 230352.png", 
        
        # ชื่อโฟลเดอร์ย่อยของการเทรนรอบนี้
        name='my_electronic_model'
    )

    print("Training Finished!")

if __name__ == '__main__':
    main()