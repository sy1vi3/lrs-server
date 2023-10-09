import eclib.db.skills
import eclib.db.rankings
import eclib.db.teams
import ecsocket
import eclib.apis
import ecusers
import ecmodules.queue
import echelpers as ech
from datetime import datetime
import csv
import files.tokens as tokens
import requests



async def handler(payload, operation):
    if operation == "send_code":
        if (code := payload['code']) is not None:
            print(code)
            endpoint = "https://test.robotevents.com/oauth/token"
            data = {
                "client_id": 8,
                "client_secret": tokens.secret,
                "redirect_uri": "https://console.liveremoteskills.org/oauth/login/",
                "grant_type": "authorization_code",
                "code": code
            }
            headers = {
                'Accept': 'application/json',
                "Authorization": f"Basic {tokens.re_test_login}",
                'Content-Type': 'application/json'
            }

            r = requests.post(endpoint, json=data, headers=headers)

            print(r.text)
