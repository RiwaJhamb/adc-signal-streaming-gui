import socket
import time
import os
import json
import select
import numpy as np

FOLDER = "adc_files"
HOST, PORT = '127.0.0.1', 12345

def list_files():
    return [f for f in os.listdir(FOLDER) if f.endswith('.txt')]

def clean_data(path):
    vals = []
    for line in open(path):
        try:
            vals.append(float(line.strip().split(':')[-1]))
        except:
            pass
    arr = np.array(vals)
    arr = arr[~np.isnan(arr)]
    if arr.size:
        arr = (arr - arr.min()) / (arr.max() - arr.min())
    return arr.tolist()

def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(1)
    print(f"Server listening on {HOST}:{PORT}")

    conn, addr = srv.accept()
    print(f"Client connected from {addr}")

    current_data = []
    idx = 0
    interval = 0.02
    next_send = time.time()

    conn.setblocking(False)

    try:
        while True:
            # 1) Check for JSON select commands
            r, _, _ = select.select([conn], [], [], 0)
            if r:
                msg = conn.recv(1024).decode().strip()
                if not msg:
                    break
                try:
                    cmd = json.loads(msg)
                    if cmd.get("cmd") == "select":
                        files = list_files()
                        idx = 0
                        interval = cmd["ms"] / 1000.0
                        path = os.path.join(FOLDER, files[cmd["idx"]])
                        current_data = clean_data(path)
                        next_send = time.time()
                        print(f"→ Now streaming {files[cmd['idx']]} @ {cmd['ms']}ms")
                except json.JSONDecodeError:
                    pass

            # 2) Stream samples on schedule
            now = time.time()
            if current_data and now >= next_send:
                if idx < len(current_data):
                    conn.sendall(f"{current_data[idx]}\n".encode())
                    idx += 1
                    next_send += interval
                else:
                    current_data = []
            time.sleep(0.001)

    except (ConnectionResetError, BrokenPipeError):
        print("Client disconnected")
    finally:
        conn.close()
        srv.close()
        print("Server shut down.")

if __name__ == "__main__":
    main()
