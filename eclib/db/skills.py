"""
Constants for 'skills' table
"""

table_ = "skillsScores"

timestamp = "timestamp"

team_num = "teamNum"

skills_type = "type"
skills_type_driving = 1
skills_type_programming = 2

red_balls = "redBalls"

blue_balls = "blueBalls"

owned_goals = "ownedGoals"

score = "score"

stop_time = "stopTime"

referee = "referee"

create_ = "CREATE TABLE IF NOT EXISTS " + table_ + " ( " \
          + timestamp + " INTEGER NOT NULL, " \
          + team_num + " TEXT NOT NULL, " \
          + skills_type + " INTEGER NOT NULL, " \
          + red_balls + " INTEGER NOT NULL, " \
          + blue_balls + " INTEGER NOT NULL, " \
          + owned_goals + " TEXT NOT NULL, " \
          + score + " INTEGER NOT NULL, " \
          + stop_time + " INTEGER NOT NULL, " \
          + referee + " TEXT NOT NULL " \
          + ");"
