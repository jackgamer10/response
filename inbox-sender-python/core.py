import base64
import json
import hashlib
import os
import platform
import uuid
import psutil
import socket
import sys

def get_hwid():
    try:
        # Simple but robust HWID for Python
        system_info = f"{platform.node()}-{platform.processor()}-{uuid.getnode()}"
        return hashlib.sha256(system_info.encode()).hexdigest().upper()
    except Exception:
        return f"UNKNOWN-HWID-{hashlib.md5(socket.gethostname().encode()).hexdigest().upper()}"

SECRET_SALT = 'magxxicVox_Super_Secure_Salt_2024'

def generate_token(hwid):
    return hashlib.sha256((hwid + SECRET_SALT).encode()).hexdigest().upper()

def encode_obf(data):
    json_data = json.dumps(data, separators=(',', ':'))
    b64_data = base64.b64encode(json_data.encode()).decode()
    return b64_data[::-1]

def decode_obf(data):
    b64_data = data[::-1]
    json_data = base64.b64decode(b64_data).decode()
    return json.loads(json_data)

def check_license():
    activation_path = os.path.join(os.path.dirname(__file__), 'activation.sys')
    hwid = get_hwid()

    if os.path.exists(activation_path):
        try:
            with open(activation_path, 'r') as f:
                data = decode_obf(f.read())

            if data.get('hwid') != hwid:
                print("\033[91m[!] Anti-Tamper: Hardware mismatch detected!\033[0m")
                sys.exit(1)

            if data.get('token') != generate_token(hwid):
                raise ValueError("Invalid token")

            print(f"\033[92m[+] License activated for HWID: {hwid[:8]}...\033[0m")
            return True
        except Exception:
            pass

    print("\033[93m[!] Software not activated.\033[0m")
    print(f"\033[96m┌───────────────────────────────────────────────────┐\033[0m")
    print(f"\033[96m│\033[97m Your HWID: \033[1m{hwid}\033[0m\033[96m │\033[0m")
    print(f"\033[96m└───────────────────────────────────────────────────┘\033[0m")

    token = input('Enter Activation Token: ').strip().upper()
    if token == generate_token(hwid):
        data = {'hwid': hwid, 'token': token, 'installPath': os.path.dirname(__file__)}
        with open(activation_path, 'w') as f:
            f.write(encode_obf(data))
        print("\033[92m[+] Activation successful! Please restart.\033[0m")
        sys.exit(0)
    else:
        print("\033[91m[!] Invalid activation token.\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    # Test
    print(f"HWID: {get_hwid()}")
    print(f"Token: {generate_token(get_hwid())}")
