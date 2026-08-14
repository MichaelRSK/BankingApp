-- BankingApp schema for Supabase (PostgreSQL)
--
-- This is the same schema Alembic builds locally, flattened into plain SQL:
--   426f100f79f6  initial schema
--   528f100fabcd  widened users.password to 255
--   95dd0676a507  added transfer_limits
--
-- Run it in the Supabase SQL Editor, or with psql against the connection
-- string from Project Settings -> Database.
--
-- Tables are created in dependency order, because a foreign key can only
-- point at a table that already exists: branches first, then customers and
-- staff, then accounts, then everything that points at accounts.
--
-- Everything lands in the "public" schema, which is where Supabase expects
-- application tables and what the connection string defaults to.


-- ---------------------------------------------------------------------------
-- branches
-- ---------------------------------------------------------------------------
-- A physical location of the bank. Keyed by branch_code rather than a
-- surrogate id, so every other table stores the code itself.
CREATE TABLE public.branches (
    branch_code  INTEGER      NOT NULL,
    location     VARCHAR(200),
    manager_id   VARCHAR(50),

    CONSTRAINT branches_pkey        PRIMARY KEY (branch_code),
    -- Redundant next to the primary key, but the model declares unique=True
    -- alongside primary_key=True, so the migration created both. Kept here so
    -- the database matches what Alembic autogenerate expects to find.
    CONSTRAINT branches_branch_code_key UNIQUE (branch_code)
);


-- ---------------------------------------------------------------------------
-- customers
-- ---------------------------------------------------------------------------
-- A person who holds one or more accounts.
--
-- SERIAL is what SQLAlchemy emits for an auto-incrementing integer primary
-- key, so it is used here rather than IDENTITY to keep the two identical.
CREATE TABLE public.customers (
    id           SERIAL       NOT NULL,
    name         VARCHAR(120) NOT NULL,
    email        VARCHAR(255) NOT NULL,
    -- Holds the branch's code, not a surrogate id, hence the name.
    branch_code  INTEGER,
    -- No DEFAULT on purpose: the application sets is_active in Customer's
    -- constructor, and adding a server default here would show up as drift
    -- the next time Alembic autogenerates a migration.
    is_active    BOOLEAN      NOT NULL,

    CONSTRAINT customers_pkey             PRIMARY KEY (id),
    CONSTRAINT customers_branch_code_fkey FOREIGN KEY (branch_code)
        REFERENCES public.branches (branch_code)
);


-- ---------------------------------------------------------------------------
-- staff
-- ---------------------------------------------------------------------------
-- One employee working at a branch.
CREATE TABLE public.staff (
    id           SERIAL       NOT NULL,
    name         VARCHAR(120) NOT NULL,
    branch_code  INTEGER,

    CONSTRAINT staff_pkey             PRIMARY KEY (id),
    CONSTRAINT staff_branch_code_fkey FOREIGN KEY (branch_code)
        REFERENCES public.branches (branch_code)
);


-- ---------------------------------------------------------------------------
-- accounts
-- ---------------------------------------------------------------------------
-- The sequence behind account_number. It is created separately, and before
-- the table, because the column's DEFAULT calls nextval() on it.
--
-- Starting at 1000 reproduces the customer-facing numbering the app began
-- with. A sequence keeps its place across restarts, which a Python counter
-- could not.
CREATE SEQUENCE public.account_number_seq START WITH 1000;

-- Savings and Checking share this one table (single table inheritance). The
-- "type" column is the discriminator that says which one a row is.
CREATE TABLE public.accounts (
    account_number  INTEGER        NOT NULL
                    DEFAULT nextval('public.account_number_seq'),
    owner           VARCHAR(120)   NOT NULL,
    owner_id        INTEGER        NOT NULL,
    -- NUMERIC, never a float. Floats cannot represent values like 0.10
    -- exactly and the error accumulates over every transaction.
    balance         NUMERIC(12, 2) NOT NULL,
    -- "Savings" or "Checking".
    type            VARCHAR(20)    NOT NULL,
    branch_code     INTEGER,

    CONSTRAINT accounts_pkey             PRIMARY KEY (account_number),
    CONSTRAINT accounts_branch_code_fkey FOREIGN KEY (branch_code)
        REFERENCES public.branches (branch_code),
    CONSTRAINT accounts_owner_id_fkey    FOREIGN KEY (owner_id)
        REFERENCES public.customers (id)
);


-- ---------------------------------------------------------------------------
-- transactions
-- ---------------------------------------------------------------------------
-- A single movement of money.
--
-- Both account columns are nullable because a deposit has no source and a
-- withdrawal has no destination.
CREATE TABLE public.transactions (
    id                SERIAL         NOT NULL,
    -- "TRANSFER", "DEPOSIT" or "WITHDRAWAL".
    transaction_type  VARCHAR(20)    NOT NULL,
    amount            NUMERIC(12, 2) NOT NULL,
    from_account_id   INTEGER,
    to_account_id     INTEGER,
    -- Naive local time, matching the application, which stamps this itself.
    timestamp         TIMESTAMP      NOT NULL,

    CONSTRAINT transactions_pkey                 PRIMARY KEY (id),
    CONSTRAINT transactions_from_account_id_fkey FOREIGN KEY (from_account_id)
        REFERENCES public.accounts (account_number),
    CONSTRAINT transactions_to_account_id_fkey   FOREIGN KEY (to_account_id)
        REFERENCES public.accounts (account_number)
);


-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
-- Login credentials and the claims that end up inside a token.
--
-- This is the app's own user table and has nothing to do with Supabase's
-- built-in auth.users. The app signs its own JWTs in app/core/security.py.
--
-- password holds a bcrypt hash, never the password. bcrypt keeps the salt
-- inside the hash string, so there is no separate salt column.
CREATE TABLE public.users (
    username  VARCHAR(20)  NOT NULL,
    -- A bcrypt hash is 60 characters. 255 leaves room for a longer algorithm.
    password  VARCHAR(255) NOT NULL,
    -- NOTE: 20 characters is what the migration created, and it is tight for
    -- a real address ("michaelrsk2004@gmail.com" is 24). See the note below
    -- the script if you would rather widen it.
    email     VARCHAR(20)  NOT NULL,
    sub       VARCHAR(40)  NOT NULL,
    roles     VARCHAR(40)  NOT NULL,

    CONSTRAINT users_pkey      PRIMARY KEY (username),
    -- sub is what lands in the token's subject claim, so a duplicate would
    -- make two users indistinguishable to every route that reads it.
    CONSTRAINT users_sub_key   UNIQUE (sub),
    CONSTRAINT users_email_key UNIQUE (email)
);


-- ---------------------------------------------------------------------------
-- transfer_limits
-- ---------------------------------------------------------------------------
-- A cap a customer sets on their own outgoing transfers. A customer can hold
-- several at once, and every one has to pass before a transfer goes through.
CREATE TABLE public.transfer_limits (
    id                   SERIAL         NOT NULL,
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
    period_start         TIMESTAMP      NOT NULL,

    CONSTRAINT transfer_limits_pkey         PRIMARY KEY (id),
    CONSTRAINT transfer_limits_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.customers (id)
);

-- Every transfer looks these rows up by user_id before the money moves, so
-- this is on the hot path. PostgreSQL does not index a foreign key column on
-- its own. The name matches what Alembic generated, otherwise the next
-- autogenerate would see an unfamiliar index and offer to drop it.
CREATE INDEX ix_transfer_limits_user_id
    ON public.transfer_limits (user_id);


-- ---------------------------------------------------------------------------
-- Row Level Security (optional, but recommended on Supabase)
-- ---------------------------------------------------------------------------
-- Supabase exposes every table in "public" through its auto-generated REST
-- API. These tables hold balances and password hashes, so leaving them
-- reachable by the anon key would hand them to anyone with the project URL.
--
-- Enabling RLS with no policies denies the anon and authenticated roles
-- entirely. The FastAPI backend is unaffected: it connects over the direct
-- Postgres connection string as the "postgres" role, which bypasses RLS.
--
-- Comment this block out only if you intend to query Supabase from the
-- browser, in which case write policies to go with it.
ALTER TABLE public.branches        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.customers       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.staff           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounts        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transfer_limits ENABLE ROW LEVEL SECURITY;


-- ---------------------------------------------------------------------------
-- Alembic bookkeeping (optional)
-- ---------------------------------------------------------------------------
-- Because this script builds the schema directly, Alembic does not know the
-- three migrations have already been applied and "alembic upgrade head" would
-- try to run them again and fail on the existing tables.
--
-- These two statements record the current revision, so Alembic sees the
-- database as already up to date and future migrations apply cleanly.
--
-- The equivalent from the command line, once DATABASE_URL points at Supabase:
--   alembic stamp head
CREATE TABLE public.alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INSERT INTO public.alembic_version (version_num) VALUES ('95dd0676a507');
