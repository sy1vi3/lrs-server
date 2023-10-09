"""
Various helper functions for use throughout Event Console.
"""
import ecsocket
import datetime
import time
import eclib.apis
import eclib.db
from discord_webhook import DiscordWebhook
import files.tokens as tokens
import jwt

TEAM_CHAT_ENABLED = True
INSPECTION_OPEN = True
SKILLS_OPEN = True
POST_TO_RE = False

INSPECTED_TEAMS = list()
SKILLS_ATTEMPTS = dict()

def log(message):
    # webhook = DiscordWebhook(url=tokens.webhook_url, content=f"`{message}`")
    # response = webhook.execute()
    pass
async def create_jwt(name="", avatar="", room="*", moderator=False, expiry = 600):
    jwt_data = {
        "context": {
            "user": {
                "avatar": f"{avatar}",
                "name": f"{name}",
                "email": "",
                "id": "abcd:a1b2c3-d4e5f6-0abc1-23de-abcdef01fedcba"
            }
        },
        "aud": "jitsi",
        "iss": "eventconsole",
        "sub": "https://connect.liveremoteskills.org/",
        "room": f"{room}",
        "exp": round(time.time())+expiry,
        "moderator": moderator
    }
    token = jwt.encode(jwt_data, tokens.jitsi_secret, algorithm='HS256')
    return token


async def send_error(client, error_msg="An error occurred. Please try again."):
    """
    Send an error message to a client

    :param client: target client
    :type client: websockets.WebSocketCommonProtocol
    :param error_msg: error text to display
    :type error_msg: str
    """
    await ecsocket.send_by_client({"api": eclib.apis.main, "modal": error_msg}, client)


async def safe_extract(client, source_dict, keys_and_types, auto_send_error=True):
    """
    Extract key values from JSON-encoded data sent by client.
    Returns error to client if expected key-value pairs are missing. \n
    Recommended syntax: `if (var := await safe_extract(client, source_dict, key=type)) is not None:`

    :param client: client to return error to
    :type client: websockets.WebSocketCommonProtocol
    :param source_dict: dictionary from which to extract values
    :type source_dict: dict[str, Any]
    :param keys_and_types: keys whose values to return, matched to their expected types
    :type keys_and_types: dict[str, type]
    :param auto_send_error: whether to automatically send an error to the client
    :type auto_send_error: bool
    :return: value (if single key) or dictionary of values corresponding to keys
    :rtype: Any | dict[str, Any] | None
    """
    extracted = dict()
    try:
        for key, type_ in keys_and_types.items():
            if isinstance(source_dict[key], type_):
                extracted[key] = source_dict[key]
            else:
                if auto_send_error:
                    await send_error(client)
                return None
        if len(extracted) == 1:
            return list(extracted.values())[0]
        else:
            return extracted
    except KeyError:
        if auto_send_error:
            await send_error(client)
        return None


def timestamp_to_readable(timestamp, gmt_to_local=-7):
    """
    Convert Unix epoch to human-readable time with desired timezone offset from GMT (in hours)

    :param timestamp: Unix epoch, generated by int(time.time())
    :type timestamp: int
    :param gmt_to_local: desired timezone offset from GMT (in hours)
    :type gmt_to_local: int
    :return: human-readable time in desired timezone
    :rtype: str
    """
    return (datetime.datetime.utcfromtimestamp(timestamp) + datetime.timedelta(hours=-5)).strftime('%-I:%M %p')


def current_time():
    """
    Get the Unix epoch corresponding to the current time

    :return: Unix epoch
    :rtype: int
    """
    return int(time.time())
