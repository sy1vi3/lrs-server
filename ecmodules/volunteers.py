import csv
import eclib.db.teams
import eclib.db.users
import eclib.db.inspection
import echelpers as ech
import random
import string
import requests
import files.tokens as tokens
import ecusers
import ecsocket


async def get_volunteers(db):
    volunteers = dict()
    volunteer_users = await db.select(eclib.db.users.table_, [(eclib.db.users.role, "!=", eclib.roles.team)])
    for user in volunteer_users:
        volunteers[user["name"]] = {"Role": user["role"], "Passcode": user["passcode"]}
    msg = {"api": "Volunteers", "operation": "update", "volunteers": volunteers}
    await ecsocket.send_by_access(msg, eclib.apis.event_ctrl)

async def delete(db, user, data):
    username = data
    if username != user.name:
        await db.delete(eclib.db.users.table_, [(eclib.db.users.name, "==", username)])
        await get_volunteers(db)
        await ecusers.User.load_users(db)

async def add(db, data):
    all_users = await db.select(eclib.db.users.table_, [])
    if data['Passcode'] == "changeme" or data['Passcode'] == "":
        used_codes = list()
        for u in all_users:
            used_codes.append(u['passcode'])
        new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
        while new_code in used_codes:
            new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
        data['Passcode'] = new_code

    row = {
        eclib.db.users.name: data['Name'],
        eclib.db.users.role: data['Role'],
        eclib.db.users.passcode: data['Passcode'],
        eclib.db.users.enabled: 1
    }

    used_names = list()
    for u in all_users:
        used_names.append(u['name'])
    if data['Name'] not in used_names:
        await db.insert(eclib.db.users.table_, row)
    else:
        print("USERADD FAILED: DUPLICATE NAME")
    await get_volunteers(db)
    await ecusers.User.load_users(db)

async def edit(db, data):
    all_users = await db.select(eclib.db.users.table_, [])

    used_codes = list()
    for u in all_users:
        used_codes.append([u['passcode'], u['name']])
    codesonly = list()
    for u in all_users:
        codesonly.append(u['passcode'])

    passcode_safe = True
    for u in used_codes:
        if u[0] == data['Passcode'] and u[1] != data['Name']:
            passcode_safe = False

    if data['Passcode'] == "changeme" or passcode_safe == False or data['Passcode'] == "":
        new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
        while new_code in used_codes:
            new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
        data['Passcode'] = new_code

    used_names = list()
    for u in all_users:
        used_names.append(u['name'])
    if data['Name'] not in used_names or (data['Name'] == data['OldName']):
        row = {
            eclib.db.users.name: data['Name'],
            eclib.db.users.role: data['Role'],
            eclib.db.users.passcode: data['Passcode'],
            eclib.db.users.enabled: 1
        }
        await db.update(eclib.db.users.table_, [(eclib.db.users.name, "==", data['OldName'])], row)
    else:
        print("USEREDIT FAILED: DUPLICATE NAME")
    await get_volunteers(db)
    await ecusers.User.load_users(db)

async def handler(db, operation, payload, user):
    if operation == "get_volunteers":
        await get_volunteers(db)
    elif operation == "delete":
        volunteers = payload['user_info']
        await delete(db, user, volunteers)
    elif operation == "add":
        volunteers = payload['user_info']
        await add(db, volunteers)
    elif operation == "edit":
        volunteers = payload['user_info']
        await edit(db, volunteers)
