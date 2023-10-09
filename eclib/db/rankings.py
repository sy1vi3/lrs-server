"""
Constants for 'rankings' table
"""

table_ = "rankings"

team_num = "teamNum"

score = "score"

prog = "prog"

driver = "driver"

second_prog = "secondProg"

second_driver = "secondDriver"

stop_time = "stopTime"

prog_stop_time = "progStopTime"

third_driver = "thirdDriver"

thirdProg = "thirdProg"

comp = "comp"

div = "div"

rank = "rank"

create_ = "CREATE TABLE IF NOT EXISTS " + table_ + " ( " \
          + team_num + " TEXT NOT NULL UNIQUE, " \
          + prog + " INTEGER NOT NULL, " \
          + driver + " INTEGER NOT NULL, " \
          + second_prog + " INTEGER NOT NULL, " \
          + second_driver + " INTEGER NOT NULL, " \
          + prog_stop_time + " INTEGER NOT NULL, " \
          + third_driver + " INTEGER NOT NULL, " \
          + thirdProg + " INTEGER NOT NULL, " \
          + score + " INTEGER NOT NULL, " \
          + stop_time + " INTEGER NOT NULL, " \
          + rank + " INTEGER NOT NULL, " \
          + comp + " TEXT NOT NULL, " \
          + div + " TEXT NOT NULL " \
          + ");"
