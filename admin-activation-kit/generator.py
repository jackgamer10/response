import hashlib
import base64

def obfuscate(s):
    return base64.b64encode(s.encode()).decode()[::-1]

print("--- MagxxicVOT XII Admin Activation Generator ---")
hwid = input("Enter User HWID: ").strip().upper()
salt = "MAGXXICVOT-XII-SALT"

token = hashlib.sha256((hwid + salt).encode()).hexdigest()[:16].upper()

print("\n-----------------------------------")
print(f"Activation Token: {token}")
print(f"Obfuscated Token (for manual entry if needed): {obfuscate(token)}")
print("-----------------------------------\n")
