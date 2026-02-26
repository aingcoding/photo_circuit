from lcapy import Circuit
import io
import sympy as sp

def analyze_netlist(netlist_str):
    log_output = []
    
    def log(msg):
        log_output.append(msg)

    def clean_expr(expr):
        try:
            expr_sym = sp.sympify(str(expr))
            if isinstance(expr_sym, sp.Piecewise):
                for e, cond in expr_sym.args:
                    if cond is True or (hasattr(cond, 'lhs') and cond.lhs == sp.Symbol('t')):
                        return sp.simplify(e)
            return sp.simplify(expr_sym)
        except:
            return expr

    try:
        lines = [line for line in netlist_str.split('\n') if line.strip() and not line.startswith('#')]
        clean_netlist = "\n".join(lines)
        
        log(f"--- Processing Netlist ({len(lines)} components) ---")
        log(clean_netlist)
        log("------------------------------------------------")

        cct = Circuit(clean_netlist)
        
        log(">> Time-Domain Analysis (t ≥ 0):")
        
        if '0' not in cct.nodes:
            log("Warning: No Ground Node (0) found.")

        node_list = sorted([str(n) for n in cct.nodes if str(n) != '0'])
        
        for n in node_list:
            try:
                val_time = cct[n].V.time()
                val_show = clean_expr(val_time)
                
                try:
                    val_float = float(val_show)
                    log(f"  V({n}, t) \t= {val_float:.4f} V")
                except:
                    log(f"  V({n}, t) \t= {val_show} V")
            except Exception as e:
                log(f"  V({n}, t) \t= Error ({e})")

        log("\n>> Branch Currents (t ≥ 0):")
        for key in cct.elements:
            try:
                if key[0] in ['W', 'P', 'O']: continue 
                
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