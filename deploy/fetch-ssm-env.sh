#!/usr/bin/env bash
#
# Pulls the app's secrets out of AWS Systems Manager Parameter Store and
# writes them where systemd can read them.
#
# This exists so no secret is ever written into the repo or left in a .env
# file on the instance's disk. The instance authenticates with its attached
# IAM role, so there is no access key on the box either.
#
# Every parameter under the prefix becomes one environment variable, named
# after the last segment of its path:
#
#   /bankingapp/DATABASE_URL    ->  DATABASE_URL=...
#   /bankingapp/JWT_SECRET_KEY  ->  JWT_SECRET_KEY=...
#
# That naming is deliberate: app/core/config.py and app/db/session.py already
# read exactly these names with os.getenv, so nothing in the application has
# to change.
#
# Run by bankingapp-env.service before the app starts.

set -euo pipefail

# The region the parameters live in. Overridable so the same script works if
# the stack is ever rebuilt elsewhere.
REGION="${AWS_REGION:-us-east-1}"

# Everything under this path is treated as config for this app.
PREFIX="${SSM_PREFIX:-/bankingapp}"

# Root-owned and not world readable: this file holds the database password
# and the JWT signing key.
OUT_DIR="/etc/bankingapp"
OUT_FILE="${OUT_DIR}/env"

install -d -m 0750 "${OUT_DIR}"

# Written to a temporary file first, then moved into place. A move is atomic,
# so the service can never read a half-written file if this script is
# interrupted partway through.
TMP_FILE="$(mktemp)"
chmod 0640 "${TMP_FILE}"

# --with-decryption is what turns a SecureString back into its real value.
# It requires kms:Decrypt on the key the parameters were encrypted with,
# which is part of the IAM policy in deploy/README.md.
#
# The AWS CLI v2 paginates automatically, so this returns every parameter
# under the prefix rather than only the first page.
aws ssm get-parameters-by-path \
    --path "${PREFIX}" \
    --with-decryption \
    --region "${REGION}" \
    --query 'Parameters[].[Name,Value]' \
    --output text \
| while IFS=$'\t' read -r name value; do
    # Strip the path, keeping only the final segment as the variable name.
    printf '%s=%s\n' "${name##*/}" "${value}"
done > "${TMP_FILE}"

# A successful call that returns nothing means the parameters were never
# created, or the prefix is wrong. Failing here is much easier to diagnose
# than letting the app start and die on "DATABASE_URL is not set".
if [ ! -s "${TMP_FILE}" ]; then
    echo "No parameters found under ${PREFIX} in ${REGION}." >&2
    echo "Check the prefix, the region, and the instance's IAM role." >&2
    rm -f "${TMP_FILE}"
    exit 1
fi

mv "${TMP_FILE}" "${OUT_FILE}"
chmod 0640 "${OUT_FILE}"

echo "Wrote $(wc -l < "${OUT_FILE}") variable(s) to ${OUT_FILE}"
