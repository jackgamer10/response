import base64
import sys
import os

def generate_token(hwid):
    # Activation logic: Base64 reverse obfuscation
    try:
        token = base64.b64encode(hwid[::-1].encode()).decode().replace('=', '')[:16].upper()
        return token
    except Exception as e:
        return f"Error: {e}"

def main():
    print("="*50)
    print(" MagxxicVOT XII - Admin Token Generator ")
    print("="*50)

    if len(sys.argv) > 1:
        hwid = sys.argv[1].strip()
    else:
        hwid = input("\nEnter User HWID: ").strip()

    if not hwid:
        print("Error: HWID cannot be empty.")
        return

    token = generate_token(hwid)

    print("\n" + "-"*30)
    print(f"HWID  : {hwid}")
    print(f"TOKEN : {token}")
    print("-"*30)
    print("\nToken generated successfully.")

if __name__ == "__main__":
    main()
