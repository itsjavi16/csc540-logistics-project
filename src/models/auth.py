"""Login: checks credentials and that the account holds the requested role."""

from src.db.helpers import fetch_one

ROLES = ("SHIPPER", "CARRIER", "VIEWER")


def login(user_id_or_name, password, role):
    """Return the logged-in user as a dict, or None for bad credentials / wrong role.

    The login screen asks for a "User ID"; we accept either the numeric
    user_id or the username. Passwords are stored as SHA2(password, 256).

    The returned dict always has user_id, username, display_name, role, and:
      - shipper_id for a SHIPPER (the id Shipment.shipper_id uses)
      - carrier_id and company_name for a CARRIER (the company that owns vehicles)
    """
    if role not in ROLES:
        raise ValueError(f"Unknown role {role}")
    ident = (user_id_or_name or "").strip()
    if not ident or not password:
        return None

    user = fetch_one(
        """SELECT u.user_id, u.username, u.display_name, u.role_type AS role,
                  sh.shipper_id, c.carrier_id, cc.company_name
           FROM User u
           LEFT JOIN Shipper sh        ON sh.user_id = u.user_id
           LEFT JOIN Carrier c         ON c.user_id = u.user_id
           LEFT JOIN CarrierCompany cc ON cc.carrier_id = c.carrier_id
           WHERE (u.username = %s OR u.user_id = %s)
             AND u.password_hash = SHA2(%s, 256)
             AND u.role_type = %s""",
        (ident, int(ident) if ident.isdigit() else -1, password, role),
    )
    return user
