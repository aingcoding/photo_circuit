from lcapy import Circuit
import io
import sympy as sp

def analyze_netlist(netlist_str):
    log_output = []
    
    def log(msg):
        log_output.append(msg)

    # ฟังก์ชันช่วยดึงเฉพาะสมการสำหรับ t >= 0 (เหมือน strip_piecewise ในโค้ดบน)
    def clean_expr(expr):
        try:
            expr_sym = sp.sympify(str(expr))
            if isinstance(expr_sym, sp.Piecewise):
                for e, cond in expr_sym.args:
                    # เลือกเงื่อนไขที่เป็น True หรือ t >= 0
                    if cond is True or (hasattr(cond, 'lhs') and cond.lhs == sp.Symbol('t')):
                        return sp.simplify(e)
            return sp.simplify(expr_sym)
        except:
            return expr

    try:
        # 1. Clean Netlist string
        lines = [line for line in netlist_str.split('\n') if line.strip() and not line.startswith('#')]
        clean_netlist = "\n".join(lines)
        
        log(f"--- Processing Netlist ({len(lines)} components) ---")
        log(clean_netlist)
        log("------------------------------------------------")

        # 2. Load Circuit
        cct = Circuit(clean_netlist)
        
        # 3. Time-Domain Analysis (แทนที่ DC Analysis เดิม)
        log(">> Time-Domain Analysis (t ≥ 0):")
        
        if '0' not in cct.nodes:
            log("⚠️ Warning: No Ground Node (0) found.")

        # แสดง Voltage ทุก Node ในรูปสมการเวลา
        node_list = sorted([str(n) for n in cct.nodes if str(n) != '0'])
        
        for n in node_list:
            try:
                # เปลี่ยนจาก .V เป็น .V.time()
                val_time = cct[n].V.time()
                val_show = clean_expr(val_time)
                
                # พยายามเช็คว่าเป็นค่าคงที่หรือไม่ ถ้าใช่ให้โชว์ทศนิยม
                try:
                    val_float = float(val_show)
                    log(f"  V({n}, t) \t= {val_float:.4f} V")
                except:
                    log(f"  V({n}, t) \t= {val_show} V")
            except Exception as e:
                log(f"  V({n}, t) \t= Error ({e})")

        # แสดงกระแส I ของแต่ละอุปกรณ์ในรูปสมการเวลา
        log("\n>> Branch Currents (t ≥ 0):")
        for key in cct.elements:
            try:
                if key[0] in ['W', 'P', 'O']: continue 
                
                # เปลี่ยนจาก .I เป็น .I.time()
                curr_time = cct[key].I.time()
                curr_show = clean_expr(curr_time)

                try:
                    curr_float = float(curr_show)
                    log(f"  I({key}, t) \t= {curr_float:.6f} A")
                except:
                    log(f"  I({key}, t) \t= {curr_show} A")
            except:
                pass

        return "\n".join(log_output)

    except Exception as e:
        return f"Analysis Failed:\n{str(e)}\n\nCheck your netlist connections."