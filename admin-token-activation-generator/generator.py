import hashlib
import json
import base64
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
import os
import sys

class Colors:
    RESET = "\033[0m"
    BRIGHT = "\033[1m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    RED = "\033[31m"
    WHITE = "\033[37m"

SECRET_SALT = 'magxxicVox_Super_Secure_Salt_2024'

def encode_obf(data):
    json_data = json.dumps(data, separators=(',', ':'))
    b64_data = base64.b64encode(json_data.encode()).decode()
    return b64_data[::-1]

def ask(query):
    return input(f"{Colors.CYAN}│ {Colors.RESET}{query}")

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    while True:
        clear()
        print(f"{Colors.MAGENTA}┌───────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.MAGENTA}│{Colors.BRIGHT}{Colors.CYAN}      magxxicVox Admin Toolkit (Python)            {Colors.MAGENTA}│{Colors.RESET}")
        print(f"{Colors.MAGENTA}├───────────────────────────────────────────────────┤{Colors.RESET}")
        print(f"{Colors.MAGENTA}│{Colors.WHITE}  1. Generate Activation Token (from HWID)         {Colors.MAGENTA}│{Colors.RESET}")
        print(f"{Colors.MAGENTA}│{Colors.WHITE}  2. Create AWS Config (aws.sys)                   {Colors.MAGENTA}│{Colors.RESET}")
        print(f"{Colors.MAGENTA}│{Colors.WHITE}  3. Create Brevo Config (brevo.sys)               {Colors.MAGENTA}│{Colors.RESET}")
        print(f"{Colors.MAGENTA}│{Colors.WHITE}  4. Create Mailgun Config (mailgun.sys)           {Colors.MAGENTA}│{Colors.RESET}")
        print(f"{Colors.MAGENTA}│{Colors.WHITE}  5. Create SendGrid Config (sendgrid.sys)         {Colors.MAGENTA}│{Colors.RESET}")
        print(f"{Colors.MAGENTA}│{Colors.WHITE}  6. Create DKIM Config (dkim.sys)                 {Colors.MAGENTA}│{Colors.RESET}")
        print(f"{Colors.MAGENTA}│{Colors.WHITE}  7. Create Direct MX Config (direct_mx.sys)       {Colors.MAGENTA}│{Colors.RESET}")
        print(f"{Colors.MAGENTA}│{Colors.WHITE}  0. Exit                                          {Colors.MAGENTA}│{Colors.RESET}")
        print(f"{Colors.MAGENTA}└───────────────────────────────────────────────────┘{Colors.RESET}")

        choice = ask('Select option: ')

        if choice == '1':
            hwid = ask('Enter User HWID: ')
            token = hashlib.sha256((hwid.strip() + SECRET_SALT).encode()).hexdigest().upper()
            print(f"\n{Colors.GREEN}[+] Generated Token:{Colors.RESET} {Colors.BRIGHT}{token}{Colors.RESET}\n")

        elif choice == '2':
            aws = {
                'region': ask('Region (e.g. us-east-1): '),
                'accessKeyId': ask('Access Key ID: '),
                'secretAccessKey': ask('Secret Access Key: ')
            }
            with open('aws.sys', 'w') as f:
                f.write(encode_obf(aws))
            print(f"\n{Colors.GREEN}[+] Created aws.sys{Colors.RESET}\n")

        elif choice == '3':
            brevo = {
                'user': ask('Brevo User Email: '),
                'apiKey': ask('Brevo API Key: ')
            }
            with open('brevo.sys', 'w') as f:
                f.write(encode_obf(brevo))
            print(f"\n{Colors.GREEN}[+] Created brevo.sys{Colors.RESET}\n")

        elif choice == '4':
            mailgun = {
                'apiKey': ask('Mailgun API Key: '),
                'domain': ask('Mailgun Domain: ')
            }
            with open('mailgun.sys', 'w') as f:
                f.write(encode_obf(mailgun))
            print(f"\n{Colors.GREEN}[+] Created mailgun.sys{Colors.RESET}\n")

        elif choice == '5':
            sendgrid = {
                'apiKey': ask('SendGrid API Key: ')
            }
            with open('sendgrid.sys', 'w') as f:
                f.write(encode_obf(sendgrid))
            print(f"\n{Colors.GREEN}[+] Created sendgrid.sys{Colors.RESET}\n")

        elif choice == '6':
            dkim = {
                'domainName': ask('DKIM Domain: '),
                'keySelector': ask('DKIM Selector: ')
            }
            with open('dkim.sys', 'w') as f:
                f.write(encode_obf(dkim))
            print(f"\n{Colors.GREEN}[+] Created dkim.sys{Colors.RESET}")
            print(f"{Colors.YELLOW}[!] Remember to place dkim_key.pem in the same folder.{Colors.RESET}\n")

        elif choice == '7':
            direct_mx = {
                'retries': int(ask('Max Retries (default 3): ') or 3),
                'timeout': int(ask('Timeout in ms (default 10000): ') or 10000),
                'verifyDns': ask('Verify DNS/MX before send? (y/n): ').lower() == 'y'
            }
            with open('direct_mx.sys', 'w') as f:
                f.write(encode_obf(direct_mx))
            print(f"\n{Colors.GREEN}[+] Created direct_mx.sys{Colors.RESET}\n")

        elif choice == '0':
            sys.exit(0)

        else:
            print(f"{Colors.RED}[!] Invalid selection.{Colors.RESET}")

        ask('Press Enter to continue...')

if __name__ == "__main__":
    main()
