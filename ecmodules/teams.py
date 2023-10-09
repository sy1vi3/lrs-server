"""
Responsible for interfacing with team database table
"""
import csv
import eclib.db.teams
import eclib.db.users
import eclib.roles
import eclib.db.inspection
import echelpers as ech
import random
import string
import requests
import files.tokens as tokens
import ecusers
import ecsocket
import ecmodules.skills
import ecmodules.inspection

async def get_teams(db):
    teams = dict()
    team_users = await db.select(eclib.db.users.table_, [(eclib.db.users.role, "==", eclib.roles.team)])
    for user in team_users:
        teams[user["name"]] = {"Role": user["role"], "Passcode": user["passcode"], "Enabled": user['enabled']}
    msg = {"api": "Team Control", "operation": "update_teams", "teams": teams}
    await ecsocket.send_by_access(msg, eclib.apis.event_ctrl)


async def load(db):
    """
    Load team profiles from registration CSV file

    :param db: database object
    :type db: ecdatabase.Database
    :param file: path to CSV file
    :type file: str
    """
    teams_loaded = []
    fail_read = False
    with open('files/event_code.txt', 'r') as f:
        event_code = f.read()
    headers = {"Authorization": f"Bearer {tokens.re_read_token}"}
    try:
        team_data_object = []
        response = requests.get(f'https://www.robotevents.com/api/v2/events?sku[]={event_code}', headers=headers).json()
        id = response['data'][0]['id']
        response = requests.get(f'https://www.robotevents.com/api/v2/events/{id}/teams', headers=headers).json()
        meta = response['meta']
        num_pages = meta['last_page']
        for page in range(num_pages):
            url = f'https://www.robotevents.com/api/v2/events/{id}/teams?page={page+1}'
            response = requests.get(url, headers=headers).json()
            for team in response['data']:
                team_data_object.append(team)
    except Exception as e:
        print(e)
        fail_read = True
        team_data_object = []

    for team in team_data_object:
        programs = team['program']['code']
        if "VRC" in programs or "VEXU" in programs:
            comp = "VRC"
        elif "VIQC" in programs:
            comp = "VIQC"
        else:
            comp = "VRC"

        try:
            div = team['division']
        except:
            if comp == "VRC":
                div = "VRC Division 1"
            elif comp == "VIQC":
                div = "VIQC Division 1"
        try:
            teamnumber = team['number']
        except:
            teamnumber = "UNKNOWN"
        try:
            teamname = team['team_name']
        except:
            teamname = "UNKNOWN"
        try:
            teamorg = team["organization"]
        except:
            teamorg = "UNKNOWN"
        try:
            teamloc = team["location"]['city'] + ", " + team["location"]['region'] + ", " + team["location"]['country']
        except:
            teamloc = "UNKNOWN"
            print(f'ERROR TEAM GEN: {teamnumber}')
        try:
            grade = team['grade']
        except:
            grade = "High School"


        await db.upsert(eclib.db.teams.table_, {
            eclib.db.teams.team_num: teamnumber,
            eclib.db.teams.team_name: teamname,
            eclib.db.teams.organization: teamorg,
            eclib.db.teams.location: teamloc,
            eclib.db.teams.div: div,
            eclib.db.teams.comp: comp,
            eclib.db.teams.grade: grade
        }, eclib.db.teams.team_num)
        await db.upsert(eclib.db.inspection.table_, {
            eclib.db.inspection.team_num: teamnumber,
            eclib.db.inspection.result: eclib.db.inspection.result_not_started,
            eclib.db.inspection.form_data: ""
        }, eclib.db.inspection.team_num)
        teams_loaded.append(teamnumber)
    usedCodes = []
    teamsfile_teams = []
    teams_need_code = []
    teams_need_remove = []
    just_users_teams = []

    if fail_read == False:

        old_teams = await db.select(eclib.db.users.table_, [("role", "==", eclib.roles.team)])
        also_old_teams = await db.select(eclib.db.teams.table_, [])
        for team in old_teams:
            teamsfile_teams.append(team['name'])
            just_users_teams.append(team['name'])
            usedCodes.append(team['passcode'])
        for team in also_old_teams:
            if team not in teamsfile_teams:
                teamsfile_teams.append(team['teamNum'])
        for team in teams_loaded:
            if team not in just_users_teams:
                teams_need_code.append(team)
        for team in teamsfile_teams:
            if team not in teams_loaded:
                teams_need_remove.append(team)




        for team in teams_need_code:
            new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
            while new_code in usedCodes:
                new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
            row = {
                eclib.db.users.name: team,
                eclib.db.users.passcode: new_code,
                eclib.db.users.role: eclib.roles.team,
                eclib.db.users.enabled: 1
            }
            await db.upsert(eclib.db.users.table_, row, eclib.db.users.name)


    for team in teams_need_remove:
        # print(team)
        await db.delete(eclib.db.users.table_, [(eclib.db.users.name, "==", team)])
        await db.delete(eclib.db.inspection.table_, [(eclib.db.inspection.team_num, "==", team)])
        await db.delete(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team)])
        await db.delete(eclib.db.skills.table_, [(eclib.db.skills.team_num, "==", team)])

    await ecmodules.skills.load_attempts(db)
    await ecmodules.inspection.load_inspected_teams(db)
    await ecmodules.inspection.push_to_ctrl(db)
    await ecusers.User.load_users(db)
    await get_teams(db)
    print("LOADED TEAMS")

async def handler(db, operation, payload):
    if operation == "edit":
        all_users = await db.select(eclib.db.users.table_, [])
        user_edit_data = payload['user_info']
        teamnum = user_edit_data['Name']
        passcode = user_edit_data['Passcode']

        enabled = 1
        used_codes = list()
        for u in all_users:
            used_codes.append([u['passcode'], u['name']])
            if u['name'] == teamnum:
                enabled = u['enabled']
        codesonly = list()
        for u in all_users:
            codesonly.append(u['passcode'])

        passcode_safe = True
        for u in used_codes:
            if u[0] == passcode and u[1] != teamnum:
                passcode_safe = False

        if passcode == "changeme" or passcode_safe == False or passcode == "":
            new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
            while new_code in codesonly:
                new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
            passcode = new_code

        row = {
            eclib.db.users.name: teamnum,
            eclib.db.users.passcode: passcode,
            eclib.db.users.role: eclib.roles.team,
            eclib.db.users.enabled: enabled
        }

        await db.update(eclib.db.users.table_, [(eclib.db.users.name, "==", teamnum), (eclib.db.users.role, "==", eclib.roles.team)], row)
        await get_teams(db)
        await ecusers.User.load_users(db)
