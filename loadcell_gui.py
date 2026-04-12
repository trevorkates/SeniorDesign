import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import messagebox, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- BRANDING & COLORS ---
CH_A_GOLD = "#ceb888"
CH_B_BLUE = "#33aaff"    
BG_DATA = "#f8f9fa"      # Off-white data area
BG_BANNER = "#1a1d20"    # Deep black banner
BTN_GRAY = "#333333"     # Dark industrial gray
BTN_HOVER = "#555555"    # Lighter gray for hover
TEXT_LIGHT = "#ffffff"   # High-contrast white
BAUD_RATE = 115200

class PortSelector:
    """Startup window to select the USB port."""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PER Rig - Setup")
        self.root.geometry("450x250")
        self.root.configure(bg=BG_BANNER)
        self.selected_port = None
        
        tk.Label(self.root, text="USB PORT SELECTION", font=('Arial', 14, 'bold'), 
                 bg=BG_BANNER, fg=CH_A_GOLD, pady=20).pack()
        
        self.ports = [p.device for p in serial.tools.list_ports.comports()]
        if not self.ports: self.ports = ["No Devices Found"]

        self.port_var = tk.StringVar()
        self.dropdown = ttk.Combobox(self.root, textvariable=self.port_var, values=self.ports, state="readonly", width=35)
        self.dropdown.pack(pady=10)
        if self.ports: self.dropdown.current(0)

        self.launch_btn = tk.Label(self.root, text="LAUNCH MONITOR", font=('Arial', 12, 'bold'), 
                                   bg=BTN_GRAY, fg=TEXT_LIGHT, padx=40, pady=15, cursor="hand2")
        self.launch_btn.pack(pady=20)
        
        self.launch_btn.bind("<Button-1>", lambda e: self.finish())
        self.launch_btn.bind("<Enter>", lambda e: self.launch_btn.config(bg=BTN_HOVER))
        self.launch_btn.bind("<Leave>", lambda e: self.launch_btn.config(bg=BTN_GRAY))
        
        self.root.mainloop()

    def finish(self):
        self.selected_port = self.port_var.get()
        if self.selected_port == "No Devices Found":
            messagebox.showwarning("Error", "Please plug in the Mega and try again.")
        else:
            self.root.destroy()

class DualLiveMonitor:
    def __init__(self, root, port):
        self.root = root
        self.root.title(f"PER Suspension Monitor - {port}")
        self.root.configure(background=BG_DATA)
        
        try:
            self.ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
        except Exception as e:
            messagebox.showerror("Serial Error", f"Could not connect to {port}")
            self.root.destroy()
            return

        self.data1, self.data2 = [0] * 100, [0] * 100 
        
        # --- TOP CONTROL BANNER ---
        # Calibration inputs removed; Global Tare expanded for ease of use
        control_frame = tk.Frame(root, bg=BG_BANNER, padx=20, pady=20)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        self.tare_btn = tk.Label(control_frame, text="GLOBAL TARE / ZERO SYSTEM", 
                                 font=('Arial', 16, 'bold'), bg=BTN_GRAY, fg=TEXT_LIGHT, pady=25, cursor="hand2")
        self.tare_btn.pack(fill=tk.X)
        self.tare_btn.bind("<Button-1>", lambda e: self.send_tare())
        self.tare_btn.bind("<Enter>", lambda e: self.tare_btn.config(bg=BTN_HOVER))
        self.tare_btn.bind("<Leave>", lambda e: self.tare_btn.config(bg=BTN_GRAY))

        # --- LIVE DATA DISPLAY ---
        display_frame = tk.Frame(root, bg=BG_DATA, pady=30)
        display_frame.pack(side=tk.TOP, fill=tk.X)
        self.label1 = tk.Label(display_frame, text="A: 0.00 N", font=("Arial", 72, "bold"), fg=CH_A_GOLD, bg=BG_DATA)
        self.label1.pack(side=tk.LEFT, expand=True)
        self.label2 = tk.Label(display_frame, text="B: 0.00 N", font=("Arial", 72, "bold"), fg=CH_B_BLUE, bg=BG_DATA)
        self.label2.pack(side=tk.LEFT, expand=True)

        # --- GRAPH ---
        self.fig, self.ax = plt.subplots(figsize=(10, 5), facecolor=BG_DATA, constrained_layout=True) 
        self.line1, = self.ax.plot(self.data1, lw=4, color=CH_A_GOLD, label="Load Cell A") 
        self.line2, = self.ax.plot(self.data2, lw=4, color=CH_B_BLUE, label="Load Cell B") 
        self.ax.set_ylim(-1000, 1000) 
        self.ax.set_ylabel("Force (N)", fontsize=12, fontweight='bold')
        self.ax.grid(True, linestyle='--', alpha=0.3)
        self.ax.legend(loc='upper right')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(pady=20, fill=tk.BOTH, expand=True, padx=30)

        self.update_all()

    def update_all(self):
        if self.ser.in_waiting > 0:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if "," in line:
                try:
                    v1, v2 = map(float, line.split(","))
                    self.data1.append(v1); self.data2.append(v2)
                    self.data1.pop(0); self.data2.pop(0)
                    self.label1.config(text=f"A: {v1:.2f} N")
                    self.label2.config(text=f"B: {v2:.2f} N")
                    self.line1.set_ydata(self.data1); self.line2.set_ydata(self.data2)
                    self.canvas.draw_idle()
                except: pass
        self.root.after(30, self.update_all)

    def send_tare(self): 
        self.ser.write(b"TARE\n")

if __name__ == "__main__":
    selector = PortSelector()
    if selector.selected_port:
        root = tk.Tk()
        root.geometry("1100x900")
        app = DualLiveMonitor(root, selector.selected_port)
        root.mainloop()
