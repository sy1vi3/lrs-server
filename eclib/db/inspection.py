"""
Constants for 'inspection' table
"""

table_ = "inspection"

team_num = "teamNum"

form_data = "formData"

result = "result"
result_not_started = 0
result_partial = 1
result_passed = 2

create_ = "CREATE TABLE IF NOT EXISTS " + table_ + " ( " \
          + team_num + " TEXT NOT NULL UNIQUE, " \
          + form_data + " TEXT DEFAULT '', " \
          + result + " INTEGER DEFAULT 0 " \
          + ");"
