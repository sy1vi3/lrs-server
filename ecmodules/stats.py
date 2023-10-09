import eclib.db.skills
import eclib.db.rankings
import eclib.db.teams
import eclib.db.inspection
import ecsocket
import eclib.apis
import ecusers
import ecmodules.queue
import echelpers as ech



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
