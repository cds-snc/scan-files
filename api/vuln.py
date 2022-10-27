from django.db import connection

def is_admin(username: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                admin
            FROM
                users
            WHERE
                username = '%s'
        """ % username)
        result = cursor.fetchone()

    if result is None:
        # User does not exist
        return False

    admin, = result
    return admin