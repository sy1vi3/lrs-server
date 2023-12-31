"""
Entry point for running Event Console.
"""
import asyncio
import ecdatabase
import ecusers
import echandler
import ecsocket
import ecmodules.inspection
import ecmodules.skills
import ecmodules.teams
import echelpers as ech

DB_FILE = "eventconsole.db"
WS_PORT = 443

TEAMS_FILE = "files/teams.csv"
VOLUNTEERS_FILE = "files/volunteers.csv"
REGISTRATIONS_FILE = "files/registrations.csv"

CERT_CHAIN = "cert/fullchain.pem"
PRIV_KEY = "cert/privkey.pem"

if __name__ == "__main__":
    db = ecdatabase.Database(DB_FILE)
    echandler.db = db
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ecmodules.teams.load(db))  # Blocking task
    ech.log("Starting server")
    ecsocket.ws_serve(loop, echandler.handler, WS_PORT, CERT_CHAIN, PRIV_KEY)  # Change to ws_serve_nossl to disable TLS
