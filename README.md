# ADC Signal Streaming & Visualization Tool

This project simulates real-time data streaming from an ADC board using socket communication. It includes a GUI with advanced signal filtering (FIR with Hamming window, EMA) and live plotting.

---

## 🛠️ Features

### ✅ Server-Side (`server.py`)
- Selectable `.txt` ADC files for streaming.
- Custom sampling interval (ms).
- Streams data continuously using sockets.
- Allows real-time file/interval changes without disconnecting.
- Sends file/interval info in JSON format.

### ✅ Client-Side (`client.py`)
- Connects to the server and receives streamed ADC data.
- GUI (Tkinter + Matplotlib) with:
  - Raw signal plot
  - FIR filter (Hamming window)
  - EMA filter (Exponential Moving Average)
- Real-time filter updates based on interval/frequency.
- Logs every received value with timestamp into `logs/client_log.txt`.

---

## 📦 Requirements

Install dependencies using:

```bash
pip install -r requirements.txt
