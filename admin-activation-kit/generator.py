import hashlib
import os
import sys

def generate_token(hwid):
    """Calculates the Activation Token for a given HWID."""
    salt = "MAGXXIC"
    token = hashlib.sha256((hwid + salt).encode()).hexdigest().upper()[:24]
    return token

def main():
    print("="*50)
    print("     MagxxicVOT XII - Admin Activation Kit")
    print("="*50)

    while True:
        hwid = input("\nEnter User HWID (or 'q' to quit): ").strip()
        if not hwid:
            continue
        if hwid.lower() == 'q':
            break

        token = generate_token(hwid)

        print("\n" + "-"*30)
        print(f"HWID:  {hwid}")
        print(f"TOKEN: {token}")
        print("-"*30)
        print("\n[+] Copy the TOKEN and send it to the user.")

if __name__ == "__main__":
    main()
