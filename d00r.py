#!/usr/bin/env python3

import os
import sys
import platform
import argparse
import requests
import queue
import threading
import re
from datetime import datetime
from html import unescape

# Configuring color variables
yellow='\u001b[1;93m'
cyan = '\u001b[1;96m'
red = '\u001b[1;91m'
green = '\u001b[1;92m'
white = '\u001b[1;37;40m'

thread_num = 1 # Number of threads
hits = []
invalid_contest_hits = []
login_page_hits = []
permission_denied_hits = []
hits_lock = threading.Lock()
attempted_requests = 0
request_errors = 0

try:
    from tqdm import tqdm
except:
    print("Missing modules: tqdm")
    sys.exit(1)

screen=r'''
      _  ___   ___
     | |/ _ \ / _ \\
   __| | | | | | | |_ __
  / _` | | | | | | | '__|
 | (_| | |_| | |_| | |
  \__,_|\___/ \___/|_|    v1.3.1

  >> URL Brute-Force Tool

             >[By CYB3RMX_]<
'''
print(f"{yellow}{screen}{white}")

# Parsing and handlig arguments
args = []
parser = argparse.ArgumentParser()
parser.add_argument("--url", required=False, help="Enter a target url.")
parser.add_argument("--wordlist", required=False, help="Select a wordlist.")
parser.add_argument("--status", required=False, nargs='+', help="Filter status codes.")
parser.add_argument("--install", required=False, help="Install d00r on your system.", action="store_true")
parser.add_argument("--thread", required=False, help="How many thread do you want ?")
args = parser.parse_args()

if args.install:
    if platform.system() == "Windows":
        user_bin = os.path.join(os.environ["USERPROFILE"], "bin")
        os.makedirs(user_bin, exist_ok=True)

        bat_path = os.path.join(user_bin, "d00r.bat")
        script_path = os.path.abspath(__file__)

        with open(bat_path, "w") as f:
            f.write(f'@echo off\npython "{script_path}" %*\n')

        print(f"{cyan}[+]{white} Installed! Make sure {user_bin} is in your PATH.")

    else:
        if not hasattr(os, "getuid") or os.getuid() != 0:
            print(f"{cyan}[{red}!{cyan}]{white} Use this argument with root privileges.")
        else:
            command = "cp d00r.py d00r; chmod +x d00r; mv d00r /usr/bin/"
            os.system(command)
            print(f"{cyan}[+]{white} Installed! Now you can run {red}d00r{white} from any terminal.")


if args.thread is not None:
    thread_num = int(args.thread)

# Using the arguments
targeturl = str(args.url)
try:
    wlist = open(args.wordlist,'r').read().split('\n')
except:
    print(f"{cyan}[{red}!{cyan}]{white} Please use -h to see available arguments")
    sys.exit(1)

# Checking how many words in that list and putting in queue
count=0
q = queue.Queue()
for w in wlist:
    w = w.strip()
    if not w:
        continue
    q.put(w)
    count+=1

# Outputs
print(f"{cyan}[{red}*{cyan}]{white} Target URL: {targeturl}")
print(f"{cyan}[{red}*{cyan}]{white} Wordlist: {args.wordlist}")
print(f"{cyan}[{red}*{cyan}]{white} Status Codes: {args.status}")
print(f"\n{cyan}[{red}*{cyan}]{white} d00r IS CHECKING DIRECTORIES PLEASE WAIT [CTRL+C TO STOP]...")
print("\n")

# Helper: pull page title if present
def clean_html_text(raw_text):
    text_no_tags = re.sub(r"<[^>]+>", " ", raw_text, flags=re.IGNORECASE | re.DOTALL)
    return " ".join(unescape(text_no_tags).split())

def natural_sort_key(text):
    if text is None:
        text = ""
    parts = re.split(r"(\d+)", text.lower())
    key = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    return key

def extract_contest_label_from_title(title):
    match = re.search(r"\[(.*?)\]", title)
    if match:
        return " ".join(match.group(1).split())
    return title

def extract_title(body):
    match = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return " ".join(unescape(match.group(1)).split())

def extract_contest_name(body):
    match = re.search(
        r"<td[^>]*>\s*Contest:\s*</td>\s*<td[^>]*>(.*?)</td>",
        body,
        re.IGNORECASE | re.DOTALL
    )
    if not match:
        return ""
    return clean_html_text(match.group(1))

def build_target_url(base, inject):
    inject = inject.strip()
    if not inject:
        return ""
    if inject.startswith("http://") or inject.startswith("https://"):
        return inject

    # Query-value bruteforce mode, e.g. ...?contest_id=
    if "?" in base and base.endswith("="):
        return f"{base}{inject.lstrip('/?&')}"

    # Directory/path bruteforce mode
    if not base.endswith("/"):
        base = f"{base}/"
    return f"{base}{inject.lstrip('/')}"

# Scanner (brute-force) function
def scanner():
    global attempted_requests, request_errors
    try:
        while True:
            try:
                inject = q.get_nowait()
            except queue.Empty:
                break

            kn0ck = build_target_url(targeturl, inject)
            if not kn0ck:
                continue
            with hits_lock:
                attempted_requests += 1
            try:
                r = requests.get(kn0ck, timeout=10)
            except requests.RequestException:
                with hits_lock:
                    request_errors += 1
                continue

            ret = f'{r.status_code}'
            title = extract_title(r.text)
            title_lower = title.lower()

            if args.status is None or ret in args.status:
                print(f"Status {green}{ret}{white} => {green}{kn0ck}{white}")
                with hits_lock:
                    hits.append((kn0ck, ret))

            if "error: invalid contest" in title_lower:
                print(f"[{red}!{white}] {red}Error: Invalid contest{white} => {red}{kn0ck}{white}")
                with hits_lock:
                    invalid_contest_hits.append(kn0ck)

            if "user login page" in title_lower:
                with hits_lock:
                    login_page_hits.append((kn0ck, title))
            
            if "permission denied" in title_lower:
                contest_name = extract_contest_name(r.text)
                if contest_name:
                    print(f"[{red}!{white}] {red}Permission denied{white} => {red}{kn0ck}{white} | Contest: {green}{contest_name}{white}")
                else:
                    print(f"[{red}!{white}] {red}Permission denied{white} => {red}{kn0ck}{white}")
                with hits_lock:
                    permission_denied_hits.append((kn0ck, title, contest_name))

    except KeyboardInterrupt:
        print(f"\n{cyan}[{red}!{cyan}]{white} Program terminated by user.")

# Handling threads
ts = []
for i in range(0,thread_num):
    try:
        t = threading.Thread(target=scanner)
        ts.append(t)
        t.start()
    except Exception as e:
        print(e)
for t in ts:
    t.join()

# Write report automatically with URLs that contain "User login page" in title.
report_file = "user_login_page_report.txt"
seen_urls = set()
unique_login_hits = []
for url, title in login_page_hits:
    if url not in seen_urls:
        seen_urls.add(url)
        unique_login_hits.append((url, title))
unique_login_hits.sort(key=lambda item: natural_sort_key(extract_contest_label_from_title(item[1])))

permission_hits_by_url = {}
for url, title, contest_name in permission_denied_hits:
    if url not in permission_hits_by_url:
        permission_hits_by_url[url] = (title, contest_name)
        continue

    known_title, known_contest_name = permission_hits_by_url[url]
    if not known_contest_name and contest_name:
        permission_hits_by_url[url] = (title, contest_name)

unique_permission_denied_hits = []
for url, (title, contest_name) in permission_hits_by_url.items():
    unique_permission_denied_hits.append((url, title, contest_name))
unique_permission_denied_hits.sort(
    key=lambda item: natural_sort_key(item[2] if item[2] else extract_contest_label_from_title(item[1]))
)

with open(report_file, "w", encoding="utf-8") as f:
    f.write("d00r title match report\n")
    f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 40 + "\n")
    f.write("User login page matches\n")
    f.write("-" * 40 + "\n")
    if unique_login_hits:
        for url, title in unique_login_hits:
            f.write(f"{url} | {title}\n")
    else:
        f.write("No pages matched title pattern: User login page\n")
    f.write("\n")
    f.write("Permission denied matches\n")
    f.write("-" * 40 + "\n")
    if unique_permission_denied_hits:
        for url, title, contest_name in unique_permission_denied_hits:
            contest_name_output = contest_name if contest_name else "Unknown contest name"
            f.write(f"{url} | Contest: {contest_name_output} | {title}\n")
    else:
        f.write("No pages matched title pattern: Permission denied\n")

print(f"\n{cyan}[{red}*{cyan}]{white} Report saved to {green}{report_file}{white} (login: {len(unique_login_hits)}, permission denied: {len(unique_permission_denied_hits)}).")
if invalid_contest_hits:
    print(f"{cyan}[{red}*{cyan}]{white} Invalid contest title detected on {red}{len(invalid_contest_hits)}{white} URL(s).")
if unique_permission_denied_hits:
    print(f"{cyan}[{red}*{cyan}]{white} Permission denied title detected on {red}{len(unique_permission_denied_hits)}{white} URL(s).")
print(f"{cyan}[{red}*{cyan}]{white} Requests sent: {attempted_requests} | Errors: {request_errors} | Status matches: {len(hits)}")
