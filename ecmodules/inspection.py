"""
Handle inspection-related tasks
"""
import eclib.db.inspection
import eclib.db.queue
import ecsocket
import eclib.apis
import ecusers
import ecmodules.queue
import echelpers as ech
import eclib.roles


async def push_to_team(team, db, client=None):
    """
    Send most current inspection data to a team.
    If `client` is specified, only sends the data to that client (for `get` requests).

    :param team: team in question
    :type team: ecusers.User
    :param db: database object
    :type db: ecdatabase.Database
    :param client: target client (only for `get` requests)
    :type client: websockets.WebSocketCommonProtocol
    """
    db_result = await db.select(eclib.db.inspection.table_, [(eclib.db.inspection.team_num, "==", team.name)])
    if len(db_result) == 0:
        await ech.send_error(client)
        return
    inspection_status = db_result[0][eclib.db.inspection.result]
    if inspection_status == eclib.db.inspection.result_passed:
        inspection_status = "Passed"
    elif inspection_status == eclib.db.inspection.result_not_started:
        inspection_status = "Not Started"
    else:
        inspection_status = "Partial"
    msg = {"api": eclib.apis.inspection, "operation": "post", "status": inspection_status}
    if client is not None:  # `get` request
        await ecsocket.send_by_client(msg, client)
    else:  # save operation
        await ecsocket.send_by_user(msg, team)


async def push_to_ctrl(db, client=None):
    """
    Send most current inspection data to volunteers.
    If `client` is specified, only sends the data to that client (for `get` requests).

    :param db: database object
    :type db: ecdatabase.Database
    :param client: target client (only for `get` requests)
    :type client: websockets.WebSocketCommonProtocol
    """
    db_result = await db.select(eclib.db.inspection.table_, list())
    status_order = (eclib.db.inspection.result_partial, eclib.db.inspection.result_not_started, eclib.db.inspection.result_passed)
    db_result.sort(key=lambda r: (status_order.index(r[eclib.db.inspection.result]), r[eclib.db.inspection.team_num]))
    inspections = list()
    ech.INSPECTED_TEAMS.clear()
    for row in db_result:
        inspection_status = row[eclib.db.inspection.result]
        if inspection_status == eclib.db.inspection.result_passed:
            inspection_status = "Passed"
            ech.INSPECTED_TEAMS.append(row[eclib.db.inspection.team_num])
        elif inspection_status == eclib.db.inspection.result_not_started:
            inspection_status = "Not Started"
        else:
            inspection_status = "Partial"
        inspections.append({eclib.db.inspection.team_num: row[eclib.db.inspection.team_num], eclib.db.inspection.result: inspection_status})
    msg = {"api": eclib.apis.inspection_ctrl, "operation": "post", "inspections": inspections, "passedTeams": ech.INSPECTED_TEAMS}
    if client is not None:  # `get` request
        await ecsocket.send_by_client(msg, client)
    else:  # save operation
        await ecsocket.send_by_access(msg, eclib.apis.inspection_ctrl)


async def load_inspection_form(payload, client, db):
    """
    Send client inspection form for a specific team

    :param payload: received payload, containing team number
    :type payload: dict[str, Any]
    :param client: client that sent payload and will receive form
    :type client: websockets.WebSocketCommonProtocol
    :param db: database object
    :type db: ecdatabase.Database
    """
    if (team_num := await ech.safe_extract(client, payload, {eclib.db.inspection.team_num: str})) is not None:
        db_result = await db.select(eclib.db.inspection.table_, [(eclib.db.inspection.team_num, "==", team_num)])
        if len(db_result) == 0:
            await ech.send_error(client)
            return
        await ecsocket.send_by_client({"api": eclib.apis.inspection_ctrl, "operation": "editableForm", "data": db_result[0]}, client)


async def team_handler(client, user, operation, _payload, db):
    """
    Handler for teams accessing *Inspection* API

    :param client: client that sent payload
    :type client: websockets.WebSocketCommonProtocol
    :param user: user that sent payload
    :type user: ecusers.User
    :param operation: operation specified in payload
    :type operation: str
    :param _payload: received payload
    :type _payload: dict[str, Any] | None
    :param db: database object
    :type db: ecdatabase.Database
    """
    if operation == "get":
        await push_to_team(user, db, client)

    elif operation == "queue":
        await ecmodules.queue.team_queue(eclib.db.queue.purpose_inspection, client, user, db)

    elif operation == "unqueue":
        await ecmodules.queue.team_unqueue(user, db)


async def ctrl_handler(client, user, operation, payload, db):
    """
    Handler for *Inspection Control* API

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

    elif operation == "save":
        if (row := await ech.safe_extract(client, payload, {eclib.db.inspection.team_num: str, eclib.db.inspection.form_data: str, eclib.db.inspection.result: int})) is not None:
            await db.update(eclib.db.inspection.table_, [(eclib.db.inspection.team_num, "==", row[eclib.db.inspection.team_num])], row)
            await push_to_ctrl(db)
            await push_to_team(ecusers.User.find_user(row[eclib.db.inspection.team_num]), db)
            await ecmodules.stats.send_team_info(db, None)

    elif operation == "getInspect":
        await load_inspection_form(payload, client, db)

    elif operation == "invite":
        if await ecmodules.queue.ctrl_invite(payload, client, user, db):
            await load_inspection_form(payload, client, db)

    elif operation == "remove":
        await ecmodules.queue.ctrl_remove(payload, client, user, db)


async def load_inspected_teams(db):
    """
    Store list of inspected teams in memory

    :param db: database object
    :type db: ecdatabase.Database
    """
    db_result = await db.select(eclib.db.inspection.table_, [(eclib.db.inspection.result, "==", eclib.db.inspection.result_passed)])
    ech.INSPECTED_TEAMS.clear()
    for row in db_result:
        print(row)
        ech.INSPECTED_TEAMS.append(row[eclib.db.inspection.team_num])
    ech.INSPECTED_TEAMS.sort()
