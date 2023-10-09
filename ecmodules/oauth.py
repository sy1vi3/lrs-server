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
import json



async def handler(payload, operation, client):
    if operation == "send_code":
        if (code := payload['code']) is not None:
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
            response = json.loads(r.text)
            if (token := response['access_token']) is not None:
                headers = {
                    'Accept': 'application/json',
                    "Authorization": f"Basic {tokens.re_test_login}",
                    "X-Auth-Token": token,
                    'Content-Type': 'application/json'
                }
                response = requests.get(f'https://test.robotevents.com/api/v2/teams?myTeams=true', headers=headers).json()
                if (data := response['data']) is not None:
                    account_teams = []
                    teams_codes = []
                    account_data = {}
                    for team in data:
                        account_teams.append(team['number'])
                    for team in account_teams:
                        with open('files/teams.csv', newline='') as teamsfile:
                            teamsreader = csv.DictReader(teamsfile, quoting=csv.QUOTE_ALL)
                            for row in teamsreader:
                                if(row['Team Number'] == team):
                                    teams_codes.append([team, row['Passcode']])
                    for team in teams_codes:
                        account_data[team[0]] = team[1]
                    msg = {"api": "OAuth", "operation": "teams_codes", "codes": account_data}
                    await ecsocket.send_by_client(msg, client)
