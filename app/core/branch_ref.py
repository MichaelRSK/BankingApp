# Branch codes are stored as plain integers, but people refer to a branch as
# "BR001" rather than "1". This module is the single place that translates
# between the two, so the format is defined once instead of being re-derived
# in every controller that happens to return a branch code.
#
# The database is deliberately left alone. branches.branch_code is an integer
# primary key, and customers, accounts and staff all point at it with foreign
# keys, so turning it into text would mean changing four columns and dropping
# and recreating three foreign keys to gain nothing the database cares about.
# The prefix is presentation, so it lives in the presentation layer.


# The pieces of the format, named rather than written inline, so changing the
# house style later is a one-line edit here instead of a search across the app.
BRANCH_REF_PREFIX = "BR"

# How many digits the number is padded to. 3 gives BR001 through BR999.
BRANCH_REF_DIGITS = 3


# Turns a stored branch code into the form people read: 1 becomes "BR001".
#
# Returns None for None rather than the string "BR000", because a customer or
# account with no branch has no reference either, and inventing one would make
# an unassigned record look assigned in the JSON.
#
# Codes past 999 are not truncated. Python's zero-padding is a minimum width,
# so 1000 becomes "BR1000" rather than silently colliding with "BR000". The
# format simply grows a digit, which is what you want from an id.
def format_branch_ref(branch_code):
    if branch_code is None:
        return None

    return f"{BRANCH_REF_PREFIX}{int(branch_code):0{BRANCH_REF_DIGITS}d}"


# Turns whatever a caller sent into the integer the database stores.
#
# Every form is accepted, because the same value arrives from three different
# places and each one types it differently:
#   None      -> None      (the field was left out; it is optional)
#   1         -> 1         (an existing API client sending a plain number)
#   "1"       -> 1         (a form field, which is always text)
#   "BR001"   -> 1         (someone typing the code the way it is displayed)
#   "br001"   -> 1         (same, without holding shift)
#
# Anything else raises ValueError, so a typo is caught here rather than
# reaching the database and failing as a foreign key violation, which would
# surface as a 500. Where that ValueError lands depends on who called:
# raised inside a pydantic validator it becomes FastAPI's usual 422, while
# the path and query parameters catch it themselves and return a 400.
def parse_branch_ref(value):
    if value is None:
        return None

    # Already a number. bool is excluded because it is a subclass of int in
    # Python, and True would otherwise quietly parse as branch 1.
    if isinstance(value, int) and not isinstance(value, bool):
        return value

    if isinstance(value, str):
        cleaned = value.strip()

        if not cleaned:
            return None

        # Accept the prefix in any case, so "BR001", "br001" and "Br001" all
        # work. Only the prefix is removed, never a stray letter elsewhere,
        # so "XR001" still fails rather than being read as 1.
        if cleaned.upper().startswith(BRANCH_REF_PREFIX):
            cleaned = cleaned[len(BRANCH_REF_PREFIX):]

        # Leading zeros are fine here: int("001") is 1. This is also what
        # rejects an empty remainder, so a bare "BR" does not become 0.
        if cleaned.isdigit():
            return int(cleaned)

    raise ValueError(
        f"branch_code must be a number or a code like "
        f"{BRANCH_REF_PREFIX}001, got {value!r}"
    )
