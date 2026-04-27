import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
from datetime import datetime
from collections import deque
import numpy as np
import os
import sys
import time

# --- BRANDING & COLORS ---
CH_A_GOLD = "#ceb888"
CH_B_BLUE = "#33aaff"
BG_DATA   = "#ffffff"
BG_BANNER = "#1a1d20"
BTN_GRAY  = "#333333"
BTN_HOVER = "#555555"
BTN_ACTIVE = "#111111"
TEXT_LIGHT = "#ffffff"
BAUD_RATE  = 115200
SG_COLORS  = ["#ceb888", "#33aaff", "#a89060", "#1f6699", "#495057", "#adb5bd"]

WINDOW_SIZE = 100   # number of samples shown on each plot


class PERRigMonitor:
    def __init__(self, root, port):
        self.root = root
        self.root.title(f"PER Rig Monitor - {port}")
        self.root.geometry("1400x950")
        self.root.configure(bg=BG_DATA)

        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(__file__)

        # --- State ---
        self.is_recording   = False
        self.recorded_data  = []
        self.serial_dead    = False   # flag so we only show the error once

        # FIX #3 — use deque(maxlen=N) instead of list + pop(0)  (O(1) vs O(n))
        self.data_lc = [deque([0.0] * WINDOW_SIZE, maxlen=WINDOW_SIZE) for _ in range(2)]
        self.data_sg = [deque([0.0] * WINDOW_SIZE, maxlen=WINDOW_SIZE) for _ in range(6)]
        self.current_vals = [0.0] * 8

        try:
            self.ser = serial.Serial(port, BAUD_RATE, timeout=0.01)
        except serial.SerialException as e:
            messagebox.showerror("Serial Error", f"Could not connect to {port}:\n{e}")
            self.root.destroy()
            return

        self.setup_ui()

        # FIX #5 — schedule first call immediately and track next target time
        self._next_update = time.monotonic()
        self.update_all()

    # ------------------------------------------------------------------
    # UI SETUP
    # ------------------------------------------------------------------
    def setup_ui(self):
        # 1. HEADER
        header = tk.Frame(self.root, bg=BG_BANNER, height=75)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="PER SUSPENSION TEST RIG",
                 font=("Arial", 16, "bold"),
                 bg=BG_BANNER, fg=CH_A_GOLD, padx=20).pack(side=tk.LEFT)

        # FIX #1 — store btn colors on the widget itself so helpers always use the right color
        self.tare_btn = self._make_btn(header, "ZERO SYSTEM", self.send_tare, BTN_GRAY)
        self.tare_btn.pack(side=tk.RIGHT, padx=10, pady=15)

        self.export_btn = self._make_btn(header, "EXPORT CSV", self.export_to_csv, BTN_GRAY)
        self.export_btn.pack(side=tk.RIGHT, padx=10, pady=15)

        self.toggle_btn = self._make_btn(header, "START RECORDING", self.toggle_recording, "#28a745")
        self.toggle_btn.pack(side=tk.RIGHT, padx=10, pady=15)

        # Status label — shown when serial connection is lost
        self.status_lbl = tk.Label(header, text="", font=("Arial", 9, "bold"),
                                   bg=BG_BANNER, fg="#ff4444")
        self.status_lbl.pack(side=tk.RIGHT, padx=10)

        # 2. FOOTER
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
        except Exception as e:
            print(f"[INFO] Logo images not found, skipping: {e}")

        # 3. WORKSPACE
        workspace = tk.Frame(self.root, bg=BG_DATA)
        workspace.pack(expand=True, fill=tk.BOTH, padx=20, pady=5)

        workspace.columnconfigure(0, weight=1)
        workspace.columnconfigure(1, weight=1)
        workspace.rowconfigure(0, weight=1)

        # --- LEFT: FORCE ON WHEEL HUB ---
        lc_frame = tk.Frame(workspace, bg=BG_DATA)
        lc_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        val_frame = tk.Frame(lc_frame, bg=BG_DATA)
        val_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 0))

        self.lbl_a = tk.Label(val_frame, text="Lateral: 0.0 N",
                              font=("Arial", 50, "bold"), fg=CH_A_GOLD, bg=BG_DATA)
        self.lbl_a.pack(side=tk.LEFT, expand=True)

        self.lbl_b = tk.Label(val_frame, text="Normal: 0.0 N",
                              font=("Arial", 50, "bold"), fg=CH_B_BLUE, bg=BG_DATA)
        self.lbl_b.pack(side=tk.LEFT, expand=True)

        self.fig_lc, self.ax_lc = plt.subplots(figsize=(6, 5), facecolor=BG_DATA)
        self.fig_lc.subplots_adjust(left=0.15, right=0.95, top=0.90, bottom=0.10)

        # FIX #4 — pass numpy arrays so matplotlib never has type ambiguity
        self.line_lc_a, = self.ax_lc.plot(np.array(self.data_lc[0]), lw=4, color=CH_A_GOLD, label="Lateral")
        self.line_lc_b, = self.ax_lc.plot(np.array(self.data_lc[1]), lw=4, color=CH_B_BLUE, label="Normal")
        self.ax_lc.set_title("Force on Wheel Hub", fontsize=11, fontweight='bold')
        self.ax_lc.legend(loc="upper left", fontsize=8)
        self.ax_lc.grid(True, alpha=0.1)
        self.ax_lc.set_xlim(0, WINDOW_SIZE)
        self.ax_lc.set_ylim(-500, 4000)
        self.ax_lc.set_xticks([])

        self.canvas_lc = FigureCanvasTkAgg(self.fig_lc, master=lc_frame)
        self.canvas_lc.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- RIGHT: STRAIN GAUGES ---
        sg_frame = tk.Frame(workspace, bg=BG_DATA)
        sg_frame.grid(row=0, column=1, sticky="nsew")

        self.fig_sg, self.axes_sg = plt.subplots(6, 1, figsize=(3.5, 7),
                                                   sharex=True, facecolor=BG_DATA)
        self.fig_sg.subplots_adjust(hspace=0.5, left=0.5, right=1, top=0.95, bottom=0.05)

        self.lines_sg = []
        self.sg_texts = []

        for i in range(6):
            line, = self.axes_sg[i].plot(np.array(self.data_sg[i]), lw=2, color=SG_COLORS[i])
            self.lines_sg.append(line)

            txt = self.axes_sg[i].text(
                -0.50, 0.5, f"Strain {i+1}\n0.0",
                transform=self.axes_sg[i].transAxes,
                fontsize=6, color=SG_COLORS[i], fontweight='bold',
                ha='right', va='center', clip_on=False
            )
            self.sg_texts.append(txt)

            self.axes_sg[i].tick_params(labelsize=7)
            self.axes_sg[i].grid(True, alpha=0.1)
            self.axes_sg[i].set_xlim(0, WINDOW_SIZE)
            self.axes_sg[i].set_ylim(-5000, 5000)
            self.axes_sg[i].set_xticks([])
            self.axes_sg[i].set_ylabel("")

        self.canvas_sg = FigureCanvasTkAgg(self.fig_sg, master=sg_frame)
        self.canvas_sg.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    # BUTTON HELPER
    # FIX #1 — color is stored on the widget; hover/leave always read from it
    # ------------------------------------------------------------------
    def _make_btn(self, parent, text, cmd, color):
        btn = tk.Label(parent, text=text, font=("Arial", 9, "bold"),
                       bg=color, fg=TEXT_LIGHT, padx=15, pady=8,
                       cursor="hand2", relief=tk.RAISED)
        btn._base_color = color   # store so we can always retrieve it

        def on_press(e):
            btn.config(relief=tk.SUNKEN, bg=BTN_ACTIVE)
            cmd()
            btn.after(100, lambda: btn.config(relief=tk.RAISED, bg=btn._base_color))

        btn.bind("<Button-1>", on_press)
        btn.bind("<Enter>",    lambda e: btn.config(bg=BTN_HOVER))
        btn.bind("<Leave>",    lambda e: btn.config(bg=btn._base_color))  # always reads current base
        return btn

    def _set_btn_color(self, btn, color):
        """Change a button's base color and update it immediately."""
        btn._base_color = color
        btn.config(bg=color)

    # ------------------------------------------------------------------
    # RECORDING
    # ------------------------------------------------------------------
    def toggle_recording(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.recorded_data = []
            self._set_btn_color(self.toggle_btn, "#dc3545")
            self.toggle_btn.config(text="STOP RECORDING")
        else:
            self._set_btn_color(self.toggle_btn, "#28a745")
            self.toggle_btn.config(text="START RECORDING")

    # ------------------------------------------------------------------
    # TARE
    # FIX #2 — no serial flush needed here; tare is fire-and-forget
    # ------------------------------------------------------------------
    def send_tare(self):
        try:
            self.ser.write(b"TARE\n")
        except serial.SerialException as e:
            print(f"[ERROR] Could not send TARE: {e}")
            self._handle_serial_error()

    # ------------------------------------------------------------------
    # EXPORT
    # FIX #2 — snapshot recorded_data BEFORE opening the dialog so we
    #           never lose data that arrives while the dialog is open,
    #           and remove the misplaced serial flush entirely.
    # ------------------------------------------------------------------
    def export_to_csv(self):
        # Snapshot now — recording continues into self.recorded_data uninterrupted
        snapshot = list(self.recorded_data)

        if not snapshot:
            messagebox.showwarning("Warning", "No recorded data to export.\nPress START RECORDING first.")
            return

        fpath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save recorded data"
        )
        if not fpath:
            return   # user cancelled — do nothing

        try:
            with open(fpath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Lateral_N", "Normal_N",
                                  "Strain1", "Strain2", "Strain3",
                                  "Strain4", "Strain5", "Strain6"])
                writer.writerows(snapshot)
            messagebox.showinfo("Success", f"Exported {len(snapshot)} rows to:\n{fpath}")
        except OSError as e:
            # FIX #8 — surface file-write errors instead of swallowing them
            messagebox.showerror("Export Error", f"Could not write file:\n{e}")

    # ------------------------------------------------------------------
    # SERIAL ERROR HANDLING
    # FIX #7 — detect serial death and notify the user once
    # ------------------------------------------------------------------
    def _handle_serial_error(self):
        if not self.serial_dead:
            self.serial_dead = True
            # Stop recording so we don't accumulate a partial dataset silently
            if self.is_recording:
                self.is_recording = False
                self._set_btn_color(self.toggle_btn, "#28a745")
                self.toggle_btn.config(text="START RECORDING")
            self.status_lbl.config(text="⚠ SERIAL DISCONNECTED")
            messagebox.showerror(
                "Serial Error",
                "Lost connection to the Arduino.\n\n"
                "Check the USB cable and restart the application."
            )

    # ------------------------------------------------------------------
    # MAIN UPDATE LOOP
    # FIX #5 — fixed-interval scheduling that compensates for execution time
    # FIX #6 — update labels consistently from the same (last) sample
    # FIX #7 — catch SerialException specifically
    # ------------------------------------------------------------------
    def update_all(self):
        INTERVAL = 0.030   # 30 ms target
        self._next_update += INTERVAL

        new_data = False
        lines_read = 0

        try:
            while self.ser.in_waiting > 0 and lines_read < 15:
                raw = self.ser.readline()
                line = raw.decode('utf-8', errors='ignore').strip()
                parts = line.split(",")
                if len(parts) >= 8:
                    try:
                        vals = [float(x) for x in parts[:8]]
                    except ValueError as e:
                        print(f"[WARN] Bad serial line ({e}): {line!r}")
                        continue

                    # FIX #6 — record / update data buffers for every line read
                    if self.is_recording:
                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        self.recorded_data.append([ts] + vals)

                    for i in range(2):
                        self.data_lc[i].append(vals[i])
                    for i in range(6):
                        self.data_sg[i].append(vals[i + 2])

                    # Always keep current_vals as the latest sample
                    self.current_vals = vals
                    new_data = True
                    lines_read += 1

        except serial.SerialException as e:
            # FIX #7 — catch specifically, not bare except
            print(f"[ERROR] Serial read failed: {e}")
            self._handle_serial_error()
            return   # stop the loop entirely on serial death

        # --- Render ---
        if new_data:
            # FIX #4 — convert deques to numpy arrays before passing to matplotlib
            self.line_lc_a.set_ydata(np.array(self.data_lc[0]))
            self.line_lc_b.set_ydata(np.array(self.data_lc[1]))
            self.canvas_lc.draw_idle()

            # FIX #6 — labels always reflect self.current_vals (last sample this frame)
            self.lbl_a.config(text=f"Lateral: {self.current_vals[0]:.1f} N")
            self.lbl_b.config(text=f"Normal:  {self.current_vals[1]:.1f} N")

            for i in range(6):
                self.lines_sg[i].set_ydata(np.array(self.data_sg[i]))
                self.sg_texts[i].set_text(f"Strain {i+1}\n{self.current_vals[i+2]:.1f}")
            self.canvas_sg.draw_idle()

        # FIX #5 — schedule next call at the fixed target, not "now + 30ms"
        delay_ms = max(1, int((self._next_update - time.monotonic()) * 1000))
        self.root.after(delay_ms, self.update_all)


# ----------------------------------------------------------------------
# PORT SELECTOR
# FIX #9 — handle window-close (X button) gracefully with WM_DELETE_WINDOW
# ----------------------------------------------------------------------
class PortSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PER Setup")
        self.root.geometry("400x250")
        self.root.configure(bg=BG_BANNER)
        self.selected_port = None

        # Handle the user closing the window via X
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        tk.Label(self.root, text="USB PORT SELECTION",
                 font=('Arial', 12, 'bold'),
                 bg=BG_BANNER, fg=CH_A_GOLD, pady=20).pack()

        self.ports = [p.device for p in serial.tools.list_ports.comports()]
        if not self.ports:
            self.ports = ["No Devices Found"]

        self.port_var = tk.StringVar()
        self.dropdown = ttk.Combobox(self.root, textvariable=self.port_var,
                                     values=self.ports, state="readonly", width=30)
        self.dropdown.pack(pady=10)
        if self.ports:
            self.dropdown.current(0)

        btn = tk.Label(self.root, text="LAUNCH MONITOR",
                       font=("Arial", 10, "bold"),
                       bg=BTN_GRAY, fg=TEXT_LIGHT,
                       padx=30, pady=15, cursor="hand2", relief=tk.RAISED)
        btn.pack(pady=20)
        btn.bind("<Button-1>", lambda e: self._finish())

        self.root.mainloop()

    def _finish(self):
        port = self.port_var.get()
        if port and port != "No Devices Found":
            self.selected_port = port
            self.root.destroy()
        else:
            messagebox.showwarning("No Device", "Please select a valid COM port.")

    def _on_close(self):
        self.selected_port = None
        self.root.destroy()


# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    selector = PortSelector()
    if selector.selected_port:
        root = tk.Tk()
        app = PERRigMonitor(root, selector.selected_port)
        root.mainloop()
