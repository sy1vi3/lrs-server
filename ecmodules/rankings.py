import eclib.db.skills
import eclib.db.rankings
import eclib.db.teams
import ecsocket
import eclib.apis
import ecusers
import ecmodules.queue
import echelpers as ech
from datetime import datetime
import csv
import files.tokens as tokens
import requests
import json
import time

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

async def post_result(event, csv_rows_to_add, div):
    with open(f'files/{event}.csv', 'w', newline='') as f:
        skills_writer = csv.writer(f)
        skills_writer.writerow(['Rank','Team','TotalScore','ProgHighScore','ProgHighScoreStopTime','ProgHighScoreTime','ProgAttempts','DriverHighScore','DriverHighScoreStopTime','DriverHighScoreTime','DriverAttempts','Age Group'])
        for row in csv_rows_to_add:
            skills_writer.writerow(row)

    with open('files/config.json', 'r') as f:
        config = json.load(f)
        event_code = div
        skills_auth_code = "null"
        for obj in config['events']:
            if obj['event-code'] == div:
                skills_auth_code = obj['auth-code']
    read_headers = {"Authorization": f"Bearer {tokens.re_read_token}"}
    response = requests.get(f'https://www.robotevents.com/api/v2/events?sku[]={event}', headers=read_headers).json()
    id = response['data'][0]['id']

    endpoint = f"https://www.robotevents.com/api/live/events/{id}/skills?skills_auth_code={skills_auth_code}"
    headers = {
        "X-Auth-Token": tokens.re_write_token,
        "Accept": "application/json",
        "Authorization": f"Basic {tokens.re_test_login}"
    }
    files = {'file': open(f'files/{event}.csv', 'rb')}

    r = requests.post(endpoint, headers=headers, files=files)

    # ech.log(f"Updated Scores, Response code {r.status_code}")

async def calc_rankings(db):
    start_time = time.time()
    divs = await get_divs(db)
    div_ranks = {}

    for div in divs:
        csv_rows_to_add = []
        d_skills = {}
        second_d_skills = {}
        third_d_skills = {}
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
                    d_skills[row['teamNum']] = [row['score'], row["stopTime"], row['timestamp']]
                else:
                    if row['score'] > d_skills[row['teamNum']][0] or (row['score'] == d_skills[row['teamNum']][0] and row['stopTime'] > d_skills[row['teamNum']][1]):
                        if row['teamNum'] in second_d_skills.keys():
                            third_d_skills[row['teamNum']] = second_d_skills[row['teamNum']]
                        second_d_skills[row['teamNum']] = d_skills[row['teamNum']]
                        d_skills[row['teamNum']] = [row['score'], row["stopTime"], row['timestamp']]
                    else:
                        if row['teamNum'] not in second_d_skills.keys():
                            second_d_skills[row['teamNum']] = [row['score'], row["stopTime"]]
                        else:
                            if row['score'] > second_d_skills[row['teamNum']][0] or (row['score'] == second_d_skills[row['teamNum']][0] and row['stopTime'] > second_d_skills[row['teamNum']][1]):
                                third_d_skills[row['teamNum']] = second_d_skills[row['teamNum']]
                                second_d_skills[row['teamNum']] = [row['score'], row["stopTime"]]
                            else:
                                if row['teamNum'] not in third_d_skills.keys():
                                    third_d_skills[row['teamNum']] = [row['score'], row["stopTime"]]
                                else:
                                    if row['score'] > third_d_skills[row['teamNum']][0] or (row['score'] == third_d_skills[row['teamNum']][0] and row['stopTime'] > third_d_skills[row['teamNum']][1]):
                                        third_d_skills[row['teamNum']] = [row['score'], row["stopTime"]]

        p_skills = {}
        second_p_skills = {}
        third_p_skills = {}
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
                    p_skills[row['teamNum']] = [row['score'], row["stopTime"], row['timestamp']]
                else:
                    if row['score'] > p_skills[row['teamNum']][0] or (row['score'] == p_skills[row['teamNum']][0] and row['stopTime'] > p_skills[row['teamNum']][1]):
                        if row['teamNum'] in second_p_skills.keys():
                            third_p_skills[row['teamNum']] = second_p_skills[row['teamNum']]
                        second_p_skills[row['teamNum']] = p_skills[row['teamNum']]
                        p_skills[row['teamNum']] = [row['score'], row["stopTime"], row['timestamp']]
                    else:
                        if row['teamNum'] not in second_p_skills.keys():
                            second_p_skills[row['teamNum']] = [row['score'], row["stopTime"]]
                        else:
                            if row['score'] > second_p_skills[row['teamNum']][0] or (row['score'] == second_p_skills[row['teamNum']][0] and row['stopTime'] > second_p_skills[row['teamNum']][1]):
                                third_p_skills[row['teamNum']] = second_p_skills[row['teamNum']]
                                second_p_skills[row['teamNum']] = [row['score'], row["stopTime"]]
                            else:
                                if row['teamNum'] not in third_p_skills.keys():
                                    third_p_skills[row['teamNum']] = [row['score'], row["stopTime"]]
                                else:
                                    if row['score'] > third_p_skills[row['teamNum']][0] or (row['score'] == third_p_skills[row['teamNum']][0] and row['stopTime'] > third_p_skills[row['teamNum']][1]):
                                        third_p_skills[row['teamNum']] = [row['score'], row["stopTime"]]

        combined = {}
        for team in d_skills.keys():
            if team in third_d_skills.keys():
                combined[team] = [[d_skills[team][0], 0, d_skills[team][1], 0], [second_d_skills[team][0], 0, second_d_skills[team][1], 0], [third_d_skills[team][0], 0, third_d_skills[team][1], 0], [d_skills[team][2], 0]]
            elif team in second_d_skills.keys():
                combined[team] = [[d_skills[team][0], 0, d_skills[team][1], 0], [second_d_skills[team][0], 0, second_d_skills[team][1], 0], [0, 0, 0, 0], [d_skills[team][2], 0]]
            else:
                combined[team] = [[d_skills[team][0], 0, d_skills[team][1], 0], [0, 0, 0, 0], [0, 0, 0, 0], [d_skills[team][2], 0]]
        for team in p_skills.keys():
            if team in combined.keys():
                if team in third_p_skills.keys():
                    combined[team][0][0] += p_skills[team][0]
                    combined[team][0][1] = p_skills[team][0]
                    combined[team][0][2] += p_skills[team][1]
                    combined[team][0][3] = p_skills[team][1]

                    combined[team][1][1] = second_p_skills[team][0]
                    combined[team][1][3] = second_p_skills[team][1]

                    combined[team][2][1] = third_p_skills[team][0]
                    combined[team][2][3] = third_p_skills[team][1]

                    combined[team][3][1] = p_skills[team][2]
                elif team in second_p_skills.keys():
                    combined[team][0][0] += p_skills[team][0]
                    combined[team][0][1] = p_skills[team][0]
                    combined[team][0][2] += p_skills[team][1]
                    combined[team][0][3] = p_skills[team][1]

                    combined[team][1][1] = second_p_skills[team][0]
                    combined[team][1][3] = second_p_skills[team][1]

                    combined[team][3][1] = p_skills[team][2]
                else:
                    combined[team][0][0] += p_skills[team][0]
                    combined[team][0][1] = p_skills[team][0]
                    combined[team][0][2] += p_skills[team][1]
                    combined[team][0][3] = p_skills[team][1]
                    combined[team][3][1] = p_skills[team][2]
            else:
                if team in third_d_skills.keys():
                    combined[team] = [[p_skills[team][0], p_skills[team][0], 0, p_skills[team][1]], [0, second_p_skills[team][0], 0, second_p_skills[team][1]], [0, third_p_skills[team][0], 0, third_p_skills[team][1]], [0, p_skills[team][2]]]
                elif team in second_d_skills.keys():
                    combined[team] = [[p_skills[team][0], p_skills[team][0], 0, p_skills[team][1]], [0, second_p_skills[team][0], 0, second_p_skills[team][1]], [0, 0, 0, 0], [0, p_skills[team][2]]]
                else:
                    combined[team] = [[p_skills[team][0], p_skills[team][0], 0, p_skills[team][1]], [0, 0, 0, 0], [0, 0, 0, 0], [0, p_skills[team][2]]]
        ranks_items = list(combined.items())
        rank_items_new = []
        for team in ranks_items:
            #                     0         1              2              3              4              5              6              7              8              9                   10
            #                     name      #combined      #prog          #2nd prog      #2nd driver    #combined time #prog time     #3rd prog      #3rd driver    #driver timestamp   #prog time
            rank_items_new.append([team[0], team[1][0][0], team[1][0][1], team[1][1][1], team[1][1][0], team[1][0][2], team[1][0][3], team[1][2][1], team[1][2][0], team[1][3][0], team[1][3][1]])
        try:
            db_result = await db.select(eclib.db.teams.table_, [("teamNum", "==", rank_items_new[0][0])])
            div_program = db_result[0]['comp']
        except:
            div_program = "VRC"
        if div_program == "VRC":
            orderedRanks = sorted(rank_items_new, key=lambda t: (t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8]), reverse=True)
        elif div_program == "VIQC":
            orderedRanks = sorted(rank_items_new, key=lambda t: (t[1], t[2], t[3], t[4], t[7], t[8]), reverse=True)
        rankingDict = {}
        for num, listing in enumerate(orderedRanks, start=1):
            team = listing[0]
            combined = listing[1]
            prog = listing[2]
            prog_2 = listing[3]
            driver_2 = listing[4]
            stoptime = listing[5]
            prog_stoptime = listing[6]
            prog_3 = listing[7]
            driver_3 = listing[8]
            d_timestamp = listing[9]
            p_timestamp = listing[10]

            driver_attempts_db = await db.select(eclib.db.skills.table_, [(eclib.db.skills.skills_type, "==", 1), (eclib.db.skills.team_num, "==", team)])
            prog_attempts_db = await db.select(eclib.db.skills.table_, [(eclib.db.skills.skills_type, "==", 2), (eclib.db.skills.team_num, "==", team)])

            driver_attempts = (len(driver_attempts_db))
            prog_attempts = (len(prog_attempts_db))

            grade_level_db =  await db.select(eclib.db.teams.table_, [(eclib.db.skills.team_num, "==", team)])
            grade_level = grade_level_db[0]['grade']

            if d_timestamp != 0:
                d_time = str(datetime.utcfromtimestamp(d_timestamp).strftime(f'%Y-%m-%d{"T"}%H:%M:%S{"Z"}'))
            else:
                d_time = ""
            if p_timestamp != 0:
                p_time = str(datetime.utcfromtimestamp(p_timestamp).strftime(f'%Y-%m-%d{"T"}%H:%M:%S{"Z"}'))
            else:
                p_time = ""
            rank = num
            db_result = await db.select(eclib.db.teams.table_, [("teamNum", "==", team)])
            program = db_result[0]['comp']

            # csv_row = f"{rank},{team},{combined},{prog},{prog_stoptime},{p_time},{prog_attempts},{combined-prog},{stoptime-prog_stoptime},{d_time},{driver_attempts},{grade_level}"
            csv_row = [rank,team,combined,prog,prog_stoptime,p_time,prog_attempts,combined-prog,stoptime-prog_stoptime,d_time,driver_attempts,grade_level]
            csv_rows_to_add.append(csv_row)
            row = {
                eclib.db.rankings.team_num: team,
                eclib.db.rankings.prog: prog,
                eclib.db.rankings.driver: combined-prog,
                eclib.db.rankings.second_prog: prog_2,
                eclib.db.rankings.second_driver: driver_2,
                eclib.db.rankings.prog_stop_time: prog_stoptime,
                eclib.db.rankings.third_driver: driver_3,
                eclib.db.rankings.thirdProg: prog_3,
                eclib.db.rankings.score: combined,
                eclib.db.rankings.stop_time: stoptime,
                eclib.db.rankings.rank: num,
                eclib.db.rankings.comp: program,
                eclib.db.rankings.div: div
            }
            await db.upsert(eclib.db.rankings.table_, row, eclib.db.rankings.team_num)

            rankingDict[rank] = {"rank": rank, "team": team, "combined": combined, "prog": prog, "prog_2":prog_2, "driver_2":driver_2, "stoptime": stoptime, "prog_stoptime":prog_stoptime, "prog_3":prog_3, "driver_3":driver_3}
        div_ranks[div] = rankingDict
        if ech.POST_TO_RE:
            await post_result(div, csv_rows_to_add, div)
    msg = {"api": eclib.apis.rankings, "operation": "return_data", "list": div_ranks}
    await ecsocket.send_by_access(msg, eclib.apis.rankings)
    print(time.time()-start_time)


async def send_rankings(db):
    divs = await get_divs(db)
    div_ranks = {}
    for div in divs:
        results = await db.select_order(eclib.db.rankings.table_, [(eclib.db.rankings.div, "==", div)], eclib.db.rankings.rank, "ASC")
        rankingDict = {}
        for team in results:
            team_num = team['teamNum']
            combined = team['score']
            prog = team['prog']
            prog_2 = team['secondProg']
            driver_2 = team['secondDriver']
            stoptime = team['stopTime']
            prog_stoptime = team['progStopTime']
            prog_3 = team['thirdProg']
            driver_3 = team['thirdDriver']
            rank = team['rank']
            program = team['comp']
            rankingDict[rank] = {"rank": rank, "team": team_num, "combined": combined, "prog": prog, "prog_2":prog_2, "driver_2":driver_2, "stoptime": stoptime, "prog_stoptime":prog_stoptime, "prog_3":prog_3, "driver_3":driver_3, "comp":program}
        div_ranks[div] = rankingDict
    msg = {"api": eclib.apis.rankings, "operation": "return_data", "list": div_ranks}
    await ecsocket.send_by_access(msg, eclib.apis.rankings)

async def purge_rankings(db):
    skills_db = await db.select(eclib.db.skills.table_, [])
    teams = []
    for row in skills_db:
        if row['teamNum'] not in teams:
            teams.append(row['teamNum'])
    rank_teams = []
    ranks_db = await db.select(eclib.db.rankings.table_, [])
    for row in ranks_db:
        if row['teamNum'] not in rank_teams:
            rank_teams.append(row['teamNum'])

    for team in rank_teams:
        if team not in teams:
            await db.delete(eclib.db.rankings.table_, [(eclib.db.rankings.team_num, "==", team)])
    await calc_rankings(db)

async def ranks_handler(db, operation):
    if operation == "get_rankings":
        await send_rankings(db)
    elif operation == "calc_rankings":
        await calc_rankings(db)
