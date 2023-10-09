"""
Handle Skills-related tasks
"""
import eclib.db.skills
import eclib.db.teams
import ecsocket
import eclib.apis
import ecusers
import ecmodules.queue
import echelpers as ech


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
    for row in db_result:
        results.append({
            "rowid": row["rowid"],
            eclib.db.skills.timestamp: ech.timestamp_to_readable(row[eclib.db.skills.timestamp]),
            eclib.db.skills.team_num: row[eclib.db.skills.team_num],
            eclib.db.skills.skills_type: "Driving" if row[eclib.db.skills.skills_type] == eclib.db.skills.skills_type_driving else "Programming",
            eclib.db.skills.score: row[eclib.db.skills.score]
        })
    results.reverse()
    msg = {"api": eclib.apis.skills_scores, "operation": "post", "scores": results}
    if client is not None:  # `get` request
        await ecsocket.send_by_client(msg, client)
    else:  # save operation
        await ecsocket.send_by_access(msg, eclib.apis.skills_scores)


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
    if (extracted := await ech.safe_extract(client, payload, {eclib.db.skills.team_num: str, "scoresheet": dict})) is not None:
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
                eclib.db.skills.stop_time: scoresheet[eclib.db.skills.stop_time]
            }
            if (rowid := await ech.safe_extract(client, payload, {"rowid": int}, False)) is not None:  # update existing score
                await db.update(eclib.db.skills.table_, [("rowid", "==", rowid)], row)
            else:  # save new score
                row[eclib.db.skills.timestamp] = ech.current_time()
                row[eclib.db.skills.referee] = user.name
                await db.insert(eclib.db.skills.table_, row)
            await push_to_ctrl(db)
            await push_to_team(ecusers.User.find_user(row[eclib.db.skills.team_num]), db)
            await push_to_scores(db)


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
        if (extracted := await ech.safe_extract(client, payload, {eclib.db.skills.team_num: str, "scoresheet": dict})) is not None:
            msg = {"api": eclib.apis.skills, "operation": "showScore", "scoresheet": extracted["scoresheet"]}
            await ecsocket.send_by_user(msg, ecusers.User.find_user(extracted[eclib.db.skills.team_num]))

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
