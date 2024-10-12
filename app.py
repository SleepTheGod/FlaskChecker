from flask import Flask, render_template, request, jsonify
import requests
import random
import threading
from queue import Queue

app = Flask(__name__)

# List of proxies
proxies = [
    "http://37.135.50.196:53281",
    "http://201.20.98.22:37596",
    "http://162.251.158.207:59830",
    "http://78.130.145.167:39825",
    "http://217.219.247.208:8080",
    "http://200.25.254.193:54240",
    "http://103.250.68.213:38562",
    "http://45.114.144.144:48642",
    "http://45.165.226.68:34456",
    "http://118.174.65.137:41137",
    "http://186.29.163.97:49787",
    "http://103.112.253.17:58449",
    "http://194.8.146.167:61941",
    "http://94.101.73.43:8080",
    "http://186.219.214.30:40456",
    "http://159.224.226.164:33803",
    "http://203.173.93.20:59661",
    "http://91.219.56.221:8080",
]

# Platforms available for checking
platforms = [
    "Xbox",
    "Instagram",
    "Twitter",
    "YouTube",
    "Pastebin",
    "GitHub",
    "Snapchat",
    "Gmail",
    "Yahoo",
    "Outlook",
    "ProtonMail",
    "Facebook",
]

# Read user agents from file
def read_user_agents_from_file(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

# Function to check username availability
def check_username(platform, username, proxy, user_agent):
    try:
        # Construct the URL based on the platform
        url = ""
        headers = {
            "User-Agent": user_agent
        }

        if platform == "xbox":
            url = f"https://xboxapi.com/api/v2/user/{username}"
        elif platform == "instagram":
            url = f"https://www.instagram.com/{username}/?__a=1"
        elif platform == "twitter":
            url = f"https://twitter.com/{username}"
        elif platform == "youtube":
            url = f"https://www.youtube.com/{username}"
        elif platform == "pastebin":
            url = f"https://pastebin.com/u/{username}"
        elif platform == "github":
            url = f"https://api.github.com/users/{username}"
        elif platform == "snapchat":
            url = f"https://app.snapchat.com/username/{username}"
        elif platform in ["gmail", "yahoo", "outlook", "protonmail"]:
            return None  # No API for username checks
        elif platform == "facebook":
            url = f"https://www.facebook.com/{username}"

        # Make the request
        response = requests.get(url, headers=headers, proxies={"http": proxy, "https": proxy}, timeout=5)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.text

            # Simple checks for availability
            if platform == "instagram":
                return "The user does not exist" not in data
            elif platform == "github":
                return "404" not in data
            elif platform == "facebook":
                return "Sorry, this content isn't available" not in data
            elif platform == "twitter":
                return "This account doesn't exist" not in data
            elif platform == "pastebin":
                return "User not found" not in data

            return True  # Placeholder for platforms without specific checks
        else:
            return None
    except Exception as e:
        return None

# Worker function for threading
def worker(username, platform, results, user_agents):
    proxy = random.choice(proxies)
    user_agent = random.choice(user_agents)
    available = check_username(platform, username, proxy, user_agent)

    if available is not None:
        results[(platform, username)] = "Available" if available else "Not Available"
    else:
        results[(platform, username)] = "Error"

@app.route('/')
def index():
    return render_template('index.html', platforms=platforms)

@app.route('/check_usernames', methods=['POST'])
def check_usernames():
    usernames = request.form.get('usernames').splitlines()
    selected_platforms = request.form.getlist('platforms')
    user_agents = read_user_agents_from_file("useragents.txt")
    results = {}

    queue = Queue()
    for platform in selected_platforms:
        for username in usernames:
            queue.put((username.strip(), platform.lower()))

    threads = []
    for _ in range(100):  # Adjust the number of threads for speed
        thread = threading.Thread(target=lambda q=queue: worker(*q.get(), results, user_agents))
        thread.start()
        threads.append(thread)

    queue.join()

    # Ensure all threads complete before sending the response
    for thread in threads:
        thread.join()

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
