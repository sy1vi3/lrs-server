import eclib.db.queue
import eclib.db.teams
import ecsocket
import eclib.apis
import echelpers as ech
import eclib.roles
import ecusers
import string
import random












async def handler(client, operation, payload):
    if operation == "post":
        with open('files/home.html', 'w') as f:
            f.write(payload['content'])
        msg = {"api": eclib.apis.home, "operation": "push_home", "content": payload['content']}
        await ecsocket.send_by_access(msg, eclib.apis.home)
    if operation == "get":
        with open('files/home.html', 'r') as f:
            content = f.read()
        msg = {"api": eclib.apis.home, "operation": "push_home", "content": content}
        await ecsocket.send_by_client(msg, client)
