# magxxicVox Inbox Sender (Python) - Administrator Guide

## Generating Activation Tokens

To generate an activation token for a user, use the following Python snippet:

```python
import hashlib

SECRET_SALT = 'magxxicVox_Super_Secure_Salt_2024'
hwid = 'USER_HWID_HERE' # The HWID the user sends you

token = hashlib.sha256((hwid + SECRET_SALT).encode()).hexdigest().upper()
print('Activation Token:', token)
```

## Creating API Config Files

Use the following snippet to generate obfuscated config files for AWS, Mailgun, etc.

```python
import base64
import json

def encode_obf(data):
    json_data = json.dumps(data)
    b64_data = base64.b64encode(json_data.encode()).decode()
    return b64_data[::-1]

# Example for AWS (aws.sys)
aws_config = {
    'region': 'us-east-1',
    'accessKeyId': 'YOUR_KEY',
    'secretAccessKey': 'YOUR_SECRET'
}
print(encode_obf(aws_config)) # Save output to aws.sys
```
