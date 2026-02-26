# CircuitVision

<img width="1600" height="800" alt="image" src="https://github.com/user-attachments/assets/70a90af7-12fa-45e2-bf69-b6c378077d84" />

## About The Project
This project is an automated system that converts photographs or hand-drawn sketches of electrical circuits into computer-understandable and simulatable netlists. 

It combines the power of **Artificial Intelligence (Object Detection & OCR)** to locate components and read their values, and **Computer Vision (Image Processing)** to trace wires and junction nodes. The extracted topology is then seamlessly passed to a circuit analysis library to perform mathematical and electrical simulations.

## Key Features
* **Component Detection:** Accurately locates standard electrical components (Resistors, Capacitors, Inductors) within the image.
* **Value Extraction:** Reads and parses text to extract numerical values and metric prefixes (e.g., k, m, u) using Optical Character Recognition.
* **Wire & Node Extraction:** Analyzes wire structures, removes visual noise, heals broken lines (Morphological transformations), and precisely maps electrical connections (Topology Mapping).
* **Netlist Generation:** Translates the extracted visual and spatial data into a standard Netlist format for circuit simulation.

## Built With 
This project is built using the following core technologies:

** AI & Machine Learning:**
* **`YOLO (Ultralytics)`** - Used for Object Detection to identify and bound circuit components (R, C, L).
* **`OCR (Optical Character Recognition)`** - Used for text recognition to extract component values from the image.

** Computer Vision & Data Processing:**
* **`OpenCV (cv2)`** - The core image processing engine. Used for image cleaning (masking objects), morphological operations (dilation to heal wires), and Connected Components labeling to extract independent electrical nodes.
* **`re` (Regular Expressions)** - Used for strict data cleaning and pattern matching to parse raw, noisy OCR text into clean numeric values and multipliers.

** Circuit Analysis & Mathematics:**
* **`Lcapy`** - (Linear Circuit Analysis with Python) Used to generate the Netlist, draw clean schematics, and perform linear circuit simulations.
* **`SymPy`** - Works under the hood of Lcapy to handle symbolic mathematics, allowing algebraic circuit analysis even with unknown variables.

## How It Works (Pipeline)
1. **AI Detection:** YOLO detects the components' bounding boxes, while OCR reads the associated text values.
2. **Image Cleaning:** OpenCV masks (erases) the detected components and text from the image, leaving only the bare wire connections.
3. **Node Mapping:** OpenCV applies binarization and morphological dilation to heal the lines, followed by Connected Components analysis to identify and label unique wires (Nodes).
4. **Analysis & Simulation:** The component coordinates are mathematically mapped to the extracted nodes, generating a complete Netlist for Lcapy to analyze and simulate.

## Original Concept by
1. Pannathat Artprasertkul
2. Pawaris Wanitchanukorn
3. Amornsak Jeena
