from ultralytics import YOLO

def main():
    # 1. โหลดโมเดล (สำคัญ: ต้องใช้ yolov8n.pt เฉยๆ ห้ามมี -cls)
    # นี่คือโมเดลสำหรับ Object Detection
    model = YOLO('yolov8s.pt') 

    # 2. เริ่มการเทรน
    results = model.train(
        # ใส่ Path ของไฟล์ data.yaml ที่เราสร้างในขั้นตอนที่ 2
        data=r"C:\Users\ACER\OneDrive\Desktop\AI_project\ohm-micro.v11i.yolov8\data.yaml",
        
        epochs=100,      # รอบการเทรน (งาน Detection ยากกว่า Classify ควรเทรนเยอะหน่อย)
        imgsz=640,       # ขนาดภาพ (640 คือมาตรฐานของ Detection ภาพวงจรควรใช้ 640 หรือสูงกว่า)
        batch=16,        # จำนวนภาพต่อรอบ
        
        # ชื่อโปรเจกต์ที่จะเซฟผลลัพธ์
        project=r'C:\Users\ACER\OneDrive\Desktop\AI_project',
        name='circuit_detect_v1',
        
        device=0,      # ถ้ามีการ์ดจอ Nvidia ให้เปิดบรรทัดนี้ (ถ้าใช้ CPU ก็ปิดไว้)
        patience=25,     # ถ้าเทรนไป 25 รอบแล้วไม่ฉลาดขึ้น ให้หยุดก่อน (กันเสียเวลา)
        augment=True     # เปิดการหมุนภาพ/กลับด้าน ช่วยให้เก่งขึ้น
    )

    print("Training Complete!")

    # 3. ลองเทสโมเดล (Validation) ดูผลลัพธ์คร่าวๆ
    model.val()

if __name__ == '__main__':
    main()