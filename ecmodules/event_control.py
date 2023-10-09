"""
Handle Event Control-related tasks
"""
import echelpers as ech
import ecmodules.chat
import ecsocket
import eclib.db.chat
import eclib.apis
import eclib.roles
import ecmodules.teams


async def handler(client, user, operation, payload, db):
    """
    Handler for accessing *Event Control* API

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
    if operation == "setToggle":
        if (extracted := await ech.safe_extract(client, payload, {"flag": str, "setting": bool})) is not None:
            if extracted["flag"] == "teamChat":
                ech.TEAM_CHAT_ENABLED = extracted["setting"]
            elif extracted["flag"] == "inspection":
                ech.INSPECTION_OPEN = extracted["setting"]
            elif extracted["flag"] == "skills":
                ech.SKILLS_OPEN = extracted["setting"]
            await ech.send_error(client, "Successfully " + ("enabled " if extracted["setting"] else "disabled ") + extracted["flag"])

    elif operation == "announce":
        if (message := await ech.safe_extract(client, payload, {"message": str})) is not None:
            await ecsocket.send_by_role({"api": eclib.apis.main, "modal": message}, eclib.roles.team)
            await db.insert(eclib.db.chat.table_, {
                eclib.db.chat.timestamp: ech.current_time(),
                eclib.db.chat.author: user.name,
                eclib.db.chat.author_type: eclib.db.chat.author_type_announcement,
                eclib.db.chat.message: message
            })
            await ecmodules.chat.push(db)
    elif operation == "refresh_teams":
        print("UPDATING TEAMS")
        await ecmodules.teams.load(db)
