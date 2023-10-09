import shutil, os
import time
import datetime
import filecmp
import glob

while True:
    try:
        db = "/home/taran/console/eventconsole.db"
        time_ = time.time()
        existing = []
        for file in glob.glob("/home/taran/console/db_backups/*"):
            file = file[31:-3]
            existing.append(file)
        existing.sort(reverse=True)
        if len(existing) > 0:
            old_file = f"/home/taran/console/db_backups/{existing[0]}.db"
            unchanged = filecmp.cmp(db, old_file)
        else:
            unchanged = False

        if unchanged == False:
            shutil.copyfile(db, f"/home/taran/console/db_backups/{round(time_)}.db")
            print(f"Copied at {round(time_)}")
        time.sleep(600)
    except Exception as e:
        print(e)
