import os
from dataclasses import dataclass
from psycopg2 import DatabaseError
from dotenv import load_dotenv

from api_university.db.tools.utils import (
    PsqlDatabaseConnection,
    try_except_decorator
)
from api_university.db.tools.db_tools import (
    Database,
    DatabaseRole,
    DatabaseUser,
    DatabasePrivilege
)

load_dotenv()


@dataclass()
class DatabaseOperation:
    connection = PsqlDatabaseConnection()
    dbname: str = os.getenv("PG_DB")
    user_name: str = os.getenv("PG_USER")
    user_password: str = os.getenv("PG_USER_PASSWORD")
    role_name: str = os.getenv("PG_ROLE")

    @try_except_decorator(DatabaseError)
    def create_db(self):
        """
        Default: Creates db, role and user with password.
        Gets data from .env.
        """
        with self.connection as db:
            # Create new database:
            new_db = Database(self.dbname, db.connection)
            new_db.create_postgresql_db()

            # Create new user:
            new_user = DatabaseUser(self.user_name, self.user_password, db.connection)
            new_user.create_new_user()

            if self.role_name is not None:
                # Create new role:
                new_role = DatabaseRole(self.role_name, db.connection)
                new_role.create_new_role()
                # Assign privileges on the database to the role:
                new_role_privileges = DatabasePrivilege(new_db.db_name, new_role.role_name, db.connection)
                new_role_privileges.grant_all_privileges()
                # Join user to role:
                new_role.join_user_to_role(new_user.username)
            else:
                # Assign privileges on the database to the user:
                new_user_privileges = DatabasePrivilege(new_db.db_name, new_user.username, db.connection)
                new_user_privileges.grant_all_privileges()

    @try_except_decorator(DatabaseError)
    def delete_db(self):
        """
        WARNING!
        COMPLETE DELETION OF DATABASE TOGETHER WITH USERS AND ROLES!
        """
        with self.connection as db:
            # Init db:
            existing_db = Database(self.dbname, db.connection)

            # Init user:
            existing_user = DatabaseUser(self.user_name, self.user_password, db.connection)

            if self.role_name is not None:
                # Init role
                existing_role = DatabaseRole(self.role_name, db.connection)
                # Init role privilege:
                existing_role_privileges = DatabasePrivilege(existing_db.db_name,
                                                             existing_role.role_name,
                                                             db.connection)
                # Remove all privileges from role:
                existing_role_privileges.remove_all_privileges()
                # Remove user from role:
                existing_role.remove_user_from_role(existing_user.username)
                # Drop the role:
                existing_role.drop_role()
            else:
                # Init user privilege:
                existing_user_privileges = DatabasePrivilege(existing_db.db_name,
                                                             existing_user.username,
                                                             db.connection)
                # Remove all privileges from user:
                existing_user_privileges.remove_all_privileges()

            # Drop the db:
            existing_db.drop_postgresql_db()

            # Drop the user:
            existing_user.drop_user()


if __name__ == '__main__':
    # init database:
    database = DatabaseOperation()

    # db operations:
    database.create_db()
    # database.delete_db()
