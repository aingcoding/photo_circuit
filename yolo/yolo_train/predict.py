from ultralytics import YOLO
import os

def main():
    # 1. กำหนดค่าต่างๆ
    model_path = r"C:\Users\ACER\OneDrive\Desktop\AI_project\circuit_detect_v132\weights\best.pt"
    conf_val =0.5
    iou_val = 0.6
    
    # 2. ดึงชื่อโฟลเดอร์ (circuit_detect_v132)
    folder_name = os.path.basename(os.path.dirname(os.path.dirname(model_path)))
    
    # 3. ตัดเอาแค่เลข 2 ตัวสุดท้าย (เช่น 132 -> 32)
    # folder_name.split('_v')[-1] จะได้ '132' แล้วเราใช้ [-2:] เพื่อเอา 2 ตัวท้าย
    model_ver = folder_name.split('_v')[-1][-2:] 
    
    # 4. สร้างชื่อตามรูปแบบ: model32_conf0.25_iou0.1
    custom_name = f"model{model_ver}_conf{conf_val}_iou{iou_val}"
    
    # โหลดโมเดล
    best_model = YOLO(model_path)
    
    # สั่ง Validation
    metrics = best_model.val(
        data=r"C:\Users\ACER\Downloads\ohm-micro.v11i.yolov8\data.yaml",
        #conf=conf_val,    
        iou=iou_val,     
        project=r'C:\Users\ACER\OneDrive\Desktop\AI_project',
        name=custom_name
    )
    
    print(f"Validation Complete! Results saved in: {custom_name}")

if __name__ == '__main__':
    main()