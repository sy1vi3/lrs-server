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
import bleach
import validators
import ast
import ecmodules.chat
from colorhash import ColorHash


async def chat_ban(user, payload, client, db):
    if (target := await ech.safe_extract(client, payload, {"target": str})) is not None:
        team_to_ban = ecusers.User.find_user(target)
        if (reason := await ech.safe_extract(client, payload, {"reason": str})) is None:
            reason = "No reason given"
        team_to_ban.chat_banned = True
        team_to_ban.chat_ban_reason = reason
        await ecmodules.stats.send_team_info(db)

async def chat_unban(user, payload, client, db):
    if (target := await ech.safe_extract(client, payload, {"target": str})) is not None:
        team_to_save = ecusers.User.find_user(target)
        team_to_save.chat_banned = False
        team_to_save.chat_ban_reason = ""
        await ecmodules.stats.send_team_info(db)

async def sticker_ban(user, payload, client, db):
    if (target := await ech.safe_extract(client, payload, {"target": str})) is not None:
        team_to_ban = ecusers.User.find_user(target)
        if (reason := await ech.safe_extract(client, payload, {"reason": str})) is None:
            reason = "No reason given"
        team_to_ban.sticker_banned = True
        team_to_ban.sticker_ban_reason = reason
        await ecmodules.stats.send_team_info(db)

async def sticker_unban(user, payload, client, db):
    if (target := await ech.safe_extract(client, payload, {"target": str})) is not None:
        team_to_save = ecusers.User.find_user(target)
        team_to_save.sticker_banned = False
        team_to_save.sticker_ban_reason = ""
        await ecmodules.stats.send_team_info(db)


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
    elif operation == "chat_ban_user":
        await chat_ban(user, payload, client, db)
    elif operation == "chat_unban_user":
        await chat_unban(user, payload, client, db)
    elif operation == "sticker_ban_user":
        await sticker_ban(user, payload, client, db)
    elif operation == "sticker_unban_user":
        await sticker_unban(user, payload, client, db)
    elif operation == "sticker_remove_specific":
        if (team := await ech.safe_extract(client, payload, {"team": str})) is not None and (target := await ech.safe_extract(client, payload, {"target": str})) is not None:
            if target != team:
                team_info = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team)])
                gifted_stickers = team_info[0]['stickers']
                try:
                    gifted_stickers = ast.literal_eval(gifted_stickers)
                except:
                    gifted_stickers = f"['{team}']"
                if target in gifted_stickers:
                    gifted_stickers.remove(target)
                    gifted_stickers = str(gifted_stickers)
                    row = {eclib.db.teams.stickers: gifted_stickers}
                    await db.update(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team)], row)
                    await ecmodules.stats.get_info_card(db, client, team)
                else:
                    await ech.send_error(client, "Error: target team not in user stickers")
            else:
                await ech.send_error(client, "Error: cannot remove a user's own sticker")
