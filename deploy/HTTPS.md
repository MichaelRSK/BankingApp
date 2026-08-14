# HTTPS on the EC2 backend

nginx as a reverse proxy in front of uvicorn, with a real Let's Encrypt
certificate. Done on 2026-08-14 against instance `i-07cbc90516580d7b6`.

**Public URL: https://54.80.133.45.nip.io**

---

## Why nip.io

Let's Encrypt will not issue a certificate for a bare IP address, and this
instance has no domain name. `nip.io` resolves any `<ip>.nip.io` straight
back to that address with no DNS records to create, so
`54.80.133.45.nip.io` is a real hostname pointing at the Elastic IP:

```
54.80.133.45.nip.io -> 54.80.133.45
```

That is enough for Let's Encrypt to validate and issue.

**This name is tied to the Elastic IP.** Release or reassign that address and
the hostname stops resolving here, and the certificate must be reissued for
whatever `<newip>.nip.io` replaces it.

---

## What was installed

```bash
sudo dnf install -y nginx certbot python3-certbot-nginx
```

nginx 1.30.4, certbot 2.6.0, both from the Amazon Linux 2023 repos.

`deploy/nginx-bankingapp.conf` documents the resulting config. It is a copy
of what runs at `/etc/nginx/conf.d/bankingapp.conf`; the instance holds the
authoritative version, since certbot edits it in place on renewal.

---

## Security group

Four ports are now open on `sg-01ea3eb28ea21e6a1`:

| Port | Source | Why |
|---|---|---|
| 22 | `71.185.127.9/32` | SSH, restricted to one address |
| 80 | `0.0.0.0/0` | HTTP-01 challenge + redirect to 443 |
| 443 | `0.0.0.0/0` | HTTPS |
| 8000 | `0.0.0.0/0` | direct uvicorn, kept for comparison |

**Port 80 must stay open.** Renewal repeats the HTTP-01 challenge every 60
days, and closing 80 would make the certificate silently fail to renew.

Port 8000 is only still open because the old direct path was worth keeping
for testing. It bypasses TLS entirely, so it should be closed once the
frontend is on HTTPS.

---

## Certificate

```bash
sudo certbot --nginx -d 54.80.133.45.nip.io \
  --non-interactive --agree-tos --register-unsafely-without-email --redirect
```

```
subject = CN=54.80.133.45.nip.io
issuer  = C=US, O=Let's Encrypt, CN=YE2
valid   = Aug 14 2026 -> Nov 12 2026
```

`--register-unsafely-without-email` was used deliberately: no address was
registered with Let's Encrypt for a certificate that dies with the lab. The
cost is no expiry warning emails, which do not matter here but would on a
real deployment — use `-m you@example.com` there.

`--redirect` is what generated the port 80 -> 443 redirect block.

### Auto-renewal — needed a manual fix

certbot reports "Certbot has set up a scheduled task to automatically renew
this certificate in the background". **On Amazon Linux 2023 that is
misleading.** The package ships `certbot-renew.timer` in a *disabled* state,
and `crond` is not running either, so nothing would have renewed anything:

```bash
systemctl is-enabled certbot-renew.timer   # disabled
```

Enabled explicitly:

```bash
sudo systemctl enable --now certbot-renew.timer
```

A deploy hook was also added, because nginx keeps the old certificate in
memory after certbot replaces the file on disk. Without the reload, a
renewed certificate is not actually served:

```bash
# /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
#!/bin/sh
systemctl reload nginx
```

Verified with a full dry run:

```
Congratulations, all simulated renewals succeeded:
  /etc/letsencrypt/live/54.80.133.45.nip.io/fullchain.pem (success)
```

---

## CORS

`/etc/bankingapp/env` now carries all three origins:

```
CORS_ALLOWED_ORIGINS=http://54.80.133.45,http://54.80.133.45:8000,https://54.80.133.45.nip.io
```

Reading these from the environment rather than the source means adding the
CloudFront origin later is a config change and a restart, not a code change:

```bash
sudo sed -i 's#^CORS_ALLOWED_ORIGINS=.*#CORS_ALLOWED_ORIGINS=http://54.80.133.45,http://54.80.133.45:8000,https://54.80.133.45.nip.io,https://YOUR.cloudfront.net#' /etc/bankingapp/env
sudo systemctl restart bankingapp
```

---

## Verified from outside AWS

All run from a developer machine, not from on the instance:

| Check | Result |
|---|---|
| `GET https://54.80.133.45.nip.io/docs` | **200**, `ssl_verify_result=0` (trusted, no `-k`) |
| `POST /api/v1/login` bad creds over HTTPS | **401** |
| `http://54.80.133.45.nip.io/docs` | **301** -> `https://.../docs` |
| `http://54.80.133.45.nip.io:8000/docs` | **200** (direct path still up) |
| Full round trip over HTTPS | register **201**, login returns a token, authed `/branches/BR001/metrics` **200** |
| CORS `https://54.80.133.45.nip.io` | allowed |
| CORS `http://localhost:5173` | allowed (local dev intact) |
| CORS `http://evil.example.com` | denied |

---

## Frontend

```
baseURL: https://54.80.133.45.nip.io
```

No port. nginx listens on 443 and proxies to 8000 internally.

This is what unblocks a CloudFront-hosted frontend: an HTTPS page cannot call
an HTTP backend, because browsers block it as mixed content regardless of
CORS. `http://54.80.133.45:8000` would have failed for that reason alone.

---

## This is all temporary

The instance, the Elastic IP, the certificate, the nginx config and the
`/etc/bankingapp/env` secrets are all inside a Qwiklabs sandbox and are
deleted when the lab session ends. The certificate is valid for 90 days but
the machine holding it will not last the day.

Nothing here survives to a real deployment except the shape of the setup.
For anything permanent, use a real domain rather than nip.io, register a
contact address with Let's Encrypt so expiry warnings arrive, and close port
8000.
