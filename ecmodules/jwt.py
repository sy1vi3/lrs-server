import eclib.db.queue
import eclib.db.teams
import ecmodules.stats
import ecsocket
import eclib.apis
import echelpers as ech
import eclib.roles
import ecusers
import string
import random





async def handler(client, user, operation, payload):
    if operation == "get_invite_link":
        if (extracted := await ech.safe_extract(client, payload, {"room": str, "expiry": int})) is not None:
            token = await ech.create_jwt("", "", extracted['room'], False, extracted['expiry'])
            link = f"https://connect.liveremoteskills.org/{extracted['room']}?jwt={token}"
            msg = {"api": eclib.apis.jwt, "operation": "return_invite_link", "link": link}
            await ecsocket.send_by_client(msg, client)
    elif operation == "join_room":
        if (room := await ech.safe_extract(client, payload, {"room": str})) is not None:
            if user.role == "Event Partner":
                avatar = "https://console.liveremoteskills.org/img/ep.png"
            else:
                avatar = "https://www.roboticseducation.org//app/uploads/2019/08/NEW-RECF-PMS-534C-e1566180271792.png"
            token = await ech.create_jwt(f"{user.name} - {user.role}", avatar, room, True, 120)
            print(token)
            link = f"https://connect.liveremoteskills.org/{room}?jwt={token}"
            msg = {"api": eclib.apis.jwt, "operation": "return_join_link", "link": link}
            await ecsocket.send_by_client(msg, client)
