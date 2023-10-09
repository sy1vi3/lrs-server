import eclib.db.skills
import eclib.db.rankings
import eclib.db.teams
import eclib.db.users
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
import random
import string



async def handler(payload, operation, client, db):
    if operation == "send_code":
        if (code := payload['code']) is not None:
            endpoint = "https://www.robotevents.com/oauth/token"
            data = {
                "client_id": 8,
                "client_secret": tokens.secret,
                "redirect_uri": "https://console.liveremoteskills.org/oauth/login/",
                "grant_type": "authorization_code",
                "code": code
            }
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }

            r = requests.post(endpoint, json=data, headers=headers)
            response = json.loads(r.text)
            if 'access_token' in response:
                token = response['access_token']
                headers = {
                    'Accept': 'application/json',
                    "Authorization": f"Basic {tokens.re_test_login}",
                    "X-Auth-Token": token,
                    'Content-Type': 'application/json'
                }
                id_response = requests.get(f'https://www.robotevents.com/api/me', headers=headers).json()
                response = requests.get(f'https://www.robotevents.com/api/v2/teams?myTeams=true', headers=headers).json()
                user_id = id_response['id']
                if (meta := response['meta']) is not None:
                    num_pages = meta['last_page']
                    account_teams = []
                    teams_codes = []
                    account_data = {}


                    events = []
                    admin = False
                    with open('files/config.json', 'r') as f:
                        config = json.load(f)
                        for event in config['events']:
                            events.append(event['event-code'])

                    for event in events:
                        admin_response = requests.get(f'https://www.robotevents.com/api/v2/events?sku[]={event}&administrators[]={user_id}', headers=headers).json()
                        if len(admin_response['data']) >= 1:
                            admin = True

                    if user_id in tokens.admins.keys():
                        admin = False
                        u_name = tokens.admins[user_id]
                        sp_u_exist = False
                        for u in ecusers.User.userlist:
                            if u.name == u_name and u.role == eclib.roles.event_partner:
                                sp_u_exist = True
                                account_teams.append(u_name)
                            elif u.name == u_name:
                                u_name = u_name + "-EP"
                        if sp_u_exist == False:
                            all_users = await db.select(eclib.db.users.table_, [])
                            used_codes = list()
                            for u in all_users:
                                used_codes.append(u['passcode'])
                            new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
                            while new_code in used_codes:
                                new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
                            row = {
                                eclib.db.users.name: u_name,
                                eclib.db.users.passcode: new_code,
                                eclib.db.users.role: eclib.roles.event_partner,
                                eclib.db.users.enabled: 1,
                                eclib.db.users.event: "ALL"
                            }
                            ech.log(f"NEW USER: {u_name}: {new_code}")
                            await db.insert(eclib.db.users.table_, row)
                            await ecusers.User.load_users(db)
                            sp_u_exist = True
                            account_teams.append(u_name)

                    if user_id in tokens.refs.keys():
                        admin = False
                        u_name = tokens.refs[user_id]
                        sp_u_exist = False
                        for u in ecusers.User.userlist:
                            if u.name == u_name and u.role == eclib.roles.referee:
                                sp_u_exist = True
                                account_teams.append(u_name)
                            elif u.name == u_name:
                                u_name = u_name + "-Ref"
                        if sp_u_exist == False:
                            all_users = await db.select(eclib.db.users.table_, [])
                            used_codes = list()
                            for u in all_users:
                                used_codes.append(u['passcode'])
                            new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
                            while new_code in used_codes:
                                new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
                            row = {
                                eclib.db.users.name: u_name,
                                eclib.db.users.passcode: new_code,
                                eclib.db.users.role: eclib.roles.referee,
                                eclib.db.users.enabled: 1,
                                eclib.db.users.event: "ALL"
                            }
                            ech.log(f"NEW USER: {u_name}: {new_code}")
                            await db.insert(eclib.db.users.table_, row)
                            await ecusers.User.load_users(db)
                            sp_u_exist = True
                            account_teams.append(u_name)

                    if user_id in tokens.producers.keys():
                        admin = False
                        u_name = tokens.producers[user_id]
                        sp_u_exist = False
                        for u in ecusers.User.userlist:
                            if u.name == u_name and u.role == eclib.roles.producer:
                                sp_u_exist = True
                                account_teams.append(u_name)
                        if sp_u_exist == False:
                            all_users = await db.select(eclib.db.users.table_, [])
                            used_codes = list()
                            for u in all_users:
                                used_codes.append(u['passcode'])
                            new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
                            while new_code in used_codes:
                                new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
                            row = {
                                eclib.db.users.name: u_name,
                                eclib.db.users.passcode: new_code,
                                eclib.db.users.role: eclib.roles.producer,
                                eclib.db.users.enabled: 1,
                                eclib.db.users.event: "ALL"
                            }
                            ech.log(f"NEW USER: {u_name}: {new_code}")
                            await db.insert(eclib.db.users.table_, row)
                            await ecusers.User.load_users(db)
                            sp_u_exist = True
                            account_teams.append(u_name)

                    if user_id in tokens.staff.keys():
                        admin = False
                        u_name = tokens.staff[user_id]
                        sp_u_exist = False
                        for u in ecusers.User.userlist:
                            if u.name == u_name and u.role == eclib.roles.staff:
                                sp_u_exist = True
                                account_teams.append(u_name)
                        if sp_u_exist == False:
                            all_users = await db.select(eclib.db.users.table_, [])
                            used_codes = list()
                            for u in all_users:
                                used_codes.append(u['passcode'])
                            new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
                            while new_code in used_codes:
                                new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
                            row = {
                                eclib.db.users.name: u_name,
                                eclib.db.users.passcode: new_code,
                                eclib.db.users.role: eclib.roles.staff,
                                eclib.db.users.enabled: 1,
                                eclib.db.users.event: "ALL"
                            }
                            ech.log(f"NEW USER: {u_name}: {new_code}")
                            await db.insert(eclib.db.users.table_, row)
                            await ecusers.User.load_users(db)
                            sp_u_exist = True
                            account_teams.append(u_name)
                    if user_id in tokens.teams.keys():
                        admin = False
                        u_names = tokens.teams[user_id]
                        sp_u_exist = False
                        for u_name in u_names:
                            for u in ecusers.User.userlist:
                                if u.name == u_name and u.role == eclib.roles.team:
                                    sp_u_exist = True
                                    account_teams.append(u_name)
                            if sp_u_exist == False:
                                all_users = await db.select(eclib.db.users.table_, [])
                                used_codes = list()
                                for u in all_users:
                                    used_codes.append(u['passcode'])
                                new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
                                while new_code in used_codes:
                                    new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
                                row = {
                                    eclib.db.users.name: u_name,
                                    eclib.db.users.passcode: new_code,
                                    eclib.db.users.role: eclib.roles.team,
                                    eclib.db.users.enabled: 1,
                                    eclib.db.users.event: "ALL"
                                }
                                ech.log(f"NEW USER: {u_name}: {new_code}")
                                await db.insert(eclib.db.users.table_, row)
                                await ecusers.User.load_users(db)
                                sp_u_exist = True
                                account_teams.append(u_name)
                    if admin:
                        admin_exist = False
                        for u in ecusers.User.userlist:
                            if u.name == "Admin" and u.role == eclib.roles.event_partner:
                                admin_exist = True
                                account_teams.append(u.name)
                        if admin_exist == False:
                            await ecusers.User.load_users(db)
                            admin_exist = True
                            account_teams.append("Admin")

                    for page in range(num_pages):
                        response = requests.get(f'https://www.robotevents.com/api/v2/teams?myTeams=true&page={page}', headers=headers).json()
                        data = response['data']

                        for team in data:
                            account_teams.append(team['number'])
                        teams = await db.select(eclib.db.users.table_, [])
                        for team in account_teams:
                            for row in teams:
                                if(row['name'] == team):
                                    teams_codes.append([team, row['passcode']])
                        for team in teams_codes:
                            account_data[team[0]] = team[1]
                    msg = {"api": "OAuth", "operation": "teams_codes", "codes": account_data}
                    await ecsocket.send_by_client(msg, client)
