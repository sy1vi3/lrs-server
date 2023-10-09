"""
Constants for 'inspection' table
"""

table_ = "recordings"

team_num = "team"

type = "type"

timestamp = "timestamp"
url = "url"

create_ = "CREATE TABLE IF NOT EXISTS " + table_ + " ( " \
          + team_num + " TEXT NOT NULL, " \
          + type + " TEXT NOT NULL, " \
          + timestamp + " INTEGER NOT NULL, " \
          + url + " TEXT NOT NULL " \
          + ");"
