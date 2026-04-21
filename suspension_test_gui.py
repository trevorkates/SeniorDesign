import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from PIL import Image, ImageTk 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
from datetime import datetime
import os
import sys

# --- BRANDING & COLORS ---
CH_A_GOLD = "#ceb888"
CH_B_BLUE = "#33aaff"    
BG_DATA = "#ffffff"      
BG_BANNER = "#1a1d20"    
BTN_GRAY = "#333333"     
BTN_HOVER = "#555555"    
BTN_ACTIVE = "#111111"   
TEXT_LIGHT = "#ffffff"   
BAUD_RATE = 115200
SG_COLORS = ["#ceb888", "#33aaff", "#a89060", "#1f6699", "#495057", "#adb5bd"]

class PERRigMonitor:
    def __init__(self, root, port):
        self.root = root
        self.root.title(f"PER Rig Monitor - {port}")
        self.root.geometry("1400x950")
        self.root.configure(bg=BG_DATA)
        
        if getattr(sys, 'frozen', False): self.base_path = sys._MEIPASS
        else: self.base_path = os.path.dirname(__file__)

        # State & Data
        self.is_recording = False
        self.recorded_data = [] 
        self.data_lc = [[] for _ in range(2)]  
        self.data_sg = [[] for _ in range(6)]  

        try:
            self.ser = serial.Serial(port, BAUD_RATE, timeout=0.01)
        except Exception as e:
            messagebox.showerror("Serial Error", f"Could not connect to {port}")
            self.root.destroy()
            return

        self.setup_ui()
        self.update_all()

    def setup_ui(self):
        # 1. HEADER
        header = tk.Frame(self.root, bg=BG_BANNER, height=75)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="PER SUSPENSION TEST RIG", font=("Arial", 16, "bold"), 
                 bg=BG_BANNER, fg=CH_A_GOLD, padx=20).pack(side=tk.LEFT)

        # Buttons - Using explicit on_click calls to ensure functionality
        self.tare_btn = self.create_custom_btn(header, "ZERO SYSTEM", self.send_tare, BTN_GRAY)
        self.tare_btn.pack(side=tk.RIGHT, padx=10, pady=15)
        
        self.export_btn = self.create_custom_btn(header, "EXPORT CSV", self.export_to_csv, BTN_GRAY)
        self.export_btn.pack(side=tk.RIGHT, padx=10, pady=15)

        self.toggle_btn = self.create_custom_btn(header, "START RECORDING", self.toggle_recording, "#28a745")
        self.toggle_btn.pack(side=tk.RIGHT, padx=10, pady=15)

        # 2. FOOTER (Centered Branding)
        footer = tk.Frame(self.root, bg=BG_DATA, height=90)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        footer.pack_propagate(False)

        logo_inner = tk.Frame(footer, bg=BG_DATA)
        logo_inner.pack(expand=True)

        try:
            p_img = Image.open(os.path.join(self.base_path, "purdue_logo.jpg"))
            p_img.thumbnail((200, 40), Image.Resampling.LANCZOS)
            self.photo_p = ImageTk.PhotoImage(p_img)
            tk.Label(logo_inner, image=self.photo_p, bg=BG_DATA).pack(side=tk.LEFT, padx=15)

            per_img = Image.open(os.path.join(self.base_path, "per_logo.jpg"))
            per_img.thumbnail((60, 60), Image.Resampling.LANCZOS)
            self.photo_per = ImageTk.PhotoImage(per_img)
            tk.Label(logo_inner, image=self.photo_per, bg=BG_DATA).pack(side=tk.LEFT, padx=15)
        except: pass

        # 3. WORKSPACE
        workspace = tk.Frame(self.root, bg=BG_DATA)
        workspace.pack(expand=True, fill=tk.BOTH, padx=20, pady=5)
        workspace.columnconfigure(0, weight=3)
        workspace.columnconfigure(1, weight=2)
        workspace.rowconfigure(0, weight=1)

        # --- LEFT: FORCE ON WHEEL HUB ---
        lc_frame = tk.Frame(workspace, bg=BG_DATA)
        lc_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 45))

        val_frame = tk.Frame(lc_frame, bg=BG_DATA)
        val_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 0))
        self.lbl_a = tk.Label(val_frame, text="Lateral: 0.0 N", font=("Arial", 50, "bold"), fg=CH_A_GOLD, bg=BG_DATA)
        self.lbl_a.pack(side=tk.LEFT, expand=True)
        self.lbl_b = tk.Label(val_frame, text="Normal: 0.0 N", font=("Arial", 50, "bold"), fg=CH_B_BLUE, bg=BG_DATA)
        self.lbl_b.pack(side=tk.LEFT, expand=True)

        self.fig_lc, self.ax_lc = plt.subplots(figsize=(6, 5), facecolor=BG_DATA)
        self.fig_lc.tight_layout(pad=4.0) 
        self.line_lc_a, = self.ax_lc.plot([], [], lw=4, color=CH_A_GOLD)
        self.line_lc_b, = self.ax_lc.plot([], [], lw=4, color=CH_B_BLUE)
        self.ax_lc.set_title("Force on Wheel Hub", fontsize=11, fontweight='bold')
        self.ax_lc.grid(True, alpha=0.1)
        
        self.canvas_lc = FigureCanvasTkAgg(self.fig_lc, master=lc_frame)
        self.canvas_lc.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- RIGHT: STRAIN GAUGES ---
        sg_frame = tk.Frame(workspace, bg=BG_DATA)
        sg_frame.grid(row=0, column=1, sticky="nsew")

        self.fig_sg, self.axes_sg = plt.subplots(6, 1, figsize=(4, 7), sharex=True, facecolor=BG_DATA)
        self.fig_sg.subplots_adjust(hspace=0.7, left=0.25, right=0.95, top=0.96, bottom=0.20)
        
        self.lines_sg = []
        for i in range(6):
            line, = self.axes_sg[i].plot([], [], lw=2, color=SG_COLORS[i])
            self.lines_sg.append(line)
            self.axes_sg[i].set_ylabel(f"SG{i+1}", fontsize=8, color=SG_COLORS[i], fontweight='bold')
            self.axes_sg[i].tick_params(labelsize=7)
            self.axes_sg[i].grid(True, alpha=0.1)
            self.axes_sg[i].set_ylim(-1000, 1000)

        self.canvas_sg = FigureCanvasTkAgg(self.fig_sg, master=sg_frame)
        self.canvas_sg.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_custom_btn(self, parent, text, cmd, color):
        btn = tk.Label(parent, text=text, font=("Arial", 9, "bold"), 
                       bg=color, fg=TEXT_LIGHT, padx=15, pady=8, 
                       cursor="hand2", relief=tk.RAISED)
        
        def on_press(e):
            btn.config(relief=tk.SUNKEN, bg=BTN_ACTIVE)
            cmd()
            # Reset visual after short delay
            btn.after(100, lambda: btn.config(relief=tk.RAISED, bg=color))
            
        btn.bind("<Button-1>", on_press)
        btn.bind("<Enter>", lambda e: btn.config(bg=BTN_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        return btn

    def toggle_recording(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.recorded_data = []
            self.toggle_btn.config(text="STOP & SAVE", bg="#dc3545")
            # Update the 'Leave' color for recording state
            self.toggle_btn.bind("<Leave>", lambda e: self.toggle_btn.config(bg="#dc3545"))
        else:
            self.toggle_btn.config(text="START RECORDING", bg="#28a745")
            self.toggle_btn.bind("<Leave>", lambda e: self.toggle_btn.config(bg="#28a745"))

    def send_tare(self): 
        try: self.ser.write(b"TARE\n")
        except: pass

    def export_to_csv(self):
        if not self.recorded_data:
            messagebox.showwarning("Warning", "No data to export.")
            return
        fpath = filedialog.asksaveasfilename(defaultextension=".csv")
        if fpath:
            with open(fpath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Lateral_N", "Normal_N", "SG1", "SG2", "SG3", "SG4", "SG5", "SG6"])
                writer.writerows(self.recorded_data)
            messagebox.showinfo("Success", "Data exported successfully.")

    def update_all(self):
        new_data = False
        lines_read = 0
        
        # THROTTLE: Only read up to 15 lines per cycle to keep UI responsive
        while self.ser.in_waiting > 0 and lines_read < 15:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            parts = line.split(",")
            if len(parts) >= 8:
                try:
                    vals = [float(x) for x in parts]
                    new_data = True
                    lines_read += 1
                    
                    if self.is_recording:
                        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        self.recorded_data.append([ts] + vals)

                    for i in range(2):
                        self.data_lc[i].append(vals[i])
                        if len(self.data_lc[i]) > 100: self.data_lc[i].pop(0)
                    for i in range(6):
                        self.data_sg[i].append(vals[i+2])
                        if len(self.data_sg[i]) > 100: self.data_sg[i].pop(0)

                    self.lbl_a.config(text=f"Lateral: {vals[0]:.1f} N")
                    self.lbl_b.config(text=f"Normal: {vals[1]:.1f} N")
                except: pass
        
        if new_data:
            self.line_lc_a.set_data(range(len(self.data_lc[0])), self.data_lc[0])
            self.line_lc_b.set_data(range(len(self.data_lc[1])), self.data_lc[1])
            self.ax_lc.relim(); self.ax_lc.autoscale_view()
            self.canvas_lc.draw_idle()

            for i in range(6):
                self.lines_sg[i].set_data(range(len(self.data_sg[i])), self.data_sg[i])
                self.axes_sg[i].relim(); self.axes_sg[i].autoscale_view()
            self.canvas_sg.draw_idle()

        # Update every 50ms for a balance of speed and responsiveness
        self.root.after(50, self.update_all)

class PortSelector:
    def __init__(self):
        self.root = tk.Tk(); self.root.title("PER Setup"); self.root.geometry("400x250"); self.root.configure(bg=BG_BANNER)
        self.selected_port = None
        tk.Label(self.root, text="USB PORT SELECTION", font=('Arial', 12, 'bold'), bg=BG_BANNER, fg=CH_A_GOLD, pady=20).pack()
        self.ports = [p.device for p in serial.tools.list_ports.comports()]
        if not self.ports: self.ports = ["No Devices Found"]
        self.port_var = tk.StringVar(); self.dropdown = ttk.Combobox(self.root, textvariable=self.port_var, values=self.ports, state="readonly", width=30)
        self.dropdown.pack(pady=10)
        if self.ports: self.dropdown.current(0)
        
        self.btn = tk.Label(self.root, text="LAUNCH MONITOR", font=("Arial", 10, "bold"), 
                            bg=BTN_GRAY, fg=TEXT_LIGHT, padx=30, pady=15, cursor="hand2", relief=tk.RAISED)
        self.btn.pack(pady=20)
        self.btn.bind("<Button-1>", lambda e: self.finish())
        self.root.mainloop()
        
    def finish(self):
        self.selected_port = self.port_var.get()
        if self.selected_port != "No Devices Found": self.root.destroy()

if __name__ == "__main__":
    selector = PortSelector()
    if selector.selected_port:
        root = tk.Tk()
        app = PERRigMonitor(root, selector.selected_port)
        root.mainloop()