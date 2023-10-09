"""
Handle Tech Support-related tasks
"""
import ecsocket
import eclib.apis
import ecusers
import eclib.roles
import echelpers as ech


async def handler(client, user, operation, payload, db):
    """
    Handler for accessing *Tech Support* API

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
        users = list(ecusers.User.userlist)
        users.sort(key=lambda r: (0 if r.role == eclib.roles.team else 1, r.name))
        usernames = list()
        for u in users:
            usernames.append(u.name)
        await ecsocket.send_by_client({"api": eclib.apis.tech_support, "users": usernames}, client)

    elif operation == "changePasscode":
        if (extracted := await ech.safe_extract(client, payload, {"user": str, "passcode": str})) is not None:
            ecusers.User.find_user(extracted["user"]).passcode = extracted["passcode"]
            await ech.send_error(client, "Successfully set " + extracted["user"] + "'s passcode to:<br><tt>" + extracted["passcode"] + "</tt>")

    elif operation == "logoutUser":
        if (username := await ech.safe_extract(client, payload, {"user": str})) is not None:
            user = ecusers.User.find_user(username)
            for conn in user.clients:
                await conn.close()
            user.clients.clear()
            await ech.send_error(client, "Successfully logged out user " + username)
