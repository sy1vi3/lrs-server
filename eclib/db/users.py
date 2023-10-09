"""
Constants for 'users' table
"""

table_ = "users"

name = "name"

role = "role"

passcode = "passcode"

enabled = "enabled"

event = "event"


create_ = "CREATE TABLE IF NOT EXISTS " + table_ + " ( " \
          + name + " TEXT NOT NULL UNIQUE, " \
          + role + " TEXT NOT NULL, " \
          + passcode + " TEXT NOT NULL UNIQUE, " \
          + enabled + " INTEGER NOT NULL, " \
          + event + " TEXT NOT NULL " \
          + ");"
