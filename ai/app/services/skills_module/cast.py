## lighcast
import requests

url = "https://auth.emsicloud.com/connect/token"

payload = "client_id=srd8q4o584g8clzz&client_secret=FiniLo36&grant_type=client_credentials&scope=emsi_open"
headers = {"Content-Type": "application/x-www-form-urlencoded"}

response = requests.request("POST", url, data=payload, headers=headers)
access_token = response.json()["access_token"]


url = "https://emsiservices.com/skills/versions/latest/skills"

querystring = {"fields": "name,type"}

headers = {"Authorization": f"Bearer {access_token}"}

response = requests.request("GET", url, headers=headers, params=querystring)

import json

with open("skills.json", "w") as f:
    json.dump(response.json(), f, indent=4)
