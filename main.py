import argparse
import os
import time
import sqlite3
import requests
import re
import random
import string
from requests.auth import HTTPBasicAuth
from datetime import datetime
from datetime import timedelta

# Function to check if a file already exists in the database
def file_exists(filename):
    conn = sqlite3.connect('files.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE filename=?", (filename,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Function to insert a file into the database
def insert_file(filename):
    conn = sqlite3.connect('files.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (filename) VALUES (?)", (filename,))
    conn.commit()
    conn.close()


# Function to generate a random agent key
def generate_agent_key():
    key_length = 10
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(key_length))



def post_file(input):
    url = args.nemesis
    username = args.nemesisuser
    password = args.nemesispass
    agent_key = generate_agent_key()

    r = requests.request("POST", f"{url}/file", auth=HTTPBasicAuth(username, password), data=input, headers={"Content-Type": "application/octet-stream"})
    if not r.ok:
        raise Exception(f"Failed to upload ({r.status_code}): {r.reason}")

    json_result = r.json()
    object_id = json_result["object_id"]

    # Calculate fields for download_object
    startTime = datetime.now()
    fileSize = len(input)
    filename = os.path.basename(input)

    expiration = (startTime + timedelta(days=90)).replace(microsecond=0)

    metadata = {
        "agent_id": agent_key,
        "agent_type": "brc4",
        "automated": True,
        "data_type": "file_data",
        "source": "none",
        "project": "brc4",
        "timestamp": startTime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "expiration": expiration.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    }

    file_data = {
        "path": filename,
        "size": fileSize,
        "object_id": object_id,
    }

    post_data = {"metadata": metadata, "data": [file_data]}

    # Set up web proxy
    proxies = {
        "http": {args.proxy},
        "https": {args.proxy},
    }

    # Make the request with the web proxy
    if args.proxy:
        r = requests.request("POST", f"{url}/data", auth=HTTPBasicAuth(username, password), json=post_data, headers={"Content-Type": "application/json"}, proxies=proxies)
    else:
        r = requests.request("POST", f"{url}/data", auth=HTTPBasicAuth(username, password), json=post_data, headers={"Content-Type": "application/json"})
    #r = requests.request("POST", f"{url}/data", auth=HTTPBasicAuth(username, password), json=post_data, headers={"Content-Type": "application/json"})
    if not r.ok:
        raise Exception(f"Failed to update ({r.status_code}): {r.reason}")
    else:
        print(f"File uploaded: {filename}")
        insert_file(filename)

# Function to monitor the folder for changes
def monitor_folder(download_dir):
    while True:
        for filename in os.listdir(download_dir):
            if not file_exists(filename):
                print(f"New file detected: {filename}")
                post_file(os.path.join(download_dir, filename))
        time.sleep(60)

# Parse command line arguments
# Function to check if the provided URL is valid
def is_valid_url(url):
    regex = r'^https?://(?:[a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9])(?:\.[a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9])(?::[0-9]{1,5})?(?:/.*)?$'
    return re.match(regex, url) is not None

parser = argparse.ArgumentParser()
parser.add_argument('--downloaddir', '-d', help='Download directory')
parser.add_argument('--nemesis', '-n', help='Nemesis API server endpoint', default='http://nemesis:8080/api')
parser.add_argument('--nemesisuser', '-u', help='Nemesis API username', default='nemesis')
parser.add_argument('--nemesispass', '-p', help='Nemesis API password', default='nemesis')
parser.add_argument('--proxy', help='Proxy server endpoint (e.g. http://127.0.0.1:8080)', default=None)
args = parser.parse_args()
# Check if the database file exists, if not, create it with the correct schema and tables
if not os.path.exists('files.db'):
    conn = sqlite3.connect('files.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE files (filename TEXT)")
    conn.commit()
    conn.close()

# Check if the provided URL is valid
#if not is_valid_url(args.nemesis):
#    print("Invalid Nemesis API server endpoint. Please provide a valid URL.")
#    exit(1)

# Start monitoring the folder
if args.downloaddir:
    monitor_folder(args.downloaddir)
else:
    print("Please provide a download directory using --downloaddir or -d argument.")