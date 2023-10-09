"""
Constants for 'teams' table
"""

table_ = "teams"

team_num = "teamNum"

team_name = "teamName"

organization = "organization"

location = "location"

div = "div"

comp = "comp"

grade = "grade"

create_ = "CREATE TABLE IF NOT EXISTS " + table_ + " ( " \
          + team_num + " TEXT NOT NULL UNIQUE, " \
          + team_name + " TEXT, " \
          + organization + " TEXT, " \
          + location + " TEXT, " \
          + div + " TEXT NOT NULL, " \
          + comp + " TEXT NOT NULL, " \
          + grade + " TEXT NOT NULL " \
          + ");"
