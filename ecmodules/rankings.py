import eclib.db.skills
import eclib.db.teams
import ecsocket
import eclib.apis
import ecusers
import ecmodules.queue
import echelpers as ech

async def get_divs(db):
    divs = []
    teams = await db.select(eclib.db.teams.table_, [])
    for row in teams:
        if row['div'] not in divs:
            divs.append(row['div'])
    divslist = {}
    for num, div in enumerate(divs, start=1):
        divslist[num] = div
    msg = {"api": eclib.apis.rankings, "operation": "div_fill", "list": divslist}
    await ecsocket.send_by_access(msg, eclib.apis.rankings)
    return divs
async def get_rankings(db):
    divs = await get_divs(db)
    div_ranks = {}
    for div in divs:
        d_skills = {}
        skills_db_driver = await db.select(eclib.db.skills.table_, [(eclib.db.skills.skills_type, "==", 1)])
        for row in skills_db_driver:
            team = row['teamNum']
            team_data = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team)])
            in_div = False
            for team_row in team_data:
                if team_row['div'] == div:
                    in_div = True
            if in_div == True:
                if row['teamNum'] not in d_skills.keys():
                    d_skills[row['teamNum']] = [row['score'], row["stopTime"]]
                else:
                    if row['score'] > d_skills[row['teamNum']][0]:
                        d_skills[row['teamNum']] = [row['score'], row["stopTime"]]
        p_skills = {}
        skills_db_prog = await db.select(eclib.db.skills.table_, [(eclib.db.skills.skills_type, "==", 2)])
        for row in skills_db_prog:
            team = row['teamNum']
            team_data = await db.select(eclib.db.teams.table_, [(eclib.db.teams.team_num, "==", team)])
            in_div = False
            for team_row in team_data:
                if team_row['div'] == div:
                    in_div = True
            if in_div == True:
                if row['teamNum'] not in p_skills.keys():
                    p_skills[row['teamNum']] = [row['score'], row["stopTime"]]
                else:
                    if row['score'] > p_skills[row['teamNum']][0]:
                        p_skills[row['teamNum']] = [row['score'], row["stopTime"]]

        combined = {}
        for team in d_skills.keys():
            combined[team] = [d_skills[team][0], 0, d_skills[team][1]]
        for team in p_skills.keys():
            if team in combined.keys():
                combined[team][0] += p_skills[team][0]
                combined[team][1] = p_skills[team][0]
                combined[team][2] += p_skills[team][1]
            else:
                combined[team] = [p_skills[team][0], p_skills[team][0], p_skills[team][1]]
        ranks_items = list(combined.items())
        rank_items_new = []
        for team in ranks_items:
            rank_items_new.append([team[0], team[1][0], team[1][1], team[1][2]])
        orderedRanks = sorted(rank_items_new, key=lambda t: (t[1], t[2], t[3]), reverse=True)
        rankingDict = {}
        for num, listing in enumerate(orderedRanks, start=1):
            team = listing[0]
            combined = listing[1]
            prog = listing[2]
            stoptime = listing[3]
            rank = num
            rankingDict[rank] = {"rank": rank, "team": team, "combined": combined, "prog": prog, "stoptime": stoptime}
        div_ranks[div] = rankingDict
    print(div_ranks)
    msg = {"api": eclib.apis.rankings, "operation": "return_data", "list": div_ranks}
    await ecsocket.send_by_access(msg, eclib.apis.rankings)

async def ranks_handler(db, operation):
    await get_rankings(db)
