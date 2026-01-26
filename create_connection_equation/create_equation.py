temporary = [] #รอ model ส่งข้อมูลเข้ามา
circuit_netlist = []
#comp_type,comp_name,comp_value,comp_unit,comp_conn1,comp_conn2

for item in temporary:
    # 1. สร้าง Dictionary สำหรับอุปกรณ์ตัวนี้ตัวเดียว
    component_data = {}
    component_data["comp_type_3"] = item[0]
    component_data["comp_name"] = item[1]
    component_data["comp_unit"] = item[2]
    component_data["comp_conn1"] = item[3]
    component_data["comp_conn2"] = item[4]
    
    # 2. ยัด Dictionary ก้อนนี้ใส่เข้าไปใน List หลัก
    circuit_netlist.append(component_data)

import json
print(json.dumps(circuit_netlist, indent=2))
