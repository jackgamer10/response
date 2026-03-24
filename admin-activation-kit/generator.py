import hashlib
import base64

def obfuscate(s):
    return base64.b64encode(s.encode()).decode()[::-1]

def run():
    print('--- MagxxicVOT XII Admin Activation Kit (Python) ---')
    hwid = input('Enter User HWID: ').strip().upper()

    if not hwid:
        print('Error: HWID is required.')
        return

    expected_token = hashlib.sha256((hwid + "MAGXXICVOT-SALT").encode()).hexdigest()[:16].upper()
    obfuscated_token = obfuscate(expected_token)

    print('\n--- Activation Details ---')
    print(f'User HWID: {hwid}')
    print(f'Raw Token: {expected_token}')
    print(f'Obfuscated Token (activation.sys content): {obfuscated_token}')
    print('\nCopy the obfuscated token into a file named "activation.sys" in the sender root directory.')

if __name__ == '__main__':
    run()
