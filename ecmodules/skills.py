"""
Handle Skills-related tasks
"""
import echandler
import eclib.db.rankings
import eclib.db.skills
import eclib.db.teams
import ecsocket
import eclib.apis
import ecusers
import ecmodules.queue
import ecmodules.rankings
import echelpers as ech
import ecmodules.chat
import time


async def push_to_team(team, db, client=None):
    """
    Send most current Skills data to a team.
    If `client` is specified, only sends the data to that client (for `get` requests).

    :param team: team in question
    :type team: ecusers.User
    :param db: database object
    :type db: ecdatabase.Database
    :param client: target client (only for `get` requests)
    :type client: websockets.WebSocketCommonProtocol
    """
    driving = ech.SKILLS_ATTEMPTS[team.name][eclib.db.skills.skills_type_driving - 1]
    programming = ech.SKILLS_ATTEMPTS[team.name][eclib.db.skills.skills_type_programming - 1]
    msg = {"api": eclib.apis.skills, "operation": "post", "drivingAttempts": driving, "programmingAttempts": programming}
    if client is not None:  # `get` request
        await ecsocket.send_by_client(msg, client)
    else:  # save operation
        await ecsocket.send_by_user(msg, team)


async def push_to_ctrl(db, client=None):
    """
    Send most current Skills data to volunteers.
    If `client` is specified, only sends the data to that client (for `get` requests).

    :param db: database object
    :type db: ecdatabase.Database
    :param client: target client (only for `get` requests)
    :type client: websockets.WebSocketCommonProtocol
    """
    db_result = await db.select(eclib.db.skills.table_, [])
    scorelist = list()
    for team_num in ech.SKILLS_ATTEMPTS:
        ech.SKILLS_ATTEMPTS[team_num] = [0, 0]
    for row in db_result:
        ech.SKILLS_ATTEMPTS[row[eclib.db.skills.team_num]][row[eclib.db.skills.skills_type] - 1] += 1
        skills_type = "Driving" if row[eclib.db.skills.skills_type] == eclib.db.skills.skills_type_driving else "Programming"
        scorelist.append({
            "rowid": row["rowid"],
            eclib.db.skills.timestamp: ech.timestamp_to_readable(row[eclib.db.skills.timestamp]),
            eclib.db.skills.team_num: row[eclib.db.skills.team_num],
            eclib.db.skills.skills_type: skills_type,
            eclib.db.skills.score: row[eclib.db.skills.score]
        })
    scorelist.reverse()
    msg = {"api": eclib.apis.skills_ctrl, "operation": "post", "scores": scorelist, "attempts": ech.SKILLS_ATTEMPTS}
    if client is not None:  # `get` request
        await ecsocket.send_by_client(msg, client)
    else:  # save operation
        await ecsocket.send_by_access(msg, eclib.apis.skills_ctrl)


async def push_to_scores(db, client=None):
    """
    Send most current Skills score history.
    If `client` is specified, only sends the data to that client (for `get` requests).

    :param db: database object
    :type db: ecdatabase.Database
    :param client: target client (only for `get` requests)
    :type client: websockets.WebSocketCommonProtocol
    """
    db_result = await db.select(eclib.db.skills.table_, [])

    results = list()
    team_results = list()
    used_times = set()
    for row in db_result:
        team_num = row[eclib.db.skills.team_num]
        timestamp = row[eclib.db.skills.timestamp]
        type = "Driving" if row[eclib.db.skills.skills_type] == eclib.db.skills.skills_type_driving else "Programming"
        skills_type = type + " Skills"
        recordings = await db.select(eclib.db.recordings.table_, [(eclib.db.recordings.team_num, "==", team_num), (eclib.db.recordings.type, "==", skills_type)])
        if len(recordings) > 0:
            # print(recordings)
            files = list()
            for r in recordings:
                if r[eclib.db.recordings.timestamp] not in used_times:
                    files.append([r[eclib.db.recordings.timestamp], r[eclib.db.recordings.url]])
            if len(files) > 0:
                est_time = timestamp - 250
                files.sort(key=lambda a: abs(a[0]-est_time))
                file_name = files[0][1]
                used_times.add(files[0][0])
            else:
                file_name = "null"
        else:
            file_name = "null"
        results.append({
            "rowid": row["rowid"],
            eclib.db.skills.timestamp: ech.timestamp_to_readable(timestamp),
            eclib.db.skills.team_num: team_num,
            eclib.db.skills.skills_type: type,
            eclib.db.skills.score: row[eclib.db.skills.score],
            "filename": file_name
        })
        team_results.append({
            "rowid": row["rowid"],
            eclib.db.skills.timestamp: ech.timestamp_to_readable(timestamp),
            eclib.db.skills.team_num: team_num,
            eclib.db.skills.skills_type: type,
            eclib.db.skills.score: row[eclib.db.skills.score],
            "filename": "null"
        })

    results.reverse()
    team_results.reverse()
    msg = {"api": eclib.apis.skills_scores, "operation": "post", "scores": results}
    team_msg = {"api": eclib.apis.skills_scores, "operation": "post", "scores": team_results}
    if client is not None:  # `get` request
        u = echandler.find_user_from_client(client)
        if u.has_access(eclib.apis.production):
            await ecsocket.send_by_client(msg, client)
        else:
            await ecsocket.send_by_client(team_msg, client)
    else:  # save operation
        await ecsocket.send_by_access(msg, eclib.apis.production)
        await ecsocket.send_by_non_access(team_msg, eclib.apis.production)


async def save(payload, client, user, db):
    """
    Save operation

    :param payload: received payload
    :type payload: dict[str, Any] | None
    :param client: client that sent payload
    :type client: websockets.WebSocketCommonProtocol
    :param user that sent payload
    :type user: ecusers.User
    :param db: database object
    :type db: ecdatabase.Database
    """

    if (extracted := await ech.safe_extract(client, payload, {eclib.db.skills.team_num: str, "scoresheet": dict, "comp": str})) is not None:
        team_user = ecusers.User.find_user(extracted[eclib.db.skills.team_num])
        if team_user.event == user.event or user.event == "ALL":
            if extracted["comp"] == "viqc":
                type_of_run = ""
                total_score = ""
                team_that_ran = ""
                if (scoresheet := await ech.safe_extract(client, extracted["scoresheet"], {
                    eclib.db.skills.skills_type: int,
                    eclib.db.skills.red_balls: int,
                    eclib.db.skills.blue_balls: int,
                    eclib.db.skills.owned_goals: int,
                    eclib.db.skills.score: int,
                    eclib.db.skills.stop_time: int
                })) is not None:
                    row = {
                        eclib.db.skills.team_num: extracted[eclib.db.skills.team_num],
                        eclib.db.skills.skills_type: scoresheet[eclib.db.skills.skills_type],
                        eclib.db.skills.red_balls: scoresheet[eclib.db.skills.red_balls],
                        eclib.db.skills.blue_balls: scoresheet[eclib.db.skills.blue_balls],
                        eclib.db.skills.owned_goals: scoresheet[eclib.db.skills.owned_goals],
                        eclib.db.skills.score: scoresheet[eclib.db.skills.score],
                        eclib.db.skills.stop_time: scoresheet[eclib.db.skills.stop_time],
                        eclib.db.skills.comp: extracted["comp"]
                    }
                    if (rowid := await ech.safe_extract(client, payload, {"rowid": int}, False)) is not None:  # update existing score
                        await db.update(eclib.db.skills.table_, [("rowid", "==", rowid)], row)
                    else:  # save new score
                        row[eclib.db.skills.timestamp] = ech.current_time()
                        row[eclib.db.skills.referee] = user.name
                        await db.insert(eclib.db.skills.table_, row)
                    type_of_run = scoresheet[eclib.db.skills.skills_type]
                    total_score = scoresheet[eclib.db.skills.score]
                    team_that_ran = extracted[eclib.db.skills.team_num]

                    await push_to_ctrl(db)
                    await push_to_team(ecusers.User.find_user(row[eclib.db.skills.team_num]), db)
                    await push_to_scores(db)
            else:
                if (scoresheet := await ech.safe_extract(client, extracted["scoresheet"], {
                    eclib.db.skills.skills_type: int,
                    eclib.db.skills.red_balls: int,
                    eclib.db.skills.blue_balls: int,
                    eclib.db.skills.owned_goals: str,
                    eclib.db.skills.score: int,
                    eclib.db.skills.stop_time: int
                })) is not None:
                    row = {
                        eclib.db.skills.team_num: extracted[eclib.db.skills.team_num],
                        eclib.db.skills.skills_type: scoresheet[eclib.db.skills.skills_type],
                        eclib.db.skills.red_balls: scoresheet[eclib.db.skills.red_balls],
                        eclib.db.skills.blue_balls: scoresheet[eclib.db.skills.blue_balls],
                        eclib.db.skills.owned_goals: scoresheet[eclib.db.skills.owned_goals],
                        eclib.db.skills.score: scoresheet[eclib.db.skills.score],
                        eclib.db.skills.stop_time: scoresheet[eclib.db.skills.stop_time],
                        eclib.db.skills.comp: extracted["comp"]
                    }
                    if (rowid := await ech.safe_extract(client, payload, {"rowid": int}, False)) is not None:  # update existing score
                        await db.update(eclib.db.skills.table_, [("rowid", "==", rowid)], row)
                    else:  # save new score
                        row[eclib.db.skills.timestamp] = ech.current_time()
                        row[eclib.db.skills.referee] = user.name
                        await db.insert(eclib.db.skills.table_, row)
                    type_of_run = scoresheet[eclib.db.skills.skills_type]
                    total_score = scoresheet[eclib.db.skills.score]
                    team_that_ran = extracted[eclib.db.skills.team_num]
                    await push_to_ctrl(db)
                    await push_to_team(ecusers.User.find_user(row[eclib.db.skills.team_num]), db)
                    await push_to_scores(db)
            if int(type_of_run) == 1:
                type_of_run = "driver"
                chat_type = "driverscore"
            elif int(type_of_run) == 2:
                type_of_run = "programming"
                chat_type = "progscore"
            else:
                type_of_run = "[HAHA TARAN'S CODE BROKE]"
            message = f"{team_that_ran} scored {total_score} points"
            await db.insert(eclib.db.chat.table_, {
                eclib.db.chat.timestamp: ech.current_time(),
                eclib.db.chat.author: user.name,
                eclib.db.chat.author_type: chat_type,
                eclib.db.chat.message: message
            })
            await ecmodules.chat.push(db)
            await ecmodules.rankings.ranks_handler(db, "calc_rankings")
            await ecmodules.stats.send_team_info(db, None)


async def get_scoresheet(payload, client, user, db, force_view=False):
    """
    Get scoresheet operation

    :param payload: received payload
    :type payload: dict[str, Any] | None
    :param client: client that sent payload
    :type client: websockets.WebSocketCommonProtocol
    :param user that sent payload
    :type user: ecusers.User
    :param db: database object
    :type db: ecdatabase.Database
    :param force_view: forces scoresheet to open in view mode
    :type force_view: bool
    """
    if (rowid := await ech.safe_extract(client, payload, {"rowid": int})) is not None:
        db_result = await db.select(eclib.db.skills.table_, [("rowid", "==", rowid)])
        if len(db_result) == 0:
            await ech.send_error(client)
            return
        if not force_view and user.has_perms(eclib.apis.skills_ctrl):
            msg = {"api": eclib.apis.skills_ctrl, "operation": "editableScore", "data": db_result[0]}
        else:
            db_result[0].pop(eclib.db.skills.referee)
            msg = {"api": eclib.apis.skills, "operation": "showScore", "scoresheet": db_result[0]}
        await ecsocket.send_by_client(msg, client)


async def team_handler(client, user, operation, payload, db):
    """
    Handler for teams accessing *Skills* API

    :param client: client that sent payload
    :type client: websockets.WebSocketCommonProtocol
    :param user: user that sent payload
    :type user: ecusers.User
    :param operation: operation specified in payload
    :type operation: str
    :param payload: received payload
    :type payload: dict[str, Any] | None
    :param db: database object
    :type db: ecdatabase.Database
    """
    if operation == "get":
        await push_to_team(user, db, client)

    elif operation == "queueDriving":
        await ecmodules.queue.team_queue(eclib.db.queue.purpose_driving_skills, client, user, db)

    elif operation == "queueProgramming":
        await ecmodules.queue.team_queue(eclib.db.queue.purpose_programming_skills, client, user, db)

    elif operation == "unqueue":
        await ecmodules.queue.team_unqueue(user, db)


async def findTeamComp(db, payload, client):
    if (team_num := await ech.safe_extract(client, payload, {"teamNum": str})) is not None:
        db_result = await db.select(eclib.db.teams.table_, [("teamNum", "==", team_num)])
        if len(db_result) > 0:
            program = db_result[0]['comp']
            msg = {"api": eclib.apis.skills_ctrl, "operation": "setType", "teamNum": team_num, "comp": program}
            await ecsocket.send_by_client(msg, client)

async def ctrl_handler(client, user, operation, payload, db):
    """
    Handler for *Skills Control* API

    :param client: client that sent payload
    :type client: websockets.WebSocketCommonProtocol
    :param user: user that sent payload
    :type user: ecusers.User
    :param operation: operation specified in payload
    :type operation: str
    :param payload: received payload
    :type payload: dict[str, Any] | None
    :param db: database object
    :type db: ecdatabase.Database
    """
    if operation == "get":
        await push_to_ctrl(db, client)

    elif operation == "invite":
        await ecmodules.queue.ctrl_invite(payload, client, user, db)

    elif operation == "showTeam":
        if (extracted := await ech.safe_extract(client, payload, {eclib.db.skills.team_num: str, "scoresheet": dict, "room": int})) is not None:
            msg = {"api": eclib.apis.skills, "operation": "showScore", "scoresheet": extracted["scoresheet"]}
            stream_msg = {"api": eclib.apis.livestream, "operation": "showScore", "scoresheet": extracted["scoresheet"], "room": extracted["room"]}
            await ecsocket.send_by_user(msg, ecusers.User.find_user(extracted[eclib.db.skills.team_num]))
            await ecsocket.send_by_role(stream_msg, eclib.roles.livestream)

    elif operation == "save":
        await save(payload, client, user, db)

    elif operation == "remove":
        await ecmodules.queue.ctrl_remove(payload, client, user, db)

    elif operation == "getScoresheet":
        await get_scoresheet(payload, client, user, db)

    elif operation == "deleteScore":
        if (rowid := await ech.safe_extract(client, payload, {"rowid": int})) is not None:
            db_result = await db.select(eclib.db.skills.table_, [("rowid", "==", rowid)])
            if len(db_result) == 0:
                await ech.send_error(client)
                return
            team_num = db_result[0][eclib.db.skills.team_num]
            await db.delete(eclib.db.skills.table_, [("rowid", "==", rowid)])
            await push_to_ctrl(db)
            await push_to_team(ecusers.User.find_user(team_num), db)
            await push_to_scores(db)
            await ecmodules.rankings.ranks_handler(db, "calc_rankings")
            await ecmodules.rankings.purge_rankings(db)
            await ecmodules.stats.send_team_info(db, None)
    elif operation == "get_comp":
        await findTeamComp(db, payload, client)


async def scores_handler(client, user, operation, payload, db):
    """
    Handler for accessing *Skills Scores* API

    :param client: client that sent payload
    :type client: websockets.WebSocketCommonProtocol
    :param user: user that sent payload
    :type user: ecusers.User
    :param operation: operation specified in payload
    :type operation: str
    :param payload: received payload
    :type payload: dict[str, Any] | None
    :param db: database object
    :type db: ecdatabase.Database
    """
    if operation == "get":
        await push_to_scores(db, client)

    elif operation == "getScoresheet":
        await get_scoresheet(payload, client, user, db, True)


async def load_attempts(db):
    """
    Store counts of Skills attempts in memory

    :param db: database object
    :type db: ecdatabase.Database
    """
    db_result = await db.select(eclib.db.teams.table_, [])
    ech.SKILLS_ATTEMPTS.clear()
    for row in db_result:
        ech.SKILLS_ATTEMPTS[row[eclib.db.teams.team_num]] = [0, 0]
    db_result = await db.select(eclib.db.skills.table_, [])
    for row in db_result:
        ech.SKILLS_ATTEMPTS[row[eclib.db.skills.team_num]][row[eclib.db.skills.skills_type] - 1] += 1
