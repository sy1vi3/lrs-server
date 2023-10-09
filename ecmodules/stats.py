import eclib.db.skills
import eclib.db.rankings
import eclib.db.teams
import eclib.db.inspection
import ecsocket
import eclib.apis
import ecusers
import ecmodules.queue
import echelpers as ech
import bleach
import ast



async def send_team_info(db, client):
    teams_data = {}
    teams_result = await db.select(eclib.db.teams.table_, [])
    for row in teams_result:
        teamnum = row['teamNum']
        div = row['div']
        program = row['comp']
        inspection_result = await db.select(eclib.db.inspection.table_, [(eclib.db.inspection.team_num, "==", teamnum)])
        if (team_inspection_data := inspection_result[0]) is not None:
            inspection_code = team_inspection_data['result']
            if inspection_code == 0:
                inspection = "Not Started"
            elif inspection_code == 1:
                inspection = "Partial"
            elif inspection_code == 2:
                inspection = "Passed"
            else:
                inspection = "Unknown"
        else:
            inspection = "Unknown"
        d_attempts = ech.SKILLS_ATTEMPTS[teamnum][0]
        p_attempts = ech.SKILLS_ATTEMPTS[teamnum][1]
        team_info = {"div": div, "program": program, "inspection": inspection, "driver": d_attempts, "prog": p_attempts}
        teams_data[teamnum] = team_info
    msg = {"api": eclib.apis.stats, "operation": "post", "data": teams_data}
    if client is not None:
        await ecsocket.send_by_client(msg, client)
    else:
        await ecsocket.send_by_access(msg, eclib.apis.stats)

async def get_info_card(db, client, team):
    team_info = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team)])
    print(team_info)
    team_name = team_info[0]['teamName']
    team_org = team_info[0]['organization']
    team_loc = team_info[0]['location']
    team_grade = team_info[0]['grade']
    driver_runs = ech.SKILLS_ATTEMPTS[team][0]
    prog_runs = ech.SKILLS_ATTEMPTS[team][1]
    team_sticker = team_info[0]['mysticker']
    gifted_stickers = team_info[0]['stickers']

    all_stickers = list()
    if team_sticker is not None:
        all_stickers.append(team_sticker)
    if gifted_stickers is not None:
        gifted_stickers = ast.literal_eval(gifted_stickers)
        for team_number in gifted_stickers:
            their_team_data = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team_number)])
            their_sticker = their_team_data[0]['mysticker']
            all_stickers.append(their_sticker)

    team_data = {
        "num": team,
        "name": team_name,
        "org": team_org,
        "loc": team_loc,
        "grade": team_grade,
        "driver": driver_runs,
        "prog": prog_runs,
        "stickers": all_stickers
    }

    msg = {"api": eclib.apis.stats, "operation": "info_card", "data": team_data}
    await ecsocket.send_by_client(msg, client)

async def handler(db, client, operation, payload):
    if operation == "get":
        await send_team_info(db, client)
    elif operation == "get_info_card":
        if (teamToGet := await ech.safe_extract(client, payload, {"team": str})) is not None:
            teamToGet = bleach.clean(teamToGet, tags=list(), attributes=dict())
            await get_info_card(db, client, teamToGet)
