import eclib.db.queue
import eclib.db.teams
import ecsocket
import eclib.apis
import echelpers as ech
import eclib.roles
import ecusers
import string
import random

async def get_current(client=None):
    current = ecusers.User.live_room
    msg = {"api": eclib.apis.output, "operation": "setActiveRoom", "room": current}
    if client==None:
        await ecsocket.send_by_access(msg, eclib.apis.output)
    else:
        await ecsocket.send_by_client(msg, client)

async def reload_active(override=False, roomSet=0):
    if override == False:
        old_active = ecusers.User.live_room
        live_rooms = list()
        live_rooms_with_time = list()
        for r in ecusers.User.event_room_data:
            info = ecusers.User.event_room_data[r]
            if info['active'] == True:
                live_rooms.append(r)
                live_rooms_with_time.append([r, info['time']])
        if old_active not in live_rooms:
            if len(live_rooms) == 0:
                ecusers.User.live_room = 0
                msg = {"api": eclib.apis.output, "operation": "setActiveRoom", "room": 0}
                await ecsocket.send_by_access(msg, eclib.apis.output)
                await ecsocket.send_by_role(msg, eclib.roles.producer)
            else:
                sorted_rooms = sorted(live_rooms_with_time,key=lambda l:l[1], reverse=True)
                new_active_room = sorted_rooms[0][0]
                ecusers.User.live_room = new_active_room
                msg = {"api": eclib.apis.output, "operation": "setActiveRoom", "room": new_active_room}
                await ecsocket.send_by_access(msg, eclib.apis.output)
                await ecsocket.send_by_role(msg, eclib.roles.producer)

    else:
        old_active = ecusers.User.live_room
        if roomSet != old_active:
            ecusers.User.live_room = roomSet
            msg = {"api": eclib.apis.output, "operation": "setActiveRoom", "room": roomSet}
            await ecsocket.send_by_access(msg, eclib.apis.output)
            await ecsocket.send_by_role(msg, eclib.roles.producer)
    room_data = ecusers.User.event_room_data
    msg = {"api": eclib.apis.output, "operation": "setAliveRooms", "data": room_data}
    await ecsocket.send_by_access(msg, eclib.apis.output)
    await ecsocket.send_by_role(msg, eclib.roles.producer)
    await get_current()







async def handler(client, operation, payload):
    if operation == "get_alive":
        room_data = ecusers.User.event_room_data
        msg = {"api": eclib.apis.output, "operation": "setAliveRooms", "data": room_data}
        await ecsocket.send_by_client(msg, client)
        await ecsocket.send_by_role(msg, eclib.roles.producer)
        await get_current(client)


async def ctrl_handler(client, operation, payload):
    if operation == "override_stream":
        new_active = payload['room']
        await reload_active(override=True, roomSet=new_active)
