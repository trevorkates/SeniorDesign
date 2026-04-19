### **1\. Download the Files**

* Click the green **Code** button at the top of this GitHub page.  
* Select **Download ZIP**.  
* Extract the ZIP file and move the folder named `SeniorDesign_main_code` to your **Desktop**.

### **2\. Install Python**

* Download and install Python 3.x from [python.org](https://www.python.org/downloads/windows).  
* **CRITICAL:** During installation, you **must** check the box that says **"Add Python to PATH"**. If this is skipped, the terminal will not recognize the commands below.

### **3\. Run the Monitor**

* Connect your Arduino/Mega to a power source and to the computer via USB.  
* Press the **Windows Key**, type `cmd`, and press **Enter**.  
* Copy and paste the following block of code into the terminal and press **Enter**:

```bash  
# 1. Navigate to your folder (Universal Path)  
cd /d "%USERPROFILE%\\Desktop\\SeniorDesign\_main\_code" || cd /d "%USERPROFILE%\\OneDrive\\Desktop\\SeniorDesign\_main\_code"

# 2. Install dependencies (Required for the port check to work)  
pip install \-r requirements.txt

# 3. IDENTIFY THE PORT (Look for "Arduino" or "USB Serial Port")  
python \-m serial.tools.list\_ports

# 4. Launch the monitor  
python loadcell\_gui.py

## **🛠 Using the App**
```

1. **Select Port:** Once the "PER Rig \- Setup" window appears, use the dropdown to select the COM port you identified in Step 3\.  
2. **Launch:** Click **LAUNCH MONITOR**.  
3. **Tare:** If the readings are not at zero with no load applied, click the **GLOBAL TARE / ZERO SYSTEM** button at the top to zero the sensors.

## **⚠️ Troubleshooting**

* **"Python is not recognized":** Re-install Python and ensure the "Add Python to PATH" checkbox is selected.  
* **"No Devices Found":** Check the USB connection to the Mega. Ensure the Arduino IDE Serial Monitor is closed, as only one program can use the port at a time.  
* **Library Errors:** Ensure you have an active internet connection when running the `pip install` command to download `pyserial` and `matplotlib`.

