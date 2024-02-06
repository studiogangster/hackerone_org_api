import os
import traceback
from bs4 import BeautifulSoup
import json
import pickle
import time
import http.cookiejar
import requests
from tinydb import TinyDB, Query
from time import sleep

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Access environment variables
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
COOKIE_FILE = os.getenv('COOKIE_FILE')
LOGIN_EMAIL = os.getenv('LOGIN_EMAIL')
LOGIN_PASSWORD = os.getenv('LOGIN_PASSWORD')
HACKERONE_ORG_HANDLE = os.getenv('HACKERONE_ORG_HANDLE')



# ... (rest of your code)
LAST_CURSOR_ID = "LAST_CURSOR_ID"
SLEEP_INTERVAL = 60  # in  seconds


# Define headers for requests
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0"
}

# Proxies configuration
http_proxy = "http://localhost:8080"
https_proxy = "http://localhost:8080"

proxies = {}

DEBUG_MODE = False

if DEBUG_MODE:
    proxies = {
        "http": http_proxy,
        "https": https_proxy,
    }


def export_to_webhook(summary, description, url):
    """Send data to Spog webhook."""
    payload_data = {
        "summary": summary,
        "description": description,
        "service": url,
        "tag": ["TEAM:Security Management"]
    }

    response = requests.post(WEBHOOK_URL, headers=headers,
                             json=payload_data, proxies=proxies, verify=False)

    print(response.content)
    if response.status_code == 200:
        print("Webhook successfully sent!")
    else:
        print(f"Failed to send webhook. Status code: {response.status_code}")
        print(response.text)


class StateManager:
    """Manage state using TinyDB."""

    def get_last_cursor_id(self):
        return self.get_int(LAST_CURSOR_ID, default=0)

    def set_last_cursor_id(self, val):
        print("set_last_cursor_id", val)
        return self.set_int(LAST_CURSOR_ID, val)

    def __init__(self, db_file='.state_db.json'):
        self.db = TinyDB(db_file)

    def set_string(self, key, value):
        self.db.upsert({'key': key, 'value': value}, Query().key == key)

    def get_string(self, key, default=None):
        result = self.db.get(Query().key == key)
        return result['value'] if result else default

    def set_list(self, key, value):
        self.db.upsert({'key': key, 'value': value}, Query().key == key)

    def get_list(self, key, default=None):
        result = self.db.get(Query().key == key)
        return result['value'] if result else default

    def set_int(self, key, value):
        self.db.upsert({'key': key, 'value': value}, Query().key == key)

    def get_int(self, key, default=None):
        result = self.db.get(Query().key == key)
        return int(result['value']) if result and result['value'] is not None else default


class NewSession(requests.Session):
    """Session with different cookie handling."""

    def __init__(self, *args, **kwargs):
        super(NewSession, self).__init__(*args, **kwargs)
        self.load_cookies()

    def load_cookies(self):
        try:
            # Check if the file exists
            if not os.path.exists(COOKIE_FILE):
                # If the file does not exist, create an empty file
                with open(COOKIE_FILE, 'w') as empty_file:
                    pass

            # Load cookies from the file
            self.cookies = http.cookiejar.MozillaCookieJar(COOKIE_FILE)
            self.cookies.load(ignore_discard=True, ignore_expires=True)

        except Exception as e:
            traceback.print_exc()
            print(f"Error loading cookies: {e}")

    def save_cookies(self):
        # Save cookies using the different cookie jar
        self.cookies.save()

    def request(self, method, url, **kwargs):
        response = super(NewSession, self).request(method, url, **kwargs)
        self.save_cookies()
        return response


def check_if_logged_in():
    """Check if user is logged in."""
    csrf_token = fetchCSRF()
    _headers = headers.copy()
    _headers["X-Csrf-Token"] = csrf_token
    print(csrf_token)

    response = session.get("https://hackerone.com/gates",
                           headers=_headers, proxies=proxies, verify=False)

    data = response.json()
    if data == {}:
        return False
    else:
        return True


def fetchCSRF():
    """Fetch CSRF token."""
    response = session.get("https://hackerone.com/users/sign_in",
                           headers=headers, proxies=proxies, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    param = soup.select('meta[name="csrf-param"]')[0].attrs["content"]
    token = soup.select('meta[name="csrf-token"]')[0].attrs["content"]
    return token


def login(token):
    """Login to HackerOne."""
    _headers = headers.copy()
    _headers["X-Csrf-Token"] = token
    data = {
        "email": LOGIN_EMAIL,
        "password": LOGIN_PASSWORD,
        "remember_me": "true",
        "fingerprsint": "b13cb8c6c2fb0d56ea1252b3df82cb0c"
    }
    response = session.post("https://hackerone.com/sessions",
                            headers=_headers, data=data, proxies=proxies, verify=False)
    print(response.status_code)
    resp = response.content
    print(resp)
    peform_login(token)


def peform_login():
    """Perform login actions."""
    _headers = headers.copy()
    _headers["X-Csrf-Token"] = fetchCSRF()
    _headers["Content-Type"] = "application/json"

    url = "https://hackerone.com/graphql"
    payload = '{"operationName":"SignIn","variables":{"product_area":"user-management","product_feature":"signin"},"query":"query SignIn {\\n  me {\\n    id\\n    __typename\\n  }\\n  session {\\n    id\\n    csrf_token\\n    __typename\\n  }\\n}\\n"}'
    response = session.post(url, headers=_headers,
                            proxies=proxies, data=payload, verify=False)
    print(response.status_code)
    csrf_token = response.json()["data"]["session"]["csrf_token"]
    sign_in(csrf_token)


def get_issues(last_cursor=0):
    """Get new issues."""
    token = fetchCSRF()
    _headers = headers.copy()
    _headers["X-Csrf-Token"] = token
    _headers["Content-Type"] = "application/json"
    url = f"https://hackerone.com/bugs.json?subject={HACKERONE_ORG_HANDLE}&report_id=0&view=custom&substates%5B%5D=new&substates%5B%5D=triaged&substates%5B%5D=needs-more-info&substates%5B%5D=resolved&substates%5B%5D=informative&substates%5B%5D=not-applicable&substates%5B%5D=duplicate&substates%5B%5D=spam&substates%5B%5D=retesting&reported_to_team=&text_query=&program_states%5B%5D=2&program_states%5B%5D=3&program_states%5B%5D=4&program_states%5B%5D=5&sort_type=submitted_at&sort_direction=descending&limit=1000&page=1"
    response = session.post(url, headers=_headers,
                            proxies=proxies, verify=False)
    print(response.status_code)
    data = response.json()
    pages = data["pages"]
    count = data["count"]
    bugs = data["bugs"]
    ids = []
    state_set = False
    for bug in bugs:
        id = int(bug["id"])
        if state_set is False:
            StateManager().set_last_cursor_id(id)
            state_set = True
        if id <= last_cursor:
            break
        ids.append(id)
    print("pages", pages)
    print("count", count)
    return ids


def get_last_issue():
    """Get details of the last issue."""
    token = fetchCSRF()
    _headers = headers.copy()
    _headers["X-Csrf-Token"] = token
    _headers["Content-Type"] = "application/json"
    url = f"https://hackerone.com/bugs.json?subject={HACKERONE_ORG_HANDLE}&report_id=0&view=custom&substates%5B%5D=new&substates%5B%5D=triaged&substates%5B%5D=needs-more-info&substates%5B%5D=resolved&substates%5B%5D=informative&substates%5B%5D=not-applicable&substates%5B%5D=duplicate&substates%5B%5D=spam&substates%5B%5D=retesting&reported_to_team=&text_query=&program_states%5B%5D=2&program_states%5B%5D=3&program_states%5B%5D=4&program_states%5B%5D=5&sort_type=submitted_at&sort_direction=descending&limit=10&page=1"
    response = session.post(url, headers=_headers,
                            proxies=proxies, verify=False)
    print(response.status_code)
    data = response.json()
    pages = data["pages"]
    count = data["count"]
    bugs = data["bugs"]
    ids = []
    bugs = bugs[:1]

    print("pages", pages)
    print("count", count)
    return int( bugs[0]["id"]  )


def get_issues_detail(id):
    """Get details of a specific issue."""
    token = fetchCSRF()
    _headers = headers.copy()
    _headers["X-Csrf-Token"] = token
    _headers["Content-Type"] = "application/json"
    url = f"https://hackerone.com/reports/{id}.json"
    response = session.get(url, headers=_headers,
                           proxies=proxies, verify=False)
    data = response.json()
    id = data["id"]
    url = data["url"]
    title = data["title"]
    severity_rating = data["severity_rating"]
    vulnerability_information = data["vulnerability_information"]
    export_to_webhook(
        title, f"Severity: {severity_rating} \n\nReference:\n\n{url}\n\nDetails:\n{vulnerability_information} ", url)
    return data


def sign_in(token):
    """Sign in to HackerOne."""
    url = "https://hackerone.com/users/sign_in"
    form_data = {
        'authenticity_token': token,
        'user[email]': LOGIN_EMAIL,
        'user[password]': LOGIN_PASSWORD,
        'user[remember_me]': '1'
    }
    response = session.post(url, data=form_data,
                            headers=headers, verify=False, proxies=proxies)
    print(response.status_code)
    print(response.text)


def main():
    state_manager = StateManager()

    """Main function to check login status and fetch issues."""
    logged_in = check_if_logged_in()

    if not logged_in:
        peform_login()
        logged_in = check_if_logged_in()
        
    print("Logged In", logged_in)

    # For debug
    if DEBUG_MODE:
        last_cursor = state_manager.get_last_cursor_id()
        last_cursor = last_cursor - 4000
        if last_cursor < 0:
            last_cursor = 0
        state_manager.set_last_cursor_id(last_cursor)

    if logged_in:
        last_cursor = state_manager.get_last_cursor_id()

        print('last_cursor', last_cursor)

        new_bug_ids = []
        if last_cursor == 0:
            # Initialize the cursor
            try:
                last_cursor = get_last_issue()
                print("last_cursor", last_cursor)
                state_manager.set_last_cursor_id(last_cursor)
            except:
                traceback.print_exc()
                pass
        else:
            # Start reading new bugs occurring after the last cursor
            if last_cursor <= 0:
                last_cursor = 0
            new_bug_ids = get_issues(last_cursor)
            print("new_bug_ids", new_bug_ids)

        for id in new_bug_ids:
            print("bug_id", id , last_cursor)
            try:
                report = get_issues_detail(id)
                print(report)
                print()
            except:
                traceback.print_exc()

    else:
        raise Exception("Coudn't lgog in")

if __name__ == "__main__":
    # Initialize StateManager
    while True:
        try:

            last_time = time.strftime('%l:%M%p %Z on %b %d, %Y')
            print(last_time)
            session = NewSession()
            main()
        except:
            traceback.print_exc()
            
            pass
        sleep(SLEEP_INTERVAL)

# Initialize session with custom cookie handling
