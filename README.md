### Download the Files

* Click the green **Code** button at the top of this GitHub page.  
* Select **Download ZIP**.  
* Extract the ZIP file and move the folder named `SeniorDesign_main_code` to your **Desktop**.

## Setup for Windows
### **1. Install Python**

* Download and install Python 3.x from [python.org](https://www.python.org/downloads/windows).  
* **CRITICAL:** During installation, you **must** check the box that says **"Add Python to PATH"**. If this is skipped, the terminal will not recognize the commands below.

### **2. Run the Monitor**

* Connect your Arduino/Mega to a power source and to the computer via USB.  
* Press the **Windows Key**, type `cmd`, and press **Enter**.  
* Copy and paste the following block of code into the terminal and press **Enter**:

```bash  
# 1. Navigate to your folder
cd /d "%USERPROFILE%\Desktop\SeniorDesign_main_code" || cd /d "%USERPROFILE%\OneDrive\Desktop\SeniorDesign_main_code"

# 2. Install dependencies
pip install -r requirements.txt

# 3. IDENTIFY THE PORT
python -m serial.tools.list_ports

# 4. Launch the monitor
python loadcell_gui.py
```

### **3. Using the App**

1. **Select Port:** Once the "PER Rig \- Setup" window appears, use the dropdown to select the COM port you identified in Step 3\.  
2. **Launch:** Click **LAUNCH MONITOR**.  
3. **Tare:** If the readings are not at zero with no load applied, click the **GLOBAL TARE / ZERO SYSTEM** button at the top to zero the sensors.

### **4. Troubleshooting**

* **"Python is not recognized":** Re-install Python and ensure the "Add Python to PATH" checkbox is selected.  
* **"No Devices Found":** Check the USB connection to the Mega. Ensure the Arduino IDE Serial Monitor is closed, as only one program can use the port at a time.  
* **Library Errors:** Ensure you have an active internet connection when running the `pip install` command to download `pyserial` and `matplotlib`.

### Circuit Diagram and Pin Organization
<img width="961" height="540" alt="Pasted Graphic 3" src="https://github.com/user-attachments/assets/2543905b-f584-454f-a08e-36759ad1e430" />
<img width="432" height="402" alt="Arduino Pin Organization" src="https://github.com/user-attachments/assets/e1a65ee3-63f5-46ea-9fef-372b5011d755" />
