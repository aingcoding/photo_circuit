from ultralytics import YOLO

# โหลดโมเดลแค่ครั้งเดียวตอนเริ่มโปรแกรม (จะได้ไม่ช้า)
# แนะนำให้ใช้ Absolute Path (Path เต็ม) เพื่อป้องกันปัญหาหาไฟล์ไม่เจอ
model = YOLO(r"C:\Users\ACER\OneDrive\Desktop\AI_project\my_electronic_model\weights\best.pt") 

def predict_electronic_symbol(image_path):
    """
    ฟังก์ชันสำหรับทายชื่อสัญลักษณ์
    Input: path ของรูปภาพ
    Output: ชื่อสัญลักษณ์ (str), ความมั่นใจ (float)
    """
    results = model(image_path, verbose=False) # verbose=False ปิดการพ่น log รกๆ
    
    for result in results:
        top1_index = result.probs.top1
        name = result.names[top1_index]
        score = result.probs.top1conf.item()
        return name, score
    
    return "Unknown", 0.0

# --- ตัวอย่างการเรียกใช้งาน ---
my_img = r"C:\Users\ACER\Downloads\Screenshot 2026-01-27 231447.png"
symbol_name, confidence = predict_electronic_symbol(my_img)

if confidence > 0.8:
    print(f"เจออุปกรณ์: {symbol_name} (มั่นใจ {confidence:.2f})")
    # ทำงานต่อ... เช่น บันทึกลง Database หรือ คำนวณค่า
else:
    print("ไม่แน่ใจว่าเป็นรูปอะไร")