"""
Constants for 'queue' table
"""

table_ = "queue"

team_num = "teamNum"

purpose = "purpose"
purpose_inspection = 0
purpose_driving_skills = 1
purpose_programming_skills = 2

time_queued = "timeQueued"

referee = "referee"

time_invited = "timeInvited"

removed_by = "removedBy"

time_removed = "timeRemoved"

create_ = "CREATE TABLE IF NOT EXISTS " + table_ + " ( " \
          + team_num + " TEXT NOT NULL, " \
          + purpose + " INTEGER NOT NULL, " \
          + time_queued + " INTEGER NOT NULL, " \
          + referee + " TEXT DEFAULT '', " \
          + time_invited + " INTEGER DEFAULT 0, " \
          + removed_by + " TEXT DEFAULT '', " \
          + time_removed + " INTEGER DEFAULT 0 " \
          + ");"
