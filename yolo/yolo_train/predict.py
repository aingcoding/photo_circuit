from ultralytics import YOLO
import os

def main():
    model_path = r"C:\Users\ACER\OneDrive\Desktop\AI_project\circuit_detect_v132\weights\best.pt"
    conf_val =0.5
    iou_val = 0.6
    
    folder_name = os.path.basename(os.path.dirname(os.path.dirname(model_path)))
    
    model_ver = folder_name.split('_v')[-1][-2:] 
    
    custom_name = f"model{model_ver}_conf{conf_val}_iou{iou_val}"
    
    best_model = YOLO(model_path)
    
    metrics = best_model.val(
        data=r"C:\Users\ACER\Downloads\ohm-micro.v11i.yolov8\data.yaml",
        conf=conf_val,    
        iou=iou_val,     
        project=r'C:\Users\ACER\OneDrive\Desktop\AI_project',
        name=custom_name
    )
    
    print(f"Validation Complete! Results saved in: {custom_name}")

if __name__ == '__main__':
    main()