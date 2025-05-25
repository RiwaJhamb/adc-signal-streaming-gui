import socket
import threading
import json
import os
import datetime
import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import firwin, lfilter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

HOST, PORT = '127.0.0.1', 12345
ADC_FOLDER = "adc_files"

raw, fir, ema = [], [], []
interval = None
cutoff = 0.0
alpha = 0.1  # EMA factor

# Prepare log file
log_path = "client_log.csv"
if not os.path.exists(log_path):
    with open(log_path, "w") as f:
        f.write("timestamp,sample\n")

# Persistent connection
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

def send_select(idx, ms):
    cmd = {"cmd": "select", "idx": idx, "ms": ms}
    sock.sendall((json.dumps(cmd) + "\n").encode())

def auto_fir_order(cutoff_freq, fs):
    if cutoff_freq <= 0 or fs <= 0:
        return 20
    nyq = fs / 2
    norm = cutoff_freq / nyq
    order = int(4 / max(norm, 1e-3))
    return max(5, min(order, 200))

def receive_loop():
    global raw, fir, ema, interval, cutoff
    buf = ""
    while True:
        data = sock.recv(1024).decode()
        if not data:
            break
        buf += data
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            try:
                val = float(line.strip())
            except:
                continue

            # Log sample
            with open(log_path, "a") as f:
                f.write(f"{datetime.datetime.now().isoformat()},{val}\n")

            raw.append(val)
            # EMA
            if ema:
                ema.append(alpha * val + (1 - alpha) * ema[-1])
            else:
                ema.append(val)

            # Hamming-window FIR via FFT-based cutoff
            if interval:
                M = min(len(raw), 200)
                block = np.array(raw[-M:])
                block -= block.mean()
                yf = np.fft.rfft(block)
                xf = np.fft.rfftfreq(M, d=interval)
                cutoff = xf[np.argmax(np.abs(yf))] if M else 0.0

                fs = 1.0 / interval
                order = auto_fir_order(cutoff, fs)
                norm_cut = max(1e-3, min(cutoff / (fs/2), 1-1e-3))
                coefs = firwin(numtaps=order, cutoff=norm_cut, window='hamming')
                fir[:] = lfilter(coefs, 1.0, raw)

            root.after(0, update_plot)
    sock.close()

def update_plot():
    M = 200
    x = np.arange(-M, 0)
    r, f, e = raw[-M:], fir[-M:], ema[-M:]
    ax1.clear(); ax1.plot(x[-len(r):], r); ax1.set_title("Raw Signal")
    ax2.clear(); ax2.plot(x[-len(f):], f)
    ax2.set_title(f"Hamming FIR (cutoff≈{cutoff:.2f}Hz, Δ={interval:.3f}s)")
    ax3.clear(); ax3.plot(x[-len(e):], e); ax3.set_title(f"EMA (α={alpha})")
    canvas.draw()

# Build GUI
root = tk.Tk(); root.title("ADC Live Viewer")
top = ttk.Frame(root); top.pack(fill=tk.X, pady=5)

ttk.Label(top, text="File:").pack(side=tk.LEFT, padx=5)
files = [f for f in os.listdir(ADC_FOLDER) if f.endswith('.txt')]
file_cb = ttk.Combobox(top, values=files, state="readonly"); file_cb.current(0); file_cb.pack(side=tk.LEFT)

ttk.Label(top, text="Interval (ms):").pack(side=tk.LEFT, padx=5)
int_cb = ttk.Combobox(top, values=[10,20,50,100,200,500,1000], state="readonly"); int_cb.set(20); int_cb.pack(side=tk.LEFT)

def on_change(_=None):
    global interval
    idx = file_cb.current()
    ms  = float(int_cb.get())
    interval = ms / 1000.0
    send_select(idx, ms)

file_cb.bind("<<ComboboxSelected>>", on_change)
int_cb.bind("<<ComboboxSelected>>", on_change)

fig, (ax1, ax2, ax3) = plt.subplots(3,1,figsize=(6,9))
fig.tight_layout(pad=3.0)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

threading.Thread(target=receive_loop, daemon=True).start()
on_change()  # bootstrap initial stream
root.mainloop()
