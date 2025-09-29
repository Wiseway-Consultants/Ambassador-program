from django.db import connection
from prospect.models import Prospect


def get_full_downline(user_id):
    query = """
    WITH RECURSIVE downline(level, user_id, prospect_id) AS (
        SELECT 1 AS level, u.id AS user_id, NULL AS prospect_id
        FROM user_user u
        WHERE u.invited_by_user_id = %s

        UNION ALL

        SELECT 1 AS level, NULL AS user_id, p.id AS prospect_id
        FROM prospect_prospect p
        WHERE p.invited_by_user_id = %s

        UNION ALL

        SELECT d.level + 1 AS level,
               COALESCE(u.id, d.user_id) AS user_id,
               COALESCE(p.id, d.prospect_id) AS prospect_id
        FROM downline d
        LEFT JOIN user_user u ON u.invited_by_user_id = d.user_id
        LEFT JOIN prospect_prospect p ON p.invited_by_user_id = d.user_id
        WHERE d.level < 7
    )
    SELECT prospect_id
    FROM downline
    WHERE prospect_id IS NOT NULL;
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [user_id, user_id])
        ids = [row[0] for row in cursor.fetchall()]
    return Prospect.objects.filter(id__in=ids).order_by('invited_by_user_id')
