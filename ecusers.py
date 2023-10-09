"""
Provides 'User' class:
Data about each user and their permissions.
"""
import eclib.apis
import csv
import eclib.roles


class User:
    """
    Data about each user and their permissions.
    """
    userlist = set()
    rooms = list()

    # Allow instances of User to be stored in sets
    def __hash__(self):
        return hash(id(self))

    def __eq__(self, x):
        return x is self

    def __ne__(self, x):
        return x is not self

    def __init__(self, name, passcode, role):
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
        self.__enable()
        self.clients = list()
        self.userlist.add(self)

    def __enable(self, enabled=True):
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
    def load_users(cls, db):
        with open('files/volunteers.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile, quoting=csv.QUOTE_ALL)
            for row in reader:
                await db.insert(eclib.db.users.table_, row)
                print(row)
        all_users = await db.select(eclib.db.users.table_, [])


    @classmethod
    def load_volunteers(cls, file):
        """
        Load volunteer user accounts from CSV file

        :param file: path to CSV file
        :type file: str
        """
        existing_volunteers = list()
        for u in cls.userlist:
            if u.role != eclib.roles.team:
                u.__enable(False)
                existing_volunteers.append(u.name)
        with open(file, newline='') as csvfile:
            reader = csv.DictReader(csvfile, quoting=csv.QUOTE_ALL)
            for row in reader:
                name = row["Name"]
                if name in existing_volunteers:
                    u = cls.find_user(name)
                    u.role = row["Role"]
                    u.passcode = row["Passcode"]
                    u.__enable()
                else:
                    u = User(row["Name"], row["Passcode"], row["Role"])
                    if u.role == eclib.roles.referee:
                        cls.rooms.append(u)
                        u.room = len(cls.rooms)

    @classmethod
    def load_teams(cls, file):
        """
        Load team user accounts from CSV file

        :param file: path to CSV file
        :type file: str
        """
        existing_teams = list()
        for u in cls.userlist:
            if u.role == eclib.roles.team:
                u.__enable(False)
                existing_teams.append(u.name)
        with open(file, newline='') as csvfile:
            reader = csv.DictReader(csvfile, quoting=csv.QUOTE_ALL)
            for row in reader:
                name = row["Team Number"]
                if name in existing_teams:
                    cls.find_user(name).__enable()
                else:
                    _ = User(name, row["Passcode"], eclib.roles.team)

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
