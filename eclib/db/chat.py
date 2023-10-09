"""
Constants for 'chat' table
"""

table_ = "chat"

timestamp = "timestamp"

author = "author"

author_type = "authorType"
author_type_announcement = 0
author_type_team = 1
author_type_referee = 2
author_type_staff = 3

message = "message"

visibility = "visibility"
visibility_visible = 1
visibility_hidden = 0

create_ = "CREATE TABLE IF NOT EXISTS " + table_ + " ( " \
          + timestamp + " INTEGER NOT NULL, " \
          + author + " TEXT NOT NULL, " \
          + author_type + " INTEGER NOT NULL, " \
          + message + " TEXT NOT NULL, " \
          + visibility + " INTEGER DEFAULT 1 " \
          + ");"
