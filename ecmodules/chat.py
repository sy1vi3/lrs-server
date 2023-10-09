"""
Handle chat-related tasks
"""
import eclib.db.chat
import ecsocket
import eclib.apis
import echelpers as ech
import eclib.roles
import bleach
from profanity_filter import ProfanityFilter

pf = ProfanityFilter()

async def push(db, new_message=True, client=None):
    """
    Send most current chat data.
    If `client` is specified, only sends the data to that client (for `get` requests).

    :param db: database object
    :type db: ecdatabase.Database
    :param new_message: whether new message was added (to trigger badge)
    :type new_message: bool
    :param client: target client (only for `get` requests)
    :type client: websockets.WebSocketCommonProtocol
    """
    db_result = await db.select(eclib.db.chat.table_, [(eclib.db.chat.visibility, "==", eclib.db.chat.visibility_visible)])
    chat = list()
    for row in db_result:
        author_type = row[eclib.db.chat.author_type]
        author = row[eclib.db.chat.author]
        if author_type == eclib.db.chat.author_type_staff:
            author_type = "staff"
        elif author_type == eclib.db.chat.author_type_referee:
            author_type = "referee"
        elif author_type == eclib.db.chat.author_type_announcement:
            author_type = "announcement"
            author = ""
        elif author_type == "sticker":
            author_type = "sticker"
            author = ""
        elif author_type == "score":
            author_type = "score"
            author = ""
        elif author_type == "system":
            author_type = "system"
            author = ""
        else:
            author_type = "team"
        chat.append({
            "rowid": row["rowid"],
            eclib.db.chat.author_type: author_type,
            eclib.db.chat.author: author,
            eclib.db.chat.message: row[eclib.db.chat.message]
        })
    msg = {"api": eclib.apis.chat, "operation": "post", "chat": chat, "badge": new_message}
    if client is not None:  # `get` request
        await ecsocket.send_by_client(msg, client)
    else:  # save operation
        await ecsocket.send_by_access(msg, eclib.apis.chat)


async def post_message(payload, client, user, db):
    """
    Post a new chat message

    :param payload: received payload, containing team number
    :type payload: dict[str, Any]
    :param client: client that sent payload and will receive form
    :type client: websockets.WebSocketCommonProtocol
    :param user: user that sent payload
    :type user: ecusers.User
    :param db: database object
    :type db: ecdatabase.Database
    """
    if (message := await ech.safe_extract(client, payload, {eclib.db.chat.message: str})) is not None:
        if user.role == eclib.roles.referee:
            author_type = eclib.db.chat.author_type_referee
        elif user.role in eclib.roles.STAFF_ROLES_:
            author_type = eclib.db.chat.author_type_staff
        else:
            if not ech.TEAM_CHAT_ENABLED:
                await ech.send_error(client, "Team chatting is currently disabled.")
                return
            author_type = eclib.db.chat.author_type_team
        message = bleach.clean(message, tags=list(), attributes=dict())
        message = " ".join(message.split())
        message = pf.censor(message)
        if len(message) == 0:
            await ech.send_error(client, "Invalid message")
            return
        if user.chat_banned and user.role == eclib.roles.team:
            await ech.send_error(client, f"User is banned from chat. <br> Reason: {user.chat_ban_reason}")
            return
        await db.insert(eclib.db.chat.table_, {
            eclib.db.chat.timestamp: ech.current_time(),
            eclib.db.chat.author: user.name,
            eclib.db.chat.author_type: author_type,
            eclib.db.chat.message: message
        })
        await push(db)
        msg = {"api": "Sound", "operation": "new_msg", "author": user.name, "new_msg_content": message}
        await ecsocket.send_by_access(msg, eclib.apis.chat)

async def handler(client, user, operation, payload, db):
    """
    Handler for accessing *Chat* API

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
        await push(db, False, client)

    elif operation == "post":
        await post_message(payload, client, user, db)

    elif operation == "delete":
        if (rowid := await ech.safe_extract(client, payload, {"rowid": int})) is not None and user.role in eclib.roles.STAFF_ROLES_:
            await db.update(eclib.db.chat.table_, [("rowid", "==", rowid)], {eclib.db.chat.visibility: eclib.db.chat.visibility_hidden})
            await push(db, False)
