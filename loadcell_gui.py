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
TEXT_DARK = "#212529"    
BAUD_RATE = 115200

class PortSelector:
    """Startup window to select the USB port without the text washing out."""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PER Rig - Setup")
        self.root.geometry("450x250")
        self.root.configure(bg=BG_BANNER)
        self.selected_port = None
        
        # Header
        tk.Label(self.root, text="USB PORT SELECTION", font=('Arial', 14, 'bold'), 
                 bg=BG_BANNER, fg=CH_A_GOLD, pady=20).pack()
        
        # Scan Ports
        self.ports = [p.device for p in serial.tools.list_ports.comports()]
        if not self.ports: self.ports = ["No Devices Found"]

        self.port_var = tk.StringVar()
        self.dropdown = ttk.Combobox(self.root, textvariable=self.port_var, values=self.ports, state="readonly", width=35)
        self.dropdown.pack(pady=10)
        if self.ports: self.dropdown.current(0)

        # Styled Label-Button for Launching
        self.launch_btn = tk.Label(self.root, text="LAUNCH MONITOR", font=('Arial', 12, 'bold'), 
                                   bg=BTN_GRAY, fg=TEXT_LIGHT, padx=40, pady=15, cursor="hand2")
        self.launch_btn.pack(pady=20)
        
        # Hover Logic
        self.launch_btn.bind("<Button-1>", lambda e: self.finish())
        self.launch_btn.bind("<Enter>", lambda e: self.launch_btn.config(bg=BTN_HOVER, fg=TEXT_LIGHT))
        self.launch_btn.bind("<Leave>", lambda e: self.launch_btn.config(bg=BTN_GRAY, fg=TEXT_LIGHT))
        
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
        control_frame = tk.Frame(root, bg=BG_BANNER, padx=20, pady=25)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        for i in range(6): control_frame.columnconfigure(i, weight=1)

        # Global Tare Button (Label style)
        self.tare_btn = tk.Label(control_frame, text="GLOBAL TARE / ZERO", 
                                 font=('Arial', 14, 'bold'), bg=BTN_GRAY, fg=TEXT_LIGHT, pady=18, cursor="hand2")
        self.tare_btn.grid(row=0, column=0, columnspan=6, sticky="ew", pady=(0, 20))
        self.tare_btn.bind("<Button-1>", lambda e: self.send_tare())
        self.tare_btn.bind("<Enter>", lambda e: self.tare_btn.config(bg=BTN_HOVER, fg=TEXT_LIGHT))
        self.tare_btn.bind("<Leave>", lambda e: self.tare_btn.config(bg=BTN_GRAY, fg=TEXT_LIGHT))

        # Calibrations 1
        tk.Label(control_frame, text="CAL 1:", bg=BG_BANNER, fg=TEXT_LIGHT).grid(row=1, column=0, sticky="e")
        self.cal1_entry = tk.Entry(control_frame, width=8, justify='center')
        self.cal1_entry.grid(row=1, column=1, padx=5)
        self.upd1 = tk.Label(control_frame, text="UPDATE A", bg=BTN_GRAY, fg=TEXT_LIGHT, pady=8, cursor="hand2", width=12)
        self.upd1.grid(row=1, column=2)
        self.upd1.bind("<Button-1>", lambda e: self.send_cal1())
        self.upd1.bind("<Enter>", lambda e: self.upd1.config(bg=BTN_HOVER))
        self.upd1.bind("<Leave>", lambda e: self.upd1.config(bg=BTN_GRAY))

        # Calibrations 2
        tk.Label(control_frame, text="CAL 2:", bg=BG_BANNER, fg=TEXT_LIGHT).grid(row=1, column=3, sticky="e")
        self.cal2_entry = tk.Entry(control_frame, width=8, justify='center')
        self.cal2_entry.grid(row=1, column=4, padx=5)
        self.upd2 = tk.Label(control_frame, text="UPDATE B", bg=BTN_GRAY, fg=TEXT_LIGHT, pady=8, cursor="hand2", width=12)
        self.upd2.grid(row=1, column=5)
        self.upd2.bind("<Button-1>", lambda e: self.send_cal2())
        self.upd2.bind("<Enter>", lambda e: self.upd2.config(bg=BTN_HOVER))
        self.upd2.bind("<Leave>", lambda e: self.upd2.config(bg=BTN_GRAY))

        # --- LIVE DATA DISPLAY ---
        display_frame = tk.Frame(root, bg=BG_DATA, pady=15)
        display_frame.pack(side=tk.TOP, fill=tk.X)
        self.label1 = tk.Label(display_frame, text="A: 0.00 N", font=("Arial", 60, "bold"), fg=CH_A_GOLD, bg=BG_DATA)
        self.label1.pack(side=tk.LEFT, expand=True)
        self.label2 = tk.Label(display_frame, text="B: 0.00 N", font=("Arial", 60, "bold"), fg=CH_B_BLUE, bg=BG_DATA)
        self.label2.pack(side=tk.LEFT, expand=True)

        # --- GRAPH ---
        self.fig, self.ax = plt.subplots(figsize=(10, 4), facecolor=BG_DATA, constrained_layout=True) 
        self.line1, = self.ax.plot(self.data1, lw=3, color=CH_A_GOLD, label="Load Cell A") 
        self.line2, = self.ax.plot(self.data2, lw=3, color=CH_B_BLUE, label="Load Cell B") 
        self.ax.set_ylim(-1000, 1000) 
        self.ax.set_ylabel("Force (N)")
        self.ax.grid(True, linestyle='--', alpha=0.3)
        
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

    def send_tare(self): self.ser.write(b"TARE\n")
    def send_cal1(self):
        f = self.cal1_entry.get()
        if f: self.ser.write(f"SET_CAL1:{f}\n".encode())
    def send_cal2(self):
        f = self.cal2_entry.get()
        if f: self.ser.write(f"SET_CAL2:{f}\n".encode())

if __name__ == "__main__":
    selector = PortSelector()
    if selector.selected_port:
        root = tk.Tk()
        root.geometry("1100x850")
        app = DualLiveMonitor(root, selector.selected_port)
        root.mainloop()