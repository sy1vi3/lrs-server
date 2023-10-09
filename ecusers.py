"""
Provides 'User' class:
Data about each user and their permissions.
"""
import eclib.apis
import csv
import eclib.roles
import asyncio
import eclib.db.users
import random
import string
import ecsocket


class User:
    """
    Data about each user and their permissions.
    """
    userlist = set()
    rooms = list()
    room_codes = dict()
    events = list()

    # Allow instances of User to be stored in sets
    def __hash__(self):
        return hash(id(self))

    def __eq__(self, x):
        return x is self

    def __ne__(self, x):
        return x is not self

    def __init__(self, name, passcode, role, event):
        """
        Create user object

        :param name: username
        :type name: str
        :param passcode: access code
        :type passcode: str
        :param role: user role
        :type role: str
        :return: user object
        :rtype: User
        """
        self.name = name
        self.passcode = passcode
        self.role = role
        self.event = event
        self.enable()
        self.clients = list()
        self.userlist.add(self)
        if event not in User.events:
            User.events.append(event)

    def enable(self, enabled=True):
        """
        Enables or disables user

        :param enabled: whether user is enabled
        :type enabled: bool
        """
        self.enabled = enabled
        if enabled:
            try:
                self.apis_rw = eclib.roles.RW_[self.role]
            except KeyError:
                self.apis_rw = tuple()
            try:
                self.apis_ro = eclib.roles.RO_[self.role]
            except KeyError:
                self.apis_ro = tuple()
        else:
            self.apis_rw = tuple()
            self.apis_ro = tuple()

    @classmethod
    async def load_users(cls, db):
        all_users = await db.select(eclib.db.users.table_, [(eclib.db.users.enabled, "==", 1)])
        disabled_users = await db.select(eclib.db.users.table_, [(eclib.db.users.enabled, "==", 0)])

        ep_in_users = False
        livestream_in_users = False
        used_codes = list()

        for u in all_users:
            if u['role'] == eclib.roles.event_partner:
                ep_in_users = True
            if u['role'] == eclib.roles.livestream:
                livestream_in_users = True
            used_codes.append(u['passcode'])
        if ep_in_users == False:
            new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
            while new_code in used_codes:
                new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
            row = {
                eclib.db.users.name: "Event Partner",
                eclib.db.users.passcode: new_code,
                eclib.db.users.role: eclib.roles.event_partner,
                eclib.db.users.enabled: 1,
                eclib.db.users.event: "ALL"
            }
            print(f"NEW USER: EVENT PARTNER: {new_code}")
            await db.insert(eclib.db.users.table_, row)
        if livestream_in_users == False:
            new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
            while new_code in used_codes:
                new_code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(13))
            row = {
                eclib.db.users.name: "Livestream",
                eclib.db.users.passcode: new_code,
                eclib.db.users.role: eclib.roles.livestream,
                eclib.db.users.enabled: 1,
                eclib.db.users.event: "ALL"
            }
            print(f"NEW USER: LIVESTREAM: {new_code}")
            await db.insert(eclib.db.users.table_, row)

        existing_users = list()
        for u in cls.userlist:
            u.enable(False)
            existing_users.append(u.name)
        for user in all_users:
            name = user["name"]
            if name in existing_users:
                u = cls.find_user(name)
                u.role = user["role"]
                u.passcode = user["passcode"]
                u.event = user["event"]
                u.enable()
            else:
                u = User(user["name"], user["passcode"], user["role"], user["event"])
                if u.role == eclib.roles.referee:
                    cls.rooms.append(u)
                    u.room = len(cls.rooms)
                    password = (''.join(random.choice(string.digits) for _ in range(4)))
                    await ecsocket.send_by_access({"api": eclib.apis.meeting_ctrl, "operation": "set_code", "room": u.room, "password": password}, eclib.apis.meeting_ctrl)
                    User.room_codes[u.room] = password
                    rooms = []
                    for u in cls.rooms:
                        rooms.append(u.room)
                    await ecsocket.send_by_access({"api": eclib.apis.meeting_ctrl, "operation": "all_rooms", "rooms": rooms}, eclib.apis.meeting_ctrl)
        print(User.room_codes)

        for user in disabled_users:
            name = user["name"]
            if name in existing_users:
                u = cls.find_user(name)
                u.role = user["role"]
                u.passcode = user["passcode"]
                u.event = user["event"]
                u.enable(False)
            else:
                u = User(user["name"], user["passcode"], user["role"], user["event"])
                u.enable(False)

    def get_apis(self):
        """
        Get all APIs a user is allowed to access

        :return: APIs a user is allowed to access
        :rtype: tuple[str]
        """
        return self.apis_rw + self.apis_ro

    def get_tablist(self):
        """
        Get list of tabs that should be visible to the user (APIs that should be presented as tabs)

        :return: list of tabs
        :rtype: list[str]
        """
        return [api for api in self.get_apis() if api in eclib.apis.tabs_]

    def has_access(self, *apis):
        """
        Check if user is allowed to access API(s).
        Uses OR logic.

        :param apis: API(s) in question
        :type apis: str
        :return: Whether user is allowed to interact with the API
        :rtype: bool
        """
        for api in apis:
            if api in self.get_apis():
                return True
        return False

    def has_perms(self, *apis):
        """
        Check if user is allowed to interact with API(s).
        Uses OR logic.

        :param apis: API(s) in question
        :type apis: str
        :return: Whether user is allowed to interact with the API
        :rtype: bool
        """
        for api in apis:
            if api in self.apis_rw:
                return True
        return False

    @classmethod
    def find_user(cls, username):
        """
        Find user object from username

        :param username: username (or team number)
        :type username: str
        :return: user object
        :rtype: User
        """
        for user in cls.userlist:
            if user.name == username:
                return user
