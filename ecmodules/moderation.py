import eclib.db.queue
import eclib.db.teams
import ecsocket
import eclib.apis
import echelpers as ech
import eclib.roles
import ecusers
import string
import random
import bleach
import validators
import ast
import ecmodules.chat
from colorhash import ColorHash






async def handler(db, client, user, operation, payload):
    if operation == "sticker_image_remove":
        if (team := await ech.safe_extract(client, payload, {"team": str})) is not None:
            team_info = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team)])
            if len(team_info) > 0:
                pass
            else:
                await ech.send_error(client, f"Uh Oh, {team} doesn't really seem to exist")
                return
            new_url = f"https://ui-avatars.com/api/?name={'+'.join(team)}&background={str(ColorHash(team).hex)[1:]}&color=fff"
            row = {eclib.db.teams.sticker_url: new_url}
            await db.update(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team)], row)
            await ech.send_error(client, f"Set {team} sticker image to: <br> <img src={new_url} width=`75`>")
            msg = {"api": eclib.apis.settings, "operation": "set_my_sticker", "url": new_url}
            await ecsocket.send_by_user(msg, ecusers.User.find_user(team))
    elif operation == "remove_user_stickers":
        if (team := await ech.safe_extract(client, payload, {"team": str})) is not None:
            team_info = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team)])
            if len(team_info) > 0:
                pass
            else:
                await ech.send_error(client, f"Uh Oh, {team} doesn't really seem to exist")
                return
            row = {eclib.db.teams.stickers: f"[]"}
            await db.update(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team)], row)
