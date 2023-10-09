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

create_ = "CREATE TABLE IF NOT EXISTS " + table_ + " ( " \
          + team_num + " TEXT NOT NULL UNIQUE, " \
          + team_name + " TEXT NOT NULL, " \
          + organization + " TEXT NOT NULL, " \
          + location + " TEXT NOT NULL, " \
          + div + " TEXT NOT NULL, " \
          + comp + " TEXT NOT NULL " \
          + ");"
