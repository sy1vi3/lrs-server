import csv
import eclib.db.teams
import eclib.db.inspection
import echelpers as ech
import random
import string
import requests
import files.tokens as tokens
import ecusers
import ecsocket


async def get_volunteers():
    volunteers = {}
    with open('files/volunteers.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile, quoting=csv.QUOTE_ALL)
        for row in reader:
            volunteers[row["Name"]] = {"Role": row["Role"], "Passcode": row["Passcode"]}
    msg = {"api": "Volunteers", "operation": "update", "volunteers": volunteers}
    await ecsocket.send_by_access(msg, eclib.apis.event_ctrl)



async def update(data):
    volunteers = []
    for key in data:
        if data[key]['Passcode'] == "changeme":
            new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
            with open('files/volunteers.csv', 'r', newline='') as csvfile, open('files/teams.csv', 'r', newline='') as csvfile2:
                while new_code in csvfile.read() or new_code in csvfile2.read():
                    print("fail")
                    new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
            data[key]['Passcode'] = new_code
        volunteers.append([key, data[key]['Role'], data[key]['Passcode']])
    num_eps_new =  str(volunteers).count("Event Partner")
    with open('files/volunteers.csv', 'r', newline='') as csvfile:
        contents = csvfile.read()
        num_eps_old = contents.count("Event Partner")
    print(num_eps_new)
    print(num_eps_old)
    if num_eps_new < num_eps_old:
        print("Tried to remove an Event Partner")
        await get_volunteers()
    else:
        with open('files/volunteers.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(["Name", "Passcode", "Role"])
            for u in volunteers:
                writer.writerow([u[0], u[2], u[1]])
        await get_volunteers()
        ecusers.User.load_volunteers("files/volunteers.csv")

async def handler(db, operation, payload):
    print(operation)
    if operation == "get_volunteers":
        await get_volunteers()
    elif operation == "add_del":
        volunteers = payload['user_info']
        await update(volunteers)
