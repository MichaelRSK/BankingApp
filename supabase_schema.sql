-- ===========================================================================
-- BankingApp - full schema for Supabase (hosted PostgreSQL)
-- ===========================================================================
--
-- HOW THIS FILE WAS PRODUCED
--   Generated from the live local database (PostgreSQL 18.4, db "bankingapp")
--   with:
--       pg_dump --schema-only --no-owner --no-privileges
--   then cross-checked column by column against the SQLAlchemy models in
--   app/models/ and cleaned up for Supabase.
--
--   Verified before dumping:
--       alembic current  ->  ae9e35893c3e (head)
--       alembic heads    ->  ae9e35893c3e (head)
--   The two matched, so the dump reflects a complete, migrated schema.
--
--   Migrations included, in order:
--       426f100f79f6  initial schema
--       528f100fabcd  widened users.password to 255
--       95dd0676a507  added transfer_limits
--       ae9e35893c3e  widened users.email to 255 and users.username to 120
--
--   Every mismatch found between the dump and the models is listed at the
--   bottom of this file under "MODEL / DATABASE MISMATCHES". None of them are
--   silently resolved here: this script reproduces what the DATABASE actually
--   has, because that is what the running app is using today.
--
-- WHAT WAS REMOVED FROM THE RAW DUMP
--   - \restrict / \unrestrict wrappers (psql-only, and they break the
--     Supabase SQL Editor, which is not psql)
--   - SET statement_timeout / lock_timeout / transaction_timeout / xmloption
--     / client_min_messages / row_security  (local session tuning; Supabase
--     manages its own, and row_security = off is refused on a hosted project)
--   - SELECT pg_catalog.set_config('search_path', '', false)  (would force
--     every unqualified name to fail; everything below is schema-qualified
--     anyway)
--   - SET default_tablespace / default_table_access_method (local storage
--     details that do not apply on Supabase)
--   - Ownership and privilege statements were already excluded by the
--     --no-owner --no-privileges flags. Nothing here reassigns an owner, so
--     the objects end up owned by whichever role runs the script.
--   - No extensions are created. The local database uses only plpgsql, which
--     every Supabase project already has.
--
-- HOW IT WAS VERIFIED (all locally - nothing was run against Supabase)
--   This script was executed against a throwaway local database and compared
--   back against the real one. The comparison was exact: 35 columns, 17
--   constraints, 11 indexes and 6 sequences all identical. It was then run a
--   second time to confirm the guards hold, which produced only "already
--   exists, skipping" notices and no duplicate alembic row.
--
--   The alembic stamp was checked too: pointing alembic at the scratch
--   database reported ae9e35893c3e (head), and "alembic upgrade head"
--   replayed nothing, which is the behaviour you want on Supabase.
--
--   A separate scratch database was also built with "alembic upgrade head"
--   from empty and matched, so this file and the migration path agree.
--   Every scratch database was dropped afterwards.
--
-- SAFE TO RE-RUN
--   Every object is guarded, so running this against a partially-set-up
--   database will not error. Tables use CREATE TABLE IF NOT EXISTS, and the
--   foreign keys sit in guarded DO blocks at the bottom, because PostgreSQL
--   has no ALTER TABLE ... ADD CONSTRAINT IF NOT EXISTS.
--
--   Note the one thing a guard cannot do: if a table already exists with the
--   WRONG shape, IF NOT EXISTS skips it silently rather than fixing it. On a
--   brand new Supabase project that is not a concern.
--
-- ORDER
--   Tables are declared parent-first so the foreign keys resolve cleanly:
--       branches -> customers -> staff -> accounts -> transactions
--                -> transfer_limits,  with users standing alone.
-- ===========================================================================


-- ---------------------------------------------------------------------------
-- SEQUENCES
-- ---------------------------------------------------------------------------
-- account_number_seq is the one hand-written sequence in the schema. It is
-- declared by app/models/account.py and is NOT tied to a column the way a
-- SERIAL sequence is, so it has to be created explicitly and BEFORE the
-- accounts table, whose DEFAULT calls nextval() on it.
--
-- Starting at 1000 reproduces the customer-facing account numbering the app
-- began with. A sequence keeps its place across restarts, which the Python
-- counter this replaced could not.
--
-- Reproduced exactly as pg_dump emitted it, including the absence of
-- "AS integer" (which makes it a bigint sequence feeding an integer column -
-- harmless, and matching local).
CREATE SEQUENCE IF NOT EXISTS public.account_number_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

-- The other five sequences in the database are all SERIAL-owned, so they are
-- created implicitly by the SERIAL columns below and need no declaration:
--     branches_branch_code_seq, customers_id_seq, staff_id_seq,
--     transactions_id_seq, transfer_limits_id_seq
-- Writing SERIAL produces exactly what the dump shows for those columns:
-- integer NOT NULL DEFAULT nextval(...), plus a sequence OWNED BY the column.


-- ---------------------------------------------------------------------------
-- branches
-- ---------------------------------------------------------------------------
-- A physical location of the bank. Keyed by branch_code rather than a
-- surrogate id, so every other table stores the code itself.
--
-- HEADS UP: branch_code is SERIAL in the live database, not a plain integer.
-- app/models/branch.py declares it primary_key=True on an Integer, and
-- SQLAlchemy makes any integer primary key auto-incrementing. See note 3 at
-- the bottom, because the app does not actually use that behaviour.
CREATE TABLE IF NOT EXISTS public.branches (
    branch_code  SERIAL,
    location     VARCHAR(200),
    manager_id   VARCHAR(50),

    CONSTRAINT branches_pkey PRIMARY KEY (branch_code)
);


-- ---------------------------------------------------------------------------
-- customers
-- ---------------------------------------------------------------------------
-- A person who holds one or more accounts.
CREATE TABLE IF NOT EXISTS public.customers (
    id           SERIAL,
    name         VARCHAR(120) NOT NULL,
    email        VARCHAR(255) NOT NULL,
    -- Holds the branch's code, not a surrogate id, hence the name.
    branch_code  INTEGER,
    -- No DEFAULT, matching the live database. Customer's constructor sets
    -- is_active in Python. Adding a server default here would show up as
    -- drift the next time Alembic autogenerates a migration.
    is_active    BOOLEAN      NOT NULL,

    CONSTRAINT customers_pkey PRIMARY KEY (id)
);


-- ---------------------------------------------------------------------------
-- staff
-- ---------------------------------------------------------------------------
-- One employee working at a branch.
CREATE TABLE IF NOT EXISTS public.staff (
    id           SERIAL,
    name         VARCHAR(120) NOT NULL,
    branch_code  INTEGER,

    CONSTRAINT staff_pkey PRIMARY KEY (id)
);


-- ---------------------------------------------------------------------------
-- accounts
-- ---------------------------------------------------------------------------
-- Savings and Checking share this one table (single table inheritance).
-- The "type" column is the discriminator saying which one a row is.
CREATE TABLE IF NOT EXISTS public.accounts (
    -- Not SERIAL: it draws from the standalone account_number_seq created
    -- above, which starts at 1000 rather than 1.
    account_number  INTEGER        NOT NULL
                    DEFAULT nextval('public.account_number_seq'::regclass),
    owner           VARCHAR(120)   NOT NULL,
    owner_id        INTEGER        NOT NULL,
    -- NUMERIC, never a float. Floats cannot represent values like 0.10
    -- exactly, and the error accumulates over every transaction.
    balance         NUMERIC(12, 2) NOT NULL,
    -- "Savings" or "Checking".
    type            VARCHAR(20)    NOT NULL,
    branch_code     INTEGER,

    CONSTRAINT accounts_pkey PRIMARY KEY (account_number)
);


-- ---------------------------------------------------------------------------
-- transactions
-- ---------------------------------------------------------------------------
-- A single movement of money.
--
-- Both account columns are nullable because a deposit has no source and a
-- withdrawal has no destination.
CREATE TABLE IF NOT EXISTS public.transactions (
    id                SERIAL,
    -- "TRANSFER", "DEPOSIT" or "WITHDRAWAL".
    transaction_type  VARCHAR(20)    NOT NULL,
    amount            NUMERIC(12, 2) NOT NULL,
    from_account_id   INTEGER,
    to_account_id     INTEGER,
    -- "timestamp" is quoted because it is a reserved word in SQL. Type is
    -- timestamp without time zone, matching the naive local times the app
    -- writes. See note 4 about time zones on Supabase.
    "timestamp"       TIMESTAMP WITHOUT TIME ZONE NOT NULL,

    CONSTRAINT transactions_pkey PRIMARY KEY (id)
);


-- ---------------------------------------------------------------------------
-- transfer_limits
-- ---------------------------------------------------------------------------
-- A cap a customer sets on their own outgoing transfers. A customer can hold
-- several at once, and every one has to pass before a transfer goes through.
CREATE TABLE IF NOT EXISTS public.transfer_limits (
    id                   SERIAL,
    -- Points at customers.id, not users.username, because that is the value
    -- the token's subject claim resolves to and what every other ownership
    -- check in the app compares against.
    user_id              INTEGER        NOT NULL,
    -- "PER_TRANSACTION", "DAILY" or "MONTHLY". Plain text rather than a
    -- PostgreSQL enum type, matching transactions.transaction_type and
    -- accounts.type, so a fourth kind later needs no ALTER TYPE.
    limit_type           VARCHAR(20)    NOT NULL,
    max_amount           NUMERIC(12, 2) NOT NULL,
    -- How much of the ceiling the current period has used. NOT NULL so the
    -- limit check never has to add to a NULL.
    current_period_used  NUMERIC(12, 2) NOT NULL,
    -- When that period began. Comparing this against now is what detects a
    -- rollover without needing a background job.
    period_start         TIMESTAMP WITHOUT TIME ZONE NOT NULL,

    CONSTRAINT transfer_limits_pkey PRIMARY KEY (id)
);


-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
-- Login credentials and the claims that end up inside a token.
--
-- IMPORTANT: this is the APP'S OWN user table and has nothing to do with
-- Supabase Auth's auth.users. See note 1 at the bottom - there is no
-- collision, and Supabase Auth should not be used for this project.
--
-- password holds a bcrypt hash, never the password. bcrypt keeps the salt
-- inside the hash string, so there is no separate salt column.
--
-- No foreign key ties users.sub to customers.id even though signup puts a
-- customer id there. That matches the live database; the link is enforced in
-- app/services/login_service.py, not by the schema.
CREATE TABLE IF NOT EXISTS public.users (
    -- 120, matching customers.name. Was VARCHAR(20) until ae9e35893c3e.
    username  VARCHAR(120) NOT NULL,
    -- A bcrypt hash is 60 characters. 255 leaves room for a longer algorithm.
    password  VARCHAR(255) NOT NULL,
    -- 255, matching customers.email, which registration writes the same
    -- address into. This was VARCHAR(20) until ae9e35893c3e, which rejected
    -- any address over 20 characters outright. See note 5.
    email     VARCHAR(255) NOT NULL,
    sub       VARCHAR(40)  NOT NULL,
    roles     VARCHAR(40)  NOT NULL,

    CONSTRAINT users_pkey      PRIMARY KEY (username),
    -- sub is what lands in the token's subject claim, so a duplicate would
    -- make two users indistinguishable to every route that reads it.
    CONSTRAINT users_sub_key   UNIQUE (sub),
    CONSTRAINT users_email_key UNIQUE (email)
);


-- ---------------------------------------------------------------------------
-- FOREIGN KEYS
-- ---------------------------------------------------------------------------
-- Split out from the CREATE TABLE statements purely so this script can be
-- re-run. PostgreSQL has no "ADD CONSTRAINT IF NOT EXISTS", so each one is
-- wrapped in a guard that checks the catalog first.
--
-- The table order above already resolves these correctly on a clean run;
-- the guards only matter when re-running against a partial database.
--
-- Names match what Alembic generated locally. Keeping them identical means a
-- future "alembic revision --autogenerate" will not see unfamiliar
-- constraints and offer to drop them.
--
-- None of these declare ON DELETE / ON UPDATE, matching the live database:
-- deleting a branch that still has customers is refused outright rather than
-- cascading. That is the desired behaviour for financial records.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'customers_branch_code_fkey'
                     AND connamespace = 'public'::regnamespace) THEN
        ALTER TABLE public.customers
            ADD CONSTRAINT customers_branch_code_fkey
            FOREIGN KEY (branch_code) REFERENCES public.branches(branch_code);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'staff_branch_code_fkey'
                     AND connamespace = 'public'::regnamespace) THEN
        ALTER TABLE public.staff
            ADD CONSTRAINT staff_branch_code_fkey
            FOREIGN KEY (branch_code) REFERENCES public.branches(branch_code);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'accounts_branch_code_fkey'
                     AND connamespace = 'public'::regnamespace) THEN
        ALTER TABLE public.accounts
            ADD CONSTRAINT accounts_branch_code_fkey
            FOREIGN KEY (branch_code) REFERENCES public.branches(branch_code);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'accounts_owner_id_fkey'
                     AND connamespace = 'public'::regnamespace) THEN
        ALTER TABLE public.accounts
            ADD CONSTRAINT accounts_owner_id_fkey
            FOREIGN KEY (owner_id) REFERENCES public.customers(id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'transactions_from_account_id_fkey'
                     AND connamespace = 'public'::regnamespace) THEN
        ALTER TABLE public.transactions
            ADD CONSTRAINT transactions_from_account_id_fkey
            FOREIGN KEY (from_account_id)
            REFERENCES public.accounts(account_number);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'transactions_to_account_id_fkey'
                     AND connamespace = 'public'::regnamespace) THEN
        ALTER TABLE public.transactions
            ADD CONSTRAINT transactions_to_account_id_fkey
            FOREIGN KEY (to_account_id)
            REFERENCES public.accounts(account_number);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'transfer_limits_user_id_fkey'
                     AND connamespace = 'public'::regnamespace) THEN
        ALTER TABLE public.transfer_limits
            ADD CONSTRAINT transfer_limits_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES public.customers(id);
    END IF;
END
$$;


-- ---------------------------------------------------------------------------
-- INDEXES
-- ---------------------------------------------------------------------------
-- The only non-constraint index in the database. Every transfer looks these
-- rows up by user_id before the money moves, so it sits on the hot path, and
-- PostgreSQL does not index a foreign key column on its own.
--
-- The other foreign key columns (accounts.owner_id, accounts.branch_code,
-- customers.branch_code, staff.branch_code, transactions.from_account_id,
-- transactions.to_account_id) have no index, matching local. Worth revisiting
-- once transaction volume grows, but it is not part of this migration.
CREATE INDEX IF NOT EXISTS ix_transfer_limits_user_id
    ON public.transfer_limits USING btree (user_id);


-- ---------------------------------------------------------------------------
-- ALEMBIC BOOKKEEPING
-- ---------------------------------------------------------------------------
-- alembic_version is a real table in the local database, so it is reproduced
-- here. Without it - or without the row - pointing Alembic at Supabase and
-- running "alembic upgrade head" would try to replay all three migrations
-- against tables that already exist, and fail on the first CREATE TABLE.
--
-- The row records that the schema is already at the latest revision, so
-- Alembic sees the database as up to date and future migrations apply
-- normally.
--
-- Equivalent from the command line, once DATABASE_URL points at Supabase:
--     alembic stamp head
CREATE TABLE IF NOT EXISTS public.alembic_version (
    version_num VARCHAR(32) NOT NULL,

    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Guarded so re-running does not raise a duplicate key error.
INSERT INTO public.alembic_version (version_num)
SELECT 'ae9e35893c3e'
WHERE NOT EXISTS (SELECT 1 FROM public.alembic_version);


-- ---------------------------------------------------------------------------
-- ROW LEVEL SECURITY  (recommended - read note 2 before removing)
-- ---------------------------------------------------------------------------
-- Short version: this does NOT block your FastAPI backend, and you do not
-- need to disable it. Full reasoning in note 2 at the bottom.
--
-- Supabase publishes every table in the "public" schema through its
-- auto-generated PostgREST API, and its default privileges grant the "anon"
-- and "authenticated" roles access to new tables there. Without RLS, anyone
-- holding the project's publishable anon key could read balances and bcrypt
-- hashes straight out of these tables.
--
-- Enabling RLS with no policies denies those roles completely. Your backend
-- is unaffected because it connects over the direct Postgres connection
-- string as the "postgres" role, which has the BYPASSRLS attribute on
-- Supabase. Verify that on your own project with:
--     SELECT current_user, rolbypassrls
--     FROM pg_roles WHERE rolname = current_user;
--
-- Delete this block only if you intend to query Supabase from the browser
-- with the anon key, in which case write policies to go with it.
ALTER TABLE public.branches        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.customers       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.staff           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounts        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transfer_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;


-- ===========================================================================
-- NOTES - read before and after running
-- ===========================================================================
--
-- 1. NO COLLISION WITH SUPABASE AUTH, AND DO NOT USE IT HERE
--    Supabase Auth's user table is auth.users - it lives in the "auth"
--    schema. The table this script creates is public.users. Different
--    schemas, so they coexist with no conflict, no rename needed.
--
--    Your SQLAlchemy connection resolves unqualified names through the
--    default search_path, which puts "public" first, so every "users" query
--    the app issues hits public.users. auth.users is never touched.
--
--    DO NOT enable or use Supabase Auth for this project. Your app already
--    has a complete auth system: bcrypt hashing plus JWTs signed with
--    JWT_SECRET_KEY in app/core/security.py, and role checks in
--    app/core/dependencies.py. Running Supabase Auth alongside it would mean
--    two independent sources of identity, two token formats, and two places
--    a user could exist - with nothing keeping them in sync. Leave Supabase
--    Auth switched off and keep JWT_SECRET_KEY as the only signing key.
--
-- 2. RLS - YOU DO NOT NEED TO DISABLE IT, AND YOUR API WILL NOT BE BLOCKED
--    Two facts settle this:
--      a) Tables created by raw SQL like this script do NOT get RLS
--         automatically. Supabase only pre-ticks "Enable RLS" when you create
--         a table through the dashboard's Table Editor. So without the block
--         above, these tables would have RLS OFF.
--      b) The "postgres" role your connection string uses has BYPASSRLS on
--         Supabase, so RLS never applies to your backend either way.
--    So RLS cannot silently block your API. The block above is there for the
--    opposite risk: with RLS off, the anon key can reach these tables through
--    PostgREST. Enabling it with no policies closes that door while leaving
--    your backend untouched. Confirm with the query in that section after
--    connecting, and if rolbypassrls ever comes back false, that is the
--    signal to revisit.
--
-- 3. branches.branch_code IS SERIAL, BUT THE APP ALWAYS SUPPLIES IT
--    app/services/branch_service.py passes branch_code explicitly on every
--    insert, so branches_branch_code_seq never advances - it is still at 1,
--    unused, on the local database. On a fresh Supabase project it will also
--    sit at 1. If a branch is ever inserted WITHOUT a code, it would draw 1
--    and collide with an existing branch 1 (which local already has). Not
--    introduced by this migration, but worth knowing.
--
-- 4. TIME ZONES
--    timestamps and period_start are "timestamp without time zone", and the
--    app writes naive local times via datetime.now(). Supabase servers run in
--    UTC while your machine does not, so the same code will record different
--    wall-clock values once deployed. Existing rows carry no offset saying
--    which zone they were written in. Switching to timestamptz is the real
--    fix; this script deliberately does not, because that is a schema change
--    and you asked for an exact match.
--
-- 5. FIXED: users.email AND users.username WERE TOO SMALL
--    Both columns were VARCHAR(20) and rejected ordinary values outright,
--    because PostgreSQL refuses an over-length string rather than truncating
--    it. Registering with a 24-character address failed with
--        ERROR: value too long for type character varying(20)
--
--    Migration ae9e35893c3e widened email to 255 and username to 120, and the
--    widths above already reflect that. Verified through the real
--    POST /api/v1/registration endpoint: a 24-character address and a
--    54-character one both return 201, and logging in with a 34-character
--    username returns a valid token.
--
--    Nothing to do here - this note is kept so the history is clear if you
--    compare this file against an older database.
--
-- 6. IF YOU LATER COPY DATA ACROSS
--    This script creates empty tables. Loading rows afterwards leaves every
--    sequence at its starting value, and the next insert then collides with
--    an existing id. Resync them after any data load:
--        SELECT setval('public.account_number_seq',
--                      (SELECT COALESCE(MAX(account_number), 999) FROM public.accounts));
--        SELECT setval('public.customers_id_seq',
--                      (SELECT COALESCE(MAX(id), 1) FROM public.customers));
--        SELECT setval('public.staff_id_seq',
--                      (SELECT COALESCE(MAX(id), 1) FROM public.staff));
--        SELECT setval('public.transactions_id_seq',
--                      (SELECT COALESCE(MAX(id), 1) FROM public.transactions));
--        SELECT setval('public.transfer_limits_id_seq',
--                      (SELECT COALESCE(MAX(id), 1) FROM public.transfer_limits));
--        SELECT setval('public.branches_branch_code_seq',
--                      (SELECT COALESCE(MAX(branch_code), 1) FROM public.branches));
--
-- 7. CONNECTING THE APP
--    Point DATABASE_URL in .env at Supabase, keeping the psycopg3 driver
--    prefix the app expects:
--        DATABASE_URL=postgresql+psycopg://postgres:PASSWORD@HOST:5432/postgres
--    Two things that catch people out:
--      - The database name on Supabase is "postgres", not "bankingapp".
--      - If you use the transaction pooler (port 6543) rather than a direct
--        connection (5432), psycopg3's prepared statements break against it.
--        Append ?prepare_threshold=0 to the URL, or use the session pooler.
--        The direct connection is also IPv6-only unless your project has the
--        IPv4 add-on, which is the usual reason a direct connection hangs.
--
-- ===========================================================================
-- MODEL / DATABASE MISMATCHES FOUND DURING CROSS-CHECK
-- ===========================================================================
-- Every column in app/models/ was compared against the dump. Types,
-- nullability, precision, defaults, primary keys, foreign keys and the index
-- all agree, EXCEPT the following. This script follows the DATABASE in every
-- case, since that is what the app runs against today.
--
--   A. users - three columns are still unbounded String in the model but
--      sized in the database: password, sub and roles are declared as plain
--      String in app/models/login.py (which would be TEXT, unlimited) while
--      the database has VARCHAR(255), (40) and (40).
--
--      username and email used to be in this list and no longer are. They
--      were given explicit String(120) and String(255) alongside migration
--      ae9e35893c3e, so model and database now agree on both.
--
--      The remaining three are harmless today, since nothing writes a value
--      near those limits, but they are the same latent trap: alembic
--      autogenerate does not compare String lengths by default, so it will
--      never warn you. Giving them explicit lengths is a one-line change
--      each, deliberately left out of this migration to keep it scoped.
--
--   B. branches.branch_code - the model declares unique=True alongside
--      primary_key=True, and the initial migration asks for a
--      UniqueConstraint, yet no separate unique constraint exists in the
--      database. Only branches_pkey is present.
--
--      Confirmed harmless: running "alembic upgrade head" against a fresh
--      empty database produces exactly the same 17 constraints as the live
--      one, so the redundant UniqueConstraint is collapsed into the primary
--      key rather than creating a second constraint. Cosmetic drift in the
--      model and migration only - nothing to add here, and rebuilding from
--      migrations elsewhere gives the same schema this script does.
--
--   C. accounts.account_number - same as B, and same conclusion. unique=True
--      sits alongside primary_key=True in app/models/account.py, and only
--      accounts_pkey exists in the database.
--
-- Checked and found clean: no CHECK constraints, no triggers, and no
-- extensions beyond plpgsql, so nothing of that kind is missing from this
-- script.
-- ===========================================================================
