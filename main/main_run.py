import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.append(project_root)
    
print(f"Project Root added: {project_root}")

from desktop_Application.gui import CircuitApp

if __name__ == "__main__":
    app = CircuitApp()
    app.mainloop()