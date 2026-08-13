# datetime is what the rollover check compares period_start against.
from datetime import datetime

# Decimal is the type the money columns come back as. Amounts arriving from
# the request body are floats, so they are converted before any comparison.
from decimal import Decimal

# Session is the type of the database handle every function here receives.
# It is passed in by the controller rather than created here, so that several
# calls can share one session and be committed together as a single unit.
from sqlalchemy.orm import Session

# Import the limit class and the enum of kinds from app/models.
from app.models.transfer_limit import TransferLimit, LimitType


# Turns whatever the caller passed into the exact Decimal the columns hold.
#
# Going through str() rather than Decimal(amount) matters: Decimal(0.1) keeps
# the float's error and produces 0.1000000000000000055..., which would make a
# transfer of exactly the limit look like it was over by a hair.
def to_money(amount):
    return Decimal(str(amount))


# Zeroes a limit's usage when the period it was counting has ended.
#
# This is the whole reason there is no background job. A DAILY limit is not
# reset at midnight by a scheduler, it is reset the first time anybody looks
# at it on a new day, which is exactly as correct and needs nothing running
# in the background.
#
# Returns True when it actually reset something, so callers can tell whether
# the session now has a change waiting to be written.
#
# Note this does NOT commit. The caller decides when, which is what lets the
# transfer endpoint fold a reset into its single commit alongside the balance
# changes.
def reset_if_period_rolled_over(limit: TransferLimit):
    # PER_TRANSACTION never accumulates, so there is no period to roll over
    # and nothing to reset.
    if not limit.accumulates():
        return False

    now = datetime.now()

    if limit.limit_type == LimitType.DAILY.value:
        # Compare calendar dates, not a 24 hour gap. A limit is "per day",
        # so 23:59 and 00:01 are different periods even though they are two
        # minutes apart.
        rolled_over = limit.period_start.date() != now.date()
    else:
        # MONTHLY. The year has to be part of the comparison, otherwise
        # January of next year would look like the same period as January
        # of this one.
        rolled_over = (
            limit.period_start.year,
            limit.period_start.month,
        ) != (now.year, now.month)

    if not rolled_over:
        return False

    # != rather than < on purpose. If the clock ever moves backwards, a
    # period_start in the future would otherwise leave the usage stuck
    # forever, blocking transfers the customer is entitled to make.
    limit.current_period_used = Decimal("0.00")
    limit.period_start = now

    return True


# Creates a limit for a customer and saves it.
#
# Returns None when limit_type is not one of the three kinds, following the
# same pattern as create_account: the service reports that the request was
# invalid, and the controller decides which HTTP status that maps to.
def create_limit(db: Session, user_id: int, limit_type: str, max_amount: float):
    # LimitType(...) would raise on an unknown value. Checking membership
    # first means an unknown kind comes back as a plain None instead of an
    # exception escaping into a 500.
    if limit_type not in [kind.value for kind in LimitType]:
        return None

    new_limit = TransferLimit(user_id, limit_type, max_amount)

    db.add(new_limit)
    db.commit()

    # Pick up the id PostgreSQL generated during the commit.
    db.refresh(new_limit)

    return new_limit


# Returns every limit belonging to one customer.
#
# The rollover check runs here as well as in the checking path, so the
# current_period_used the frontend shows is never a stale figure left over
# from yesterday. Without it a customer could open the page on a new day and
# still see "used $500 of $500" when nothing is actually blocked.
#
# That makes a GET write to the database, which is unusual, but only when a
# period has genuinely ended. The commit is skipped entirely when nothing
# rolled over, so an ordinary read stays a read.
def get_limits(db: Session, user_id: int):
    limits = (
        db.query(TransferLimit)
        .filter(TransferLimit.user_id == user_id)
        .all()
    )

    # any() would stop at the first True and skip the remaining resets, so
    # the results are collected into a list first and checked afterwards.
    resets = [reset_if_period_rolled_over(limit) for limit in limits]

    if any(resets):
        db.commit()

    return limits


# Finds a single limit by its id, without caring who owns it.
#
# The controller needs this to tell "no such limit" apart from "not yours":
# the first is a 404 and the second a 403, and a lookup that filtered by
# owner could only ever report one of them.
#
# Returns None when there is no limit with that id.
def get_limit(db: Session, limit_id: int):
    return (
        db.query(TransferLimit)
        .filter(TransferLimit._limit_id == limit_id)
        .first()
    )


# Changes a limit's max_amount.
#
# Returns None when the limit does not exist OR when it belongs to somebody
# else. The user_id is part of the query rather than checked afterwards, so
# a row belonging to another customer is never loaded in the first place and
# there is no path through this function that can write to one. The
# controller does its own lookup beforehand to choose between 404 and 403,
# but this stays safe on its own even if some future caller forgets to.
def update_limit(db: Session, limit_id: int, user_id: int, max_amount: float):
    limit = (
        db.query(TransferLimit)
        .filter(TransferLimit._limit_id == limit_id)
        .filter(TransferLimit.user_id == user_id)
        .first()
    )

    if limit is None:
        return None

    limit.max_amount = to_money(max_amount)

    # SQLAlchemy notices the object changed and writes the new value out on
    # commit, so there is no separate "save" step to remember.
    db.commit()
    db.refresh(limit)

    return limit


# Checks a proposed transfer against every limit the customer has set.
#
# Returns None when the transfer is allowed, or a sentence explaining the
# refusal when it is not. A returned string rather than a raised exception
# keeps this consistent with the other services, which report what happened
# and leave the status code to the controller, the same way "Insufficient
# funds" is decided in the transfer route today.
#
# A customer with no limits set has nothing to fail, so this returns None.
def check_transfer_against_limits(db: Session, user_id: int, amount: float):
    amount = to_money(amount)

    limits = (
        db.query(TransferLimit)
        .filter(TransferLimit.user_id == user_id)
        .all()
    )

    for limit in limits:
        # Roll the period over BEFORE reading current_period_used, not just
        # before adding to it. Checking first means yesterday's spending can
        # never block a transfer that today's limit allows.
        reset_if_period_rolled_over(limit)

        if limit.limit_type == LimitType.PER_TRANSACTION.value:
            # Nothing accumulates here, the single amount is simply compared
            # against the ceiling.
            if amount > limit.max_amount:
                return (
                    f"Transfer of ${amount:.2f} exceeds your per-transaction "
                    f"limit of ${limit.max_amount:.2f}"
                )
            continue

        # DAILY and MONTHLY. What matters is the total after this transfer,
        # so the amount is added to what has already been spent before the
        # comparison.
        projected_total = limit.current_period_used + amount

        if projected_total > limit.max_amount:
            period = "daily" if limit.limit_type == LimitType.DAILY.value else "monthly"
            return (
                f"Transfer of ${amount:.2f} would exceed your {period} limit "
                f"of ${limit.max_amount:.2f} "
                f"(${limit.current_period_used:.2f} already used)"
            )

    return None


# Adds a completed transfer to the running total on every limit that counts
# one, called after the transfer has been allowed through.
#
# PER_TRANSACTION limits are skipped. They cap one transfer at a time and
# have no notion of a total to add to.
#
# This deliberately does NOT commit, for the same reason record_transfer does
# not: the transfer endpoint changes two balances, writes a history row and
# updates these totals, and all of them have to succeed or fail together.
# Committing here would record the usage even if the balance changes were
# later rolled back, and the customer would lose part of their allowance for
# a transfer that never happened.
def record_usage(db: Session, user_id: int, amount: float):
    amount = to_money(amount)

    limits = (
        db.query(TransferLimit)
        .filter(TransferLimit.user_id == user_id)
        .all()
    )

    for limit in limits:
        if not limit.accumulates():
            continue

        # Checked again here rather than trusting the check that just ran.
        # A request that started at 23:59:59 can reach this line after
        # midnight, and without this the first spending of the new day would
        # be added onto the previous day's total.
        reset_if_period_rolled_over(limit)

        limit.current_period_used = limit.current_period_used + amount