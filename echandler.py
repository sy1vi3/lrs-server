"""
Handle messages received over WebSocket connections
"""
import json
import websockets
import ecusers
import ecsocket
import eclib.apis
import echelpers as ech
import ecmodules.chat
import ecmodules.event_control
import ecmodules.inspection
import ecmodules.queue
import ecmodules.skills
import ecmodules.tech_support
import ecmodules.rankings
import ecmodules.stats
import ecmodules.oauth
import ecmodules.volunteers
import ecmodules.event_config
import ecmodules.output
import ecmodules.home
import ecmodules.moderation
import ecmodules.settings
import ecmodules.jwt
import jwt
import files.tokens as tokens
import time
import threading
from datetime import date

db = None


def find_user_from_client(client):
    """
    Find user associated with a client

    :param client: client
    :type client: websockets.WebSocketCommonProtocol
    :return: corresponding user
    :rtype: ecusers.User
    """
    for user in ecusers.User.userlist:
        if client in user.clients:
            return user


async def echandle(client, user, api, operation, payload):
    """
    Perform relevant operation based on API specified in received payload.
    For logged-in users only.

    :param client: client that sent payload
    :type client: websockets.WebSocketCommonProtocol
    :param user: user that sent payload
    :type user: ecusers.User
    :param api: API specified in payload
    :type api: str
    :param operation: operation specified in payload
    :type operation: str
    :param payload: received payload, or `None` for automatically triggered 'get' requests
    :type payload: dict[str, Any] | None
    """
    global db
    if (user.has_access(api) and operation.startswith("get")) or (user.has_perms(api) and payload is not None):
        if payload is not None:
            # print(user.name + ": " + str(payload))
            pass
        if api == eclib.apis.chat:
            await ecmodules.chat.handler(client, user, operation, payload, db)
        elif api == eclib.apis.inspection:
            await ecmodules.inspection.team_handler(client, user, operation, payload, db)
        elif api == eclib.apis.inspection_ctrl:
            await ecmodules.inspection.ctrl_handler(client, user, operation, payload, db)
        elif api == eclib.apis.skills:
            await ecmodules.skills.team_handler(client, user, operation, payload, db)
        elif api == eclib.apis.rankings:
            await ecmodules.rankings.ranks_handler(db, operation)
        elif api == eclib.apis.skills_ctrl:
            await ecmodules.skills.ctrl_handler(client, user, operation, payload, db)
        elif api == eclib.apis.skills_scores:
            await ecmodules.skills.scores_handler(client, user, operation, payload, db)
        elif api == eclib.apis.tech_support:
            await ecmodules.tech_support.handler(client, user, operation, payload, db)
        elif api == eclib.apis.event_ctrl:
            await ecmodules.event_control.handler(client, user, operation, payload, db)
        elif api == eclib.apis.stats:
            await ecmodules.stats.handler(db, client, operation, payload)
        elif api == eclib.apis.volunteers:
            await ecmodules.volunteers.handler(db, operation, payload, user)
        elif api == eclib.apis.oauth:
            print(api)
        elif api == eclib.apis.team_control:
            await ecmodules.teams.handler(db, operation, payload)
        elif api == eclib.apis.queue and operation == "get":
            await ecmodules.queue.push_update(db, client, user)
        elif api == eclib.apis.settings:
            await ecmodules.settings.handler(db, operation, payload, client, user)
        elif api == eclib.apis.event_room:
            if user.role == eclib.roles.referee:
                jwt_data = {
                    "context": {
                        "user": {
                            "avatar": "https://console.liveremoteskills.org/img/avatar/referee.png",
                            "name": f"{user.name} - Ref",
                            "email": "",
                            "id": "abcd:a1b2c3-d4e5f6-0abc1-23de-abcdef01fedcba"
                        }
                    },
                    "aud": "jitsi",
                    "iss": "eventconsole",
                    "sub": "https://connect.liveremoteskills.org/",
                    "room": f"room{user.room}",
                    "exp": round(time.time())+36000,
                    "moderator": True
                }
                token = jwt.encode(jwt_data, tokens.jitsi_secret, algorithm='HS256')
                msg = {"api": eclib.apis.event_room, "operation": "give_ref_login", "room": user.room, "pass": ecusers.User.room_codes[user.room], "jwt": token}
                await ecsocket.send_by_client(msg, client)
        elif api == eclib.apis.meeting_ctrl:
            if operation == "init":
                jwt_data = {
                    "context": {
                        "user": {
                            "avatar": "https://console.liveremoteskills.org/img/ep.png",
                            "name": f"{user.name} - Event Partner",
                            "email": "",
                            "id": "abcd:a1b2c3-d4e5f6-0abc1-23de-abcdef01fedcba"
                        }
                    },
                    "aud": "jitsi",
                    "iss": "eventconsole",
                    "sub": "https://connect.liveremoteskills.org/",
                    "room": "*",
                    "exp": round(time.time())+36000,
                    "moderator": True
                }
                token = jwt.encode(jwt_data, tokens.jitsi_secret, algorithm='HS256')
                await ecsocket.send_by_client({"api": eclib.apis.meeting_ctrl, "operation": "set_code", "rooms": len(ecusers.User.rooms), "jwt": token}, client)
        elif api == eclib.apis.event_config:
            await ecmodules.event_config.handler(db, user, client, operation, payload)
        elif api == eclib.apis.output:
            await ecmodules.output.handler(client, operation, payload)
        elif api == eclib.apis.livestream:
            if operation == "get_ranks":
                await ecmodules.rankings.send_rankings(db)
        elif api == eclib.apis.production:
            await ecmodules.output.ctrl_handler(client, operation, payload)
        elif api == eclib.apis.home:
            await ecmodules.home.handler(client, operation, payload)
        elif api == eclib.apis.jwt:
            if operation == "get_jwt_from_livestream":
                room = payload['room']
                jwt_data = {
                    "context": {
                        "user": {
                            "avatar": "https://console.liveremoteskills.org/img/avatar/livestream.png",
                            "name": f"Livestream",
                            "email": "",
                            "id": "abcd:a1b2c3-d4e5f6-0abc1-23de-abcdef01fedcba"
                        }
                    },
                    "aud": "jitsi",
                    "iss": "eventconsole",
                    "sub": "https://connect.liveremoteskills.org/",
                    "room": room,
                    "exp": round(time.time())+36000,
                    "moderator": False
                }
                token = jwt.encode(jwt_data, tokens.jitsi_secret, algorithm='HS256')
                msg = {"api": eclib.apis.jwt, "operation": "return_jwt", "jwt": token}
                await ecsocket.send_by_client(msg, client)
            else:
                await ecmodules.jwt.handler(client, user, operation, payload)
        elif api == eclib.apis.moderation:
            await ecmodules.moderation.handler(db, client, user, operation, payload)
        else:
            await ech.send_error(client, "mayonase on an ecolater im going up so cya later")
    elif api == eclib.apis.main and operation == "get":
        tablist = user.get_tablist()
        await ecsocket.send_by_client({"api": eclib.apis.main, "name": user.name, "role": user.role, "tablist": tablist}, client)
        for api in user.get_apis():
            await echandle(client, user, api, "get", None)
        await ecmodules.queue.push_update(db, client, user)
    else:
        print(api, operation, payload)
        await ech.send_error(client, "RECF didn't like that... Maybe try <code>sudo [command]</code> instead?")

async def log_to_file(client, message):
    if (user := find_user_from_client(client)) is not None:
        name = user.name
    else:
        name = "NOT LOGGED IN"
    to_store = f"\n{date.today()}  |  {ech.timestamp_to_readable(ech.current_time())}  |  {client.remote_address[0]}  |  {name}"
    length = len(to_store)
    space_needed = 65-length
    to_store += " " * space_needed
    to_store += f"|  {message}"
    with open("log/log.txt", "a") as f:
        f.write(to_store)


async def handler(client, _path):
    """
    Immediate function called when WebSocket payload received

    :param client: client that sent payload
    :type client: websockets.WebSocketCommonProtocol
    :type _path: str
    """
    global db
    try:
        async for message in client:

            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                await ech.send_error(client)
                return
            await log_to_file(client, message)
            if (extracted := await ech.safe_extract(client, payload, {"api": str, "operation": str})) is not None:
                if extracted["api"] == eclib.apis.login and extracted["operation"] == "login":
                    if (passcode := await ech.safe_extract(client, payload, {"accessCode": str})) is not None:
                        success = False
                        for user in ecusers.User.userlist:
                            if passcode == user.passcode and user.enabled:
                                success = True
                                ech.log("[LOGIN] " + user.name)
                                ecsocket.unregister(client)
                                ecsocket.register(client, user)
                                await echandle(client, user, eclib.apis.main, "get", None)
                                new_teams = await db.select(eclib.db.teams.table_, [])
                                msg = {"api": "Event Data", "operation": "event_info", "event": user.event, "teams": new_teams}
                                await ecsocket.send_by_client(msg, client)
                                await ecmodules.home.handler(client, "get", payload)
                                if user.role == eclib.roles.event_partner:
                                    await ecmodules.volunteers.get_volunteers(db)
                                    await ecmodules.teams.get_teams(db)
                                    room_data = ecusers.User.rooms
                                    rooms = []
                                    for u in room_data:
                                        rooms.append(u.room)

                                    msg = {"api": eclib.apis.event_ctrl, "operation": "room_code_update", "rooms": ecusers.User.room_codes}
                                    await ecsocket.send_by_role(msg, eclib.roles.event_partner)

                                    await ecsocket.send_by_access({"api": eclib.apis.meeting_ctrl, "operation": "all_rooms", "rooms": rooms}, eclib.apis.meeting_ctrl)
                                    msg = {"api": eclib.apis.event_ctrl, "operation": "set_re_button", "linked": ech.POST_TO_RE}
                                    await ecsocket.send_by_client(msg, client)
                                if user.role == eclib.roles.referee:
                                    jwt_data = {
                                        "context": {
                                            "user": {
                                                "avatar": "https://console.liveremoteskills.org/img/avatar/referee.png",
                                                "name": f"{user.name} - Ref",
                                                "email": "",
                                                "id": "abcd:a1b2c3-d4e5f6-0abc1-23de-abcdef01fedcba"
                                            }
                                        },
                                        "aud": "jitsi",
                                        "iss": "eventconsole",
                                        "sub": "https://connect.liveremoteskills.org/",
                                        "room": f"room{user.room}",
                                        "exp": round(time.time())+36000,
                                        "moderator": True
                                    }
                                    token = jwt.encode(jwt_data, tokens.jitsi_secret, algorithm='HS256')
                                    msg = {"api": eclib.apis.event_room, "operation": "give_ref_login", "room": user.room, "pass": ecusers.User.room_codes[user.room], "jwt": token}
                                    await ecsocket.send_by_client(msg, client)
                                if user.role == eclib.roles.livestream:
                                    if (roomnum := await ech.safe_extract(client, payload, {"room_num": str})) is not None:
                                        try:
                                            room_info = ecusers.User.event_room_data[int(roomnum)]
                                        except:
                                            room_info = {"passcode": ecusers.User.room_codes[int(roomnum)], "info": {"team": "", "location": "", "name": ""}}
                                        msg = {"api": eclib.apis.livestream, "operation": "code", "info": room_info}
                                        await ecsocket.send_by_client(msg, client)
                                if user.role == eclib.roles.output:
                                    streaming_passcode = ""
                                    for r in ecusers.User.userlist:
                                        if r.role == eclib.roles.livestream:
                                            streaming_passcode = r.passcode
                                    msg = {"api": eclib.apis.output, "operation": "setStreamCode", "auth": streaming_passcode}
                                    await ecsocket.send_by_client(msg, client)
                                    await ecmodules.output.reload_active()
                                if user.role == eclib.roles.livestream:
                                    await ecmodules.rankings.send_rankings(db)
                                if user.has_perms(eclib.apis.production):
                                    await ecmodules.output.handler(client, "get_alive", payload)
                                    output_passcode = ""
                                    for r in ecusers.User.userlist:
                                        if r.role == eclib.roles.output:
                                            output_passcode = r.passcode
                                    msg = {"api": eclib.apis.output, "operation": "setOutputCode", "auth": output_passcode}
                                    await ecsocket.send_by_client(msg, client)
                                if user.role == eclib.roles.team:
                                    team_row = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", user.name)])
                                    sticker_url = team_row[0]['mysticker']
                                    msg = {"api": eclib.apis.settings, "operation": "set_my_sticker", "url": sticker_url}
                                    await ecsocket.send_by_client(msg, client)
                                break
                        if not success:
                            await ecsocket.send_by_client({"api": eclib.apis.login, "failure": True}, client)
                elif extracted["api"] == eclib.apis.oauth:
                    await ecmodules.oauth.handler(payload, extracted['operation'], client, db)
                else:
                    if (user := find_user_from_client(client)) is not None:
                        await echandle(client, user, extracted["api"], extracted["operation"], payload)
                    else:
                        await ech.send_error(client, "Something real wack is up with either the server or you")
                        return
            else:
                await ech.send_error(client, "Our servers are humbled by your incredible response")
    except websockets.ConnectionClosed:
        pass
    finally:
        ecsocket.unregister(client)
