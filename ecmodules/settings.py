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


async def chat_announce_sticker(db, sender, receiver):
    message = f"{receiver} received a sticker from {sender}"
    await db.insert(eclib.db.chat.table_, {
        eclib.db.chat.timestamp: ech.current_time(),
        eclib.db.chat.author: sender,
        eclib.db.chat.author_type: "sticker",
        eclib.db.chat.message: message
    })
    await ecmodules.chat.push(db)


async def handler(db, operation, payload, client, user):
    if operation == "set_sticker_url":
        if user.sticker_banned == False:
            if (sticker_url := await ech.safe_extract(client, payload, {"sticker_url": str})) is not None:
                sticker_url = bleach.clean(sticker_url, tags=list(), attributes=dict())
                if validators.url(sticker_url):
                    pass
                else:
                    await ech.send_error(client, "Please enter a valid URL")
                    return
                row = {
                    eclib.db.teams.sticker_url: sticker_url
                }
                await db.update(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", user.name)], row)
                msg = {"api": eclib.apis.settings, "operation": "set_my_sticker", "url": sticker_url}
                await ecsocket.send_by_client(msg, client)
        else:
            await ech.send_error(client, f"You are banned from using stickers <br> Reason: {user.sticker_ban_reason}")
    elif operation == "gift_sticker":
        if user.sticker_banned == False:
            if(team_to_gift := await ech.safe_extract(client, payload, {"team": str})) is not None:
                if team_to_gift != user.name:
                    team_info = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team_to_gift)])
                    if len(team_info) > 0:
                        pass
                    else:
                        await ech.send_error(client, "Team does not exist")
                        return
                    existing_stickers = team_info[0]['stickers']
                    if existing_stickers is None:
                        row = {eclib.db.teams.stickers: f"['{user.name}']"}
                        await db.update(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team_to_gift)], row)
                        await chat_announce_sticker(db, user.name, team_to_gift)
                    else:
                        existing_stickers = ast.literal_eval(existing_stickers)
                        if user.name not in existing_stickers:
                            existing_stickers.append(user.name)
                        else:
                            await ech.send_error(client, "You have already gifted a sticker to this team")
                            return
                        new_stickers = str(existing_stickers)
                        row = {eclib.db.teams.stickers: new_stickers}
                        await db.update(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team_to_gift)], row)
                        await chat_announce_sticker(db, user.name, team_to_gift)
                    team_info = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team_to_gift)])
                else:
                    await ech.send_error(client, "You can't gift a sticker to yourself!")
            else:
                await ech.send_error(client, f"You are banned from using stickers. <br> Reason: {user.sticker_ban_reason}")
    elif operation == "congrats":
        if user.sticker_banned == False:
            if(receiver := await ech.safe_extract(client, payload, {"team": str})) is not None:
                receiver = bleach.clean(receiver, tags=list(), attributes=dict())
                data = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", receiver)])
                if len(data) > 0:
                    pass
                else:
                    await ech.send_error(client, f"{receiver} is not a valid team")
                    return
                message = f"{user.name} congratulated {receiver}"
                await db.insert(eclib.db.chat.table_, {
                    eclib.db.chat.timestamp: ech.current_time(),
                    eclib.db.chat.author: user.name,
                    eclib.db.chat.author_type: "system",
                    eclib.db.chat.message: message
                })
                await ecmodules.chat.push(db)
        else:
            await ech.send_error(client, f"You are banned from sending congratulations. <br> Reason: {user.sticker_ban_reason}")
    elif operation == "remove_team_from_profile":
        if (target := await ech.safe_extract(client, payload, {"target": str})) is not None:
            team = user.name
            if target != team:
                team_info = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team)])
                gifted_stickers = team_info[0]['stickers']
                try:
                    gifted_stickers = ast.literal_eval(gifted_stickers)
                except:
                    gifted_stickers = f"['{team}']"
                    print("Error in eval")
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
