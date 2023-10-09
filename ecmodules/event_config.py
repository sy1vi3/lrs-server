import json
import ecsocket
import eclib.apis
import ecusers
import ecmodules.queue
import echelpers as ech
import eclib.roles
import files.tokens as tokens
import requests

with open('files/config.json', 'r') as f:
    config = json.load(f)


async def find_user_from_client(client):
    """
    Find user associated with a client

    :param client: client
    :type client: websockets.WebSocketCommonProtocol
    :return: corresponding user
    :rtype: ecusers.User
    """
    for user in ecusers.User.userlist:
        if client in user.clients:
            return user

async def save_config_to_file(config):
    with open('files/config.json', 'w') as f:
        json.dump(config, f)

async def push_config(client):
    global config
    with open('files/config.json', 'r') as f:
        config = json.load(f)
    events = config['events']
    # Test  code valid here
    msg = {"api": eclib.apis.event_config, "operation": "push_config", "config": events}
    user = await find_user_from_client(client)
    if user.role == eclib.roles.event_partner:
        await ecsocket.send_by_client(msg, client)


async def edit_config(db, user, client, payload):
    global config
    sku = payload['sku']
    auth_code = payload['auth']
    for event in config['events']:
        if event['event-code'] == sku:
            event['auth-code'] = auth_code
    await save_config_to_file(config)
    await push_config(client)


async def delete_config(db, user, client, payload):
    global config
    sku = payload['sku']
    for event in config['events']:
        if event['event-code'] == sku:
            config['events'].remove(event)
    await save_config_to_file(config)
    await push_config(client)

async def add_config(db, user, client, payload):
    global config
    sku = payload['sku']
    headers = {
        'Accept': 'application/json',
        "Authorization": f"Basic {tokens.re_test_login}",
        "X-Auth-Token": tokens.re_write_token,
        'Content-Type': 'application/json'
    }
    response = requests.get(f'https://www.robotevents.com/api/v2/events?sku[]={sku}', headers=headers).json()
    r_data = response['data']
    if len(r_data) >= 1:
        auth_code = payload['auth']
        config['events'].append({"event-code": sku, "auth-code": auth_code})
        await save_config_to_file(config)
        await push_config(client)
    else:
        await ech.send_error(client, "Invalid Event Code")



async def handler(db, user, client, operation, payload):
    if operation == "get":
        await push_config(client)
    elif operation == "edit":
        await edit_config(db, user, client, payload)
    elif operation == "delete":
        await delete_config(db, user, client, payload)
    elif operation == "add":
        await add_config(db, user, client, payload)
