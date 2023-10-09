"""
Handle queue-related tasks
"""
import eclib.db.queue
import eclib.db.teams
import ecsocket
import eclib.apis
import echelpers as ech
import eclib.roles
import ecusers
import string
import random
import ecmodules.output
import requests
import files.tokens as tokens
import threading
import time

def stop_room_recording(stopId, room, fileName):
    endpoint = "https://remote.robotevents.com/api/lrs/stop"
    headers = {
        'Accept': 'application/json',
        "X-Auth-Token": tokens.rre_token,
        'Content-Type': 'application/json'
    }
    info = {
      'stopId': stopId
    }
    r = requests.post(endpoint, headers=headers, json=info)
    if r.status_code == 204:
        ech.log(f"Stopped recording room {room}. Filename is {fileName}")
    else:
        ech.log(f"Error in stopping: {r}")

def start_room_recording(url, event, team, intent, room):
    intent = intent.replace(" ", "_")
    endpoint = "https://remote.robotevents.com/api/lrs/start"
    headers = {
        'Accept': 'application/json',
        "X-Auth-Token": tokens.rre_token,
        'Content-Type': 'application/json'
    }
    info = {
      "url": url,
      "eventCode": event,
      "teamNumber": team,
      "matchType": intent,
      "instance": round(time.time())
    }
    r = requests.post(endpoint, headers=headers, json=info)
    stopId = r.json()['stopId']
    fileName = r.json()['fileName']
    ecusers.User.event_room_data[room]['stopId'] = stopId
    ecusers.User.event_room_data[room]['fileName'] = fileName
    if r.status_code == 202 or r.status_code == 201:
        ech.log(f"Starting recording room {room}. StopId = {stopId}")
    else:
        ech.log(f"Error in starting {room}: {r.json()} | {r.status_code}")


async def rm_from_active(team):
    for room in ecusers.User.event_room_data:
        room_team = ecusers.User.event_room_data[room]['info']['team']
        if room_team == team:
            info = {
                "team": "",
                "location": "",
                "name": ""
            }
            ecusers.User.event_room_data[room]['info'] = info
            ecusers.User.event_room_data[room]['active'] = False
            msg = {"api": eclib.apis.livestream, "operation": "update", "room": room, "data": info}
            await ecsocket.send_by_role(msg, eclib.roles.livestream)
            room_data = ecusers.User.event_room_data
            msg = {"api": eclib.apis.output, "operation": "setAliveRooms", "data": room_data}
            await ecsocket.send_by_role(msg, eclib.roles.output)
            await ecmodules.output.reload_active()

            stopId = ecusers.User.event_room_data[room]['stopId']
            fileName = ecusers.User.event_room_data[room]['fileName']
            kill_thread = threading.Thread(target=stop_room_recording, args=(stopId, room, fileName), daemon=True)
            kill_thread.start()



async def push_update(db, client=None, user=None):
    """
    Send most current queue data.
    If `client` and `user` are specified, only sends the data to that client (for `get` requests).

    :param db: database object
    :type db: ecdatabase.Database
    :param client: target client (only for `get` requests)
    :type client: websockets.WebSocketCommonProtocol
    :param user: user of target client (only for `get` requests)
    :type user: ecusers.User
    """
    db_result = await db.select(eclib.db.queue.table_, [(eclib.db.queue.time_removed, "==", "0")])
    teams_queue = list()
    volunteers_queue = list()
    stream_queue = list()
    for row in db_result:
        purpose = row[eclib.db.queue.purpose]
        stream_queue.append({eclib.db.queue.team_num: row[eclib.db.queue.team_num], eclib.db.queue.purpose: purpose, eclib.db.queue.referee: row[eclib.db.queue.referee]})
        if purpose == eclib.db.queue.purpose_driving_skills:
            purpose = "Driving Skills"
        elif purpose == eclib.db.queue.purpose_programming_skills:
            purpose = "Programming Skills"
        else:
            purpose = "Inspection"
        teams_queue.append({
            eclib.db.queue.team_num: row[eclib.db.queue.team_num],
            eclib.db.queue.purpose: purpose,
            "ongoing": bool(row[eclib.db.queue.referee])
        })
        volunteers_queue.append({
            eclib.db.queue.team_num: row[eclib.db.queue.team_num],
            eclib.db.queue.purpose: purpose,
            eclib.db.queue.time_queued: ech.timestamp_to_readable(row[eclib.db.queue.time_queued]),
            eclib.db.queue.referee: row[eclib.db.queue.referee]
        })
    teams_msg = {"api": eclib.apis.queue, "operation": "post", "queue": teams_queue}
    volunteers_msg = {"api": eclib.apis.queue, "operation": "postCtrl", "queue": volunteers_queue}

    labels = [None] * len(ecusers.User.rooms)
    upcoming = list()
    for item in stream_queue:
        pickle = {eclib.db.queue.team_num: item[eclib.db.queue.team_num], eclib.db.queue.purpose: item[eclib.db.queue.purpose]}
        if item[eclib.db.queue.referee] and item[eclib.db.queue.purpose] > eclib.db.queue.purpose_inspection:
            for i, referee in enumerate(ecusers.User.rooms):
                if item[eclib.db.queue.referee] == referee.name:
                    labels[i] = pickle
                    break
        elif len(upcoming) < 3 and item[eclib.db.queue.purpose] > eclib.db.queue.purpose_inspection:
            upcoming.append(pickle)
    stream_msg = {"api": eclib.apis.livestream, "labels": labels, "upcoming": upcoming}

    if client is not None and user is not None:  # `get` request
        if user.has_access(eclib.apis.inspection, eclib.apis.skills):
            await ecsocket.send_by_client(teams_msg, client)
        if user.has_access(eclib.apis.inspection_ctrl, eclib.apis.skills_ctrl):
            await ecsocket.send_by_client(volunteers_msg, client)
        if user.has_access(eclib.apis.livestream):
            await ecsocket.send_by_client(stream_msg, client)
    else:  # save operation
        await ecsocket.send_by_access(volunteers_msg, eclib.apis.inspection_ctrl, eclib.apis.skills_ctrl)
        await ecsocket.send_by_access(teams_msg, eclib.apis.inspection, eclib.apis.skills)
        await ecsocket.send_by_access(stream_msg, eclib.apis.livestream)


async def team_queue(purpose, client, team, db):
    """
    Add team to queue.
    Executed by team.

    :param purpose: queue purpose
    :type purpose: int
    :param client: client that sent request
    :type client: websockets.WebSocketCommonProtocol
    :param team: team in question
    :type team: ecusers.User
    :param db: database object
    :type db: ecdatabase.Database
    """
    db_result = await db.select(eclib.db.queue.table_, [(eclib.db.queue.team_num, "==", team.name), (eclib.db.queue.time_removed, "==", 0)])
    if len(db_result) == 0:
        if purpose in (eclib.db.queue.purpose_driving_skills, eclib.db.queue.purpose_programming_skills):
            if not ech.SKILLS_OPEN:
                await ech.send_error(client, "Skills is currently closed.")
                return
            elif ech.SKILLS_ATTEMPTS[team.name][purpose - 1] >= 3:
                await ech.send_error(client, "You have exceeded your allowed " + ("Driving" if purpose == eclib.db.queue.purpose_driving_skills else "Programming") + " Skills attempts.")
                return
            elif team.name not in ech.INSPECTED_TEAMS:
                await ech.send_error(client, "You have not passed inspection.")
                return
        elif purpose == eclib.db.queue.purpose_inspection:
            if not ech.INSPECTION_OPEN:
                await ech.send_error(client, "Inspection is currently closed.")
                return
        else:
            await ech.send_error(client)
            return
        await db.insert(eclib.db.queue.table_, {eclib.db.queue.team_num: team.name, eclib.db.queue.purpose: purpose, eclib.db.queue.time_queued: ech.current_time()})
        await push_update(db)
    else:
        await ech.send_error(client, "You must leave the queue before you can queue again!")


async def team_unqueue(team, db):
    """
    Remove team from queue.
    Executed by team.

    :param team: team in question
    :type team: ecusers.User
    :param db: database object
    :type db: ecdatabase.Database
    """
    await db.update(eclib.db.queue.table_, [(eclib.db.queue.team_num, "==", team.name), (eclib.db.queue.time_removed, "==", 0)], {
        eclib.db.queue.removed_by: team.name,
        eclib.db.queue.time_removed: ech.current_time()
    })
    await push_update(db)
    await rm_from_active(team.name)





async def invite_team(db, user, client, team_num, intent):
    jwt = await ech.create_jwt(team_num, "", f"room{user.room}", False, 180)
    # await ecsocket.send_by_access({"api": eclib.apis.meeting_ctrl, "operation": "set_code", "room": user.room, "password": password}, eclib.apis.meeting_ctrl)
    team_msg = {"api": eclib.apis.main, "modal":
                "<p>You are invited to join the video call:</p>" +
                "<p><a href=\"https://connect.liveremoteskills.org/room" + str(user.room) + "?jwt=" + jwt + "\" target=\"_blank\" + style='word-break: break-word;'>" +
                "https://connect.liveremoteskills.org/room" + str(user.room) + "?jwt=" + jwt + "</a></p>",
                "room": user.room, "jwt": jwt
                }
    ecusers.User.room_codes[user.room] = "No Password"
    await ecsocket.send_by_user(team_msg, ecusers.User.find_user(team_num))
    await push_update(db)
    team_data_result = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team_num)])
    team_data = team_data_result[0]
    location = team_data['location']
    team_name = team_data['teamName']
    info = {
        "team": team_num,
        "location": location,
        "name": team_name
    }
    passcode = "No Passcode"
    start_record = False
    if user.room in ecusers.User.event_room_data:
        if ecusers.User.event_room_data[user.room]['active'] == False:  # Start new room
            start_record = True
            ecusers.User.event_room_data[user.room] = {"passcode": passcode, "info": info, "active": True, "time": ech.current_time(), "intent": intent}
            msg = {"api": eclib.apis.livestream, "operation": "update", "room": user.room, "data": info}
            await ecsocket.send_by_role(msg, eclib.roles.livestream)
            room_data = ecusers.User.event_room_data
            msg = {"api": eclib.apis.output, "operation": "setAliveRooms", "data": room_data}
            await ecsocket.send_by_role(msg, eclib.roles.output)
            await ecmodules.output.reload_active()
        else: # Re-invite
            ecusers.User.event_room_data[user.room] = {"passcode": passcode, "info": info, "active": True, "time": ecusers.User.event_room_data[user.room]['time'], "intent": intent}
    else: # Start new room
        start_record = True
        ecusers.User.event_room_data[user.room] = {"passcode": passcode, "info": info, "active": True, "time": ech.current_time(), "intent": intent}
        msg = {"api": eclib.apis.livestream, "operation": "update", "room": user.room, "data": info}
        await ecsocket.send_by_role(msg, eclib.roles.livestream)
        room_data = ecusers.User.event_room_data
        msg = {"api": eclib.apis.output, "operation": "setAliveRooms", "data": room_data}
        await ecsocket.send_by_role(msg, eclib.roles.output)
        await ecmodules.output.reload_active()
    if start_record:
        streaming_passcode = ""
        for r in ecusers.User.userlist:
            if r.role == eclib.roles.livestream:
                streaming_passcode = r.passcode
        if streaming_passcode == "":
            await ech.send_error(client, "Tell the EP that the system is having trouble locating a livestream user")
            return
        url = f"https://console.liveremoteskills.org/stream?room={user.room}&token={streaming_passcode}"
        team_info = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team_num)])
        if len(team_info) > 0:
            event = team_info[0]['div']
        else:
            event = "RE-XX-00-0000"
        record_thread = threading.Thread(target=start_room_recording, args=(url, event, team_num, intent, user.room), daemon=True)
        record_thread.start()

async def ctrl_invite(payload, client, user, db):
    """
    Invite team to meeting room.
    Executed by referee.

    :param payload: received payload
    :type payload: dict[str, Any]
    :param client: client that sent request
    :type client: websockets.WebSocketCommonProtocol
    :param user: team in question
    :type user: ecusers.User
    :param db: database object
    :type db: ecdatabase.Database
    :return: whether operation was successful
    :rtype: bool
    """
    if (team_num := await ech.safe_extract(client, payload, {eclib.db.queue.team_num: str})) is not None and user.role == eclib.roles.referee:
        db_result = await db.select(eclib.db.queue.table_, [(eclib.db.queue.referee, "==", user.name), (eclib.db.queue.time_removed, "==", 0)])
        if len(db_result) > 0:
            if db_result[0][eclib.db.queue.team_num] != team_num:
                await ech.send_error(client, "You can only invite one team at a time!")
                return False
        db_result = await db.select(eclib.db.queue.table_, [(eclib.db.queue.team_num, "==", team_num), (eclib.db.queue.time_removed, "==", 0)])
        if (intent := await ech.safe_extract(client, payload, {'intent': str})) is not None:
            pass
        else:
            intent = "Unknown"
        if intent != "General":
            if len(db_result) == 0:
                await ech.send_error(client)
                return False
            if db_result[0][eclib.db.queue.referee] in ("", user.name):
                await db.update(eclib.db.queue.table_, [(eclib.db.queue.team_num, "==", team_num), (eclib.db.queue.time_removed, "==", 0)], {
                    eclib.db.queue.time_invited: ech.current_time(),
                    eclib.db.queue.referee: user.name
                })
                await invite_team(db, user, client, team_num, intent)
                return True
        else:
            await invite_team(db, user, client, team_num, intent)
            return True
    return False


async def ctrl_remove(payload, client, user, db):
    """
    Remove team from queue.
    Executed by referee or event partner.

    :param payload: received payload
    :type payload: dict[str, Any]
    :param client: client that sent request
    :type client: websockets.WebSocketCommonProtocol
    :param user: team in question
    :type user: ecusers.User
    :param db: database object
    :type db: ecdatabase.Database
    """
    if (team_num := await ech.safe_extract(client, payload, {eclib.db.inspection.team_num: str})) is not None:
        db_result = await db.select(eclib.db.queue.table_, [(eclib.db.queue.team_num, "==", team_num), (eclib.db.queue.time_removed, "==", 0)])
        if len(db_result) == 0:
            await ech.send_error(client)
            return
        if user.name == db_result[0][eclib.db.queue.referee] or user.role == eclib.roles.event_partner:
            await db.update(eclib.db.queue.table_, [(eclib.db.queue.team_num, "==", team_num), (eclib.db.queue.time_removed, "==", 0)], {
                eclib.db.queue.removed_by: user.name,
                eclib.db.queue.time_removed: ech.current_time()
            })
            await push_update(db)
            await rm_from_active(team_num)
        else:
            await ech.send_error(client)
