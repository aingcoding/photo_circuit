from ultralytics import YOLO

def main():
    # 1. โหลดโมเดลเริ่มต้น
    # ใช้ 'yolov8n-cls.pt' (Nano Classification) ตัวเล็กสุดและเร็วสุด เหมาะกับงานง่ายๆ
    model = YOLO('yolov8n-cls.pt') 

    # 2. สั่งเทรน (Training)
    results = model.train(
        data=r'C:\Users\ACER\OneDrive\Desktop\AI_homework\Project_AI\symbol',  # <-- แก้ตรงนี้เป็น path โฟลเดอร์ dataset ของคุณ
        epochs=50,                    # จำนวนรอบการเทรน (50 รอบกำลังดีสำหรับข้อมูลน้อย)
        imgsz=128,                    # ขนาดภาพ (128x128 px เหมาะกับไอคอนสัญลักษณ์)
        batch=16,                     # จำนวนภาพที่ป้อนเข้าต่อครั้ง
        augment=True,                 # เปิดใช้ Augmentation อัตโนมัติ (หมุน, ปรับแสง) ของ YOLO
        name='my_electronic_model'    # ชื่อโปรเจกต์ (ผลลัพธ์จะไปอยู่ที่ runs/classify/my_electronic_model)
    )

    # 3. ตรวจสอบผลลัพธ์เบื้องต้น
    print("Training Finished!")

if __name__ == '__main__':
    main()