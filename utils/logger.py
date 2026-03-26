import time

def log(level, module, message):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] [{module}] {message}")