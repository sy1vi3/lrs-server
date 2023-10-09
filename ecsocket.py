"""
Low-level WebSockets library.
Abstracted further as appropriate in each module.
"""
import websockets
import ssl
import ecusers
import json


def register(client, user):
    """
    Associate a client with a user (on login)

    :param client: client WebSocket connection
    :type client: websockets.WebSocketCommonProtocol
    :param user: corresponding user
    :type user: ecusers.User
    """
    user.clients.append(client)


def unregister(client):
    """
    Dissociate a client from all users (on logout)

    :param client: client WebSocket connection
    :type client: websockets.WebSocketCommonProtocol
    """
    for user in ecusers.User.userlist:
        if client in user.clients:
            user.clients.remove(client)


async def send_by_client(message, *clients):
    """
    Send a payload to specified client(s)

    :param message: payload
    :type message: dict[str, Any]
    :param clients: target client(s)
    :type clients: websockets.WebSocketCommonProtocol
    """
    for client in clients:
        await client.send(json.dumps(message))


async def send_by_user(message, *users):
    """
    Send a payload to specified user(s)

    :param message: payload
    :type message: dict[str, Any]
    :param users: target user(s)
    :type users: ecusers.User
    """
    for u in users:
        await send_by_client(message, *u.clients)


async def send_by_access(message, *apis):
    """
    Send a payload to all users who can access specified API(s)

    :param message: payload
    :type message: dict[str, Any]
    :param apis: API(s) in question
    :type apis: str
    """
    for u in ecusers.User.userlist:
        if not set(apis).isdisjoint(u.get_apis()):
            await send_by_user(message, u)


async def send_by_role(message, *roles):
    """
    Send a payload to all users with specified role(s)

    :param message: payload
    :type message: dict[str, Any]
    :param roles: role(s) in question
    :type roles: str
    """
    for u in ecusers.User.userlist:
        if u.role in roles:
            await send_by_user(message, u)


def ws_serve(event_loop, handler, port, cert_chain, private_key):
    """
    Run the WebSocket server with TLS (wss://)

    :param event_loop: result of asyncio.get_event_loop()
    :type event_loop: asyncio.AbstractEventLoop
    :param handler: function to handle received WebSocket payloads
    :type handler: (websockets.WebSocketCommonProtocol, str) -> Awaitable
    :param port: network port to use
    :type port: int
    :param cert_chain: path to certificate chain file
    :type cert_chain: str
    :param private_key: path to private key file
    :type private_key: str
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_chain, private_key)
    event_loop.run_until_complete(websockets.serve(handler, "", port, ssl=context))
    event_loop.run_forever()


def ws_serve_nossl(event_loop, handler, port, *_):
    """
    Run the WebSocket server without TLS (ws://)

    :param event_loop: result of asyncio.get_event_loop()
    :type event_loop: asyncio.AbstractEventLoop
    :param handler: function to handle received WebSocket payloads
    :type handler: (websockets.WebSocketCommonProtocol, str) -> Awaitable
    :param port: network port to use
    :type port: int
    """
    event_loop.run_until_complete(websockets.serve(handler, "", port))
    event_loop.run_forever()
