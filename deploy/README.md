# Deploying the backend to EC2

Runbook for getting the FastAPI backend live on an EC2 instance, reading its
secrets from AWS Systems Manager Parameter Store rather than a `.env` file.

The database stays on Supabase. Nothing here touches the frontend.

---

## What was actually deployed (2026-08-14)

Live on `i-07cbc90516580d7b6` at **http://54.243.21.175:8000**, Amazon Linux
2023, Python 3.11.15, repo at branch `supabase-integration`.

**Parameter Store was not used.** The account is a Qwiklabs sandbox
(`user/michael-krueger@quicklabs.internal`) with IAM locked down: the
instance profile dropdown is empty because roles cannot be created, and the
instance's IAM role is confirmed empty. Without a role the instance cannot
authenticate to SSM at all, so section 6's `put-parameter` route is not
available there.

What was done instead: `/etc/bankingapp/env` written by hand, root-owned and
mode 0640, holding `DATABASE_URL` and a freshly generated `JWT_SECRET_KEY`.
`bankingapp.service` reads it with `EnvironmentFile`, exactly as it would
have if SSM had populated the same file, so nothing else changed and no
application code was touched.

Keep the SSM sections below: they are correct for any account that allows
role creation, and re-enabling that path is a two-line change documented in
`bankingapp.service`.

Everything below assumes **Amazon Linux 2023**, which ships Python 3.11 and
the AWS CLI v2 already. On Ubuntu the package manager commands differ
(`apt` instead of `dnf`, user `ubuntu` instead of `ec2-user`).

---

## 0. Prerequisites on your own machine

```bash
aws configure          # access key, secret, default region, output format
aws sts get-caller-identity   # should print your account and user ARN
```

Set `REGION` and `KEY_NAME` to match what you use below.

---

## 1. Confirm the instance is running and get its public IP

```bash
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].{ID:InstanceId,IP:PublicIpAddress,Name:Tags[?Key==`Name`]|[0].Value,SG:SecurityGroups[0].GroupId,Role:IamInstanceProfile.Arn}' \
  --output table
```

If this returns nothing, no instance is running and one must be launched
first.

---

## 2. SSH in

The key pair `.pem` is downloadable only once, at creation. If it is lost,
the key cannot be recovered and a new key pair is needed.

```bash
# Windows: restrict the key so SSH stops refusing it as too permissive
icacls "C:\path\to\your-key.pem" /inheritance:r /grant:r "%USERNAME%:R"

ssh -i "C:\path\to\your-key.pem" ec2-user@<PUBLIC_IP>
```

Ubuntu AMIs use `ubuntu@` instead of `ec2-user@`.

---

## 3. Install Python, pip and git on the instance

```bash
sudo dnf update -y
sudo dnf install -y python3 python3-pip git
python3 --version      # expect 3.11.x on AL2023
```

---

## 4. Get the code onto the instance

The repo is public, so a plain clone works and needs no credentials:

```bash
cd /home/ec2-user
git clone https://github.com/tectorm/BankingApp.git
cd BankingApp
```

If the repo is private, either create a read-only deploy key on the instance
(`ssh-keygen -t ed25519`, add the public key under the repo's Deploy Keys)
and clone over SSH, or copy the code up from your machine with
`scp -i key.pem -r . ec2-user@<IP>:~/BankingApp`.

**`.env` is gitignored and will not come across. That is intentional** —
the secrets come from Parameter Store instead, in step 6.

---

## 5. Install dependencies

A virtual environment, so the app's packages never collide with the system
Python that `dnf` manages:

```bash
cd /home/ec2-user/BankingApp
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
```

The systemd unit runs `.venv/bin/uvicorn` directly, so the environment never
has to be "activated" the way it is interactively.

---

## 6. Secrets in Parameter Store

### Store them

`SecureString` encrypts the value at rest with KMS. Both of these are
genuine secrets, so neither should be a plain `String`.

```bash
aws ssm put-parameter \
  --name "/bankingapp/DATABASE_URL" \
  --type "SecureString" \
  --value "postgresql+psycopg://postgres.PROJECTREF:PASSWORD@aws-0-us-east-1.pooler.supabase.com:5432/postgres" \
  --overwrite

aws ssm put-parameter \
  --name "/bankingapp/JWT_SECRET_KEY" \
  --type "SecureString" \
  --value "$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  --overwrite
```

**Generate a new JWT signing key for production rather than reusing the local
one.** Anyone holding that key can mint a valid token for any user, and the
local value has been sitting in a `.env` on your development machine. A
different key per environment also means tokens from one cannot be replayed
against the other.

Verify:

```bash
aws ssm get-parameters-by-path --path "/bankingapp" --with-decryption \
  --query 'Parameters[].Name' --output table
```

### Let the instance read them

The instance needs an IAM role. Since the console dropdown was not
cooperating, attach it from the CLI:

```bash
# Trust policy: only EC2 may assume this role
cat > trust.json <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
 "Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}
EOF

aws iam create-role --role-name BankingAppInstanceRole \
  --assume-role-policy-document file://trust.json

# Read-only on this app's parameters, and decrypt for the SecureStrings.
# Scoped to /bankingapp/* rather than all of SSM.
cat > ssm-policy.json <<'EOF'
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":["ssm:GetParameter","ssm:GetParameters","ssm:GetParametersByPath"],
  "Resource":"arn:aws:ssm:*:*:parameter/bankingapp/*"},
 {"Effect":"Allow","Action":["kms:Decrypt"],"Resource":"*",
  "Condition":{"StringEquals":{"kms:ViaService":"ssm.us-east-1.amazonaws.com"}}}]}
EOF

aws iam put-role-policy --role-name BankingAppInstanceRole \
  --policy-name BankingAppSSMRead --policy-document file://ssm-policy.json

aws iam create-instance-profile --instance-profile-name BankingAppInstanceProfile
aws iam add-role-to-instance-profile \
  --instance-profile-name BankingAppInstanceProfile \
  --role-name BankingAppInstanceRole

# This is the step the console dropdown was failing to do
aws ec2 associate-iam-instance-profile \
  --instance-id <INSTANCE_ID> \
  --iam-instance-profile Name=BankingAppInstanceProfile
```

Confirm from on the instance:

```bash
aws sts get-caller-identity     # should show the assumed role
aws ssm get-parameters-by-path --path /bankingapp --with-decryption \
  --region us-east-1 --query 'Parameters[].Name'
```

### Why no application code changes

`app/core/config.py` and `app/db/session.py` both call `load_dotenv()` and
then `os.getenv(...)`. `load_dotenv()` **does not overwrite variables already
present in the environment**, so real environment variables take precedence
and the missing `.env` is simply ignored.

So the secrets only need to be in the process environment before uvicorn
starts, which `bankingapp-env.service` does. Fetching from SSM inside the app
would mean editing both files, adding boto3, and handling SSM failures at
import time, to arrive at the same result.

---

## 7. Security group rules

Show what is currently allowed:

```bash
aws ec2 describe-security-groups --group-ids <SG_ID> \
  --query 'SecurityGroups[].IpPermissions[].{Proto:IpProtocol,From:FromPort,To:ToPort,CIDR:IpRanges[].CidrIp}' \
  --output table
```

Open SSH and the app port if they are missing. Lock SSH to your own address
rather than the whole internet:

```bash
MYIP=$(curl -s https://checkip.amazonaws.com)

aws ec2 authorize-security-group-ingress --group-id <SG_ID> \
  --protocol tcp --port 22 --cidr "${MYIP}/32"

aws ec2 authorize-security-group-ingress --group-id <SG_ID> \
  --protocol tcp --port 8000 --cidr 0.0.0.0/0
```

Port 8000 open to the world is fine for getting this reachable and testing
it. It is **plain HTTP**, so tokens and passwords cross the network
unencrypted — see the note at the bottom before this is used for anything
real.

---

## 8. Run it under systemd

From the repo on the instance:

```bash
sudo install -m 0755 deploy/fetch-ssm-env.sh /usr/local/bin/fetch-ssm-env.sh
sudo install -m 0644 deploy/bankingapp-env.service /etc/systemd/system/
sudo install -m 0644 deploy/bankingapp.service     /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now bankingapp-env.service
sudo systemctl enable --now bankingapp.service

systemctl status bankingapp --no-pager
journalctl -u bankingapp -n 50 --no-pager
```

`enable` is what makes it start again after a reboot; `--now` starts it
immediately as well.

Check it locally on the instance first, which separates "the app is broken"
from "the network is blocking it":

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/docs
```

---

## 9. Verify from your own machine

This is the check that actually proves it is reachable from outside AWS:

```bash
curl -i http://<PUBLIC_IP>:8000/docs

# Reaches the database too: a bogus login should return 401, not 500
curl -i -X POST http://<PUBLIC_IP>:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"__nobody__","password":"__nope__"}'
```

`401` means the request reached FastAPI, which queried Supabase and found no
such user — the whole chain works. A `500` instead points at `DATABASE_URL`.

If curl hangs rather than refusing, that is the security group. If it is
refused immediately, the app is not listening — check `journalctl`.

---

## 10. Point the frontend at it

```
http://<PUBLIC_IP>:8000
```

That is the value for `baseURL` in `frontend/src/api/api.js`, replacing
`http://127.0.0.1:8000`. Frontend work is deliberately out of scope here.

---

## Before this is anything but a demo

- **The public IP changes on stop/start.** Attach an Elastic IP, or the
  frontend's `baseURL` breaks every time the instance is restarted.
- **It is HTTP, not HTTPS.** Two consequences: credentials cross the network
  in the clear, and once the frontend is served over HTTPS the browser will
  block calls to an HTTP backend as mixed content. The fix is nginx in front
  of uvicorn with a certificate, which needs a domain name.
- **CORS is dev-only.** `app/main.py` allows `localhost` origins by a regex.
  The deployed frontend's origin has to be added or every browser request
  fails, even while curl succeeds.
