# Vakansiyalar REST API

FastAPI + PostgreSQL + SQLAlchemy 2.x + Alembic + Pydantic v2 + JWT Bearer.

## Directory tree

```text
app/
├── core/ (config.py, security.py)
├── db/ (session.py)
├── models/ (user.py, job.py, application.py)
├── schemas/ (auth.py, job.py, application.py)
├── routers/ (auth.py, admin.py, jobs.py, applications.py)
├── dependencies.py
└── main.py
alembic/ (env.py, versions/)
scripts/create_admin.py
deploy/ (nginx.conf, job-api.service)
.github/workflows/ci.yml
requirements.txt
.env.example
```

## Install

Python 3.11/3.12 va PostgreSQL 15+ tavsiya qilinadi.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

`.env` ichida `DATABASE_URL` va kamida 32 baytli `JWT_SECRET_KEY` belgilang. Secret yaratish:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

PostgreSQL:

```sql
CREATE USER job_user WITH PASSWORD 'strong-database-password';
CREATE DATABASE job_portal OWNER job_user;
```

## Alembic

Model metadata `alembic/env.py` ga ulangan. Dastlabki migratsiya:

```bash
alembic revision --autogenerate -m "create users jobs applications"
alembic upgrade head
```

Migratsiya faylini deploydan oldin ko'rib chiqing. Keyingi model o'zgarishlari uchun yangi revision yarating va `alembic upgrade head` bajaring.

## Admin

```bash
python -m scripts.create_admin --name "System Admin" --email admin@example.com --password 'Very-Strong-Admin-Password!'
```

Admin candidate'ni employer'ga o'tkazadi: `PATCH /api/v1/admin/users/{user_id}/role`, body `{"role":"employer"}`. Public registration faqat candidate yaratadi.

## Run

```bash
uvicorn app.main:app --reload
```

Swagger: http://127.0.0.1:8000/docs  
ReDoc: http://127.0.0.1:8000/redoc  
OpenAPI: http://127.0.0.1:8000/openapi.json  
Health: http://127.0.0.1:8000/health

Production:

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 2 --bind 127.0.0.1:8000
```

## Endpoints

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/auth/register` | Public; role candidate |
| POST | `/api/v1/auth/login` | Public |
| GET | `/api/v1/auth/me` | Authenticated |
| PATCH | `/api/v1/admin/users/{user_id}/role` | Admin |
| GET | `/api/v1/jobs` | Public, open/non-expired |
| GET | `/api/v1/jobs/{job_id}` | Public, open/non-expired |
| POST | `/api/v1/jobs` | Employer |
| PUT/PATCH | `/api/v1/jobs/{job_id}` | Owning employer |
| DELETE | `/api/v1/jobs/{job_id}` | Owner, no applications |
| PATCH | `/api/v1/jobs/{job_id}/close` | Owner |
| POST | `/api/v1/jobs/{job_id}/apply` | Candidate |
| GET | `/api/v1/applications/my` | Candidate |
| GET | `/api/v1/jobs/{job_id}/applications` | Owner |
| PATCH | `/api/v1/applications/{application_id}/status` | Owner |

List query params: `title`, `job_type`, `requested_salary`, `skip`, `limit`. Salary filter means `salary_min >= requested_salary`.

## Swagger OAuth2

`/docs` da avval `/auth/register` yoki `/auth/login` orqali token oling. **Authorize** tugmasida Bearer token kiriting va protected endpointlarni sinang.

## AWS EC2 + Nginx

1. EC2 Security Group'da faqat kerakli SSH/HTTP/HTTPS portlarini oching; PostgreSQL portini internetga chiqarmang.
2. Loyihani `/opt/vakansiya-api` ga joylang, virtual environment yarating, dependency'larni o'rnating, `.env` ni serverda yarating.
3. `alembic upgrade head` bajaring.
4. `deploy/job-api.service` ni `/etc/systemd/system/job-api.service` ga ko'chiring; `deploy/nginx.conf` ichida domenni o'zgartiring.
5. `sudo systemctl daemon-reload && sudo systemctl enable --now job-api`
6. `sudo nginx -t && sudo systemctl reload nginx`
7. HTTPS uchun Certbot yoki AWS Load Balancer + ACM ishlating.

GitHub Actions workflow compile va smoke-testni bajaradi. Production CD uchun OIDC + AWS SSM/CodeDeploy yoki cheklangan SSH deploy job qo'shing.

## Muhim

- `.env` va secretlarni Git'ga yubormang; HTTPS ishlating.
- PostgreSQL CHECK constraints `0 <= salary_min <= salary_max` ni himoya qiladi.
- `UNIQUE(job_id, candidate_id)` takroriy arizalarni DB darajasida cheklaydi.
- Production release oldidan haqiqiy PostgreSQL bilan integratsion test, rate limiting, monitoring, backup, dependency scanning va migration review qo'shing.

## GitHub Actions CI/CD → AWS EC2

`main` ga push bo'lganda workflow avval PostgreSQL 16 service bilan lint, migratsiya va testlarni bajaradi. Test muvaffaqiyatli bo'lsagina deploy job EC2 ga kodni yuboradi, dependency'larni o'rnatadi, `alembic upgrade head` bajaradi, `job-api` service'ni qayta ishga tushiradi va `/health` ni tekshiradi. Pull request faqat CI/testni bajaradi, deploy qilmaydi.

GitHub repository → **Settings → Secrets and variables → Actions → New repository secret** bo'limida quyidagilarni yarating:

- `EC2_HOST`: EC2 public IPv4 yoki DNS nomi
- `EC2_USERNAME`: odatda Ubuntu AMI uchun `ubuntu`, Amazon Linux uchun `ec2-user`
- `EC2_SSH_KEY`: EC2 ga kiradigan private SSH key'ning to'liq mazmuni

EC2 da oldindan `/opt/vakansiya-api/.env` faylini yarating, PostgreSQL ulanishi va kamida 32 baytli `JWT_SECRET_KEY` kiriting. `job-api.service` systemd service va Nginx konfiguratsiyasini bir marta o'rnating (`deploy/` ichida namunalar bor). Deploy foydalanuvchisiga `/opt/vakansiya-api` ga yozish ruxsati hamda `sudo systemctl restart job-api` va `sudo systemctl is-active job-api` ni parolsiz bajarish huquqi kerak. SSH security group ingress'ini faqat kerakli IP manzillardan oching; 8000 va PostgreSQL portlarini internetga ochmang.

API profil endpointlari: `GET /api/v1/auth/me` (oldingi yo'l) va `GET /api/v1/users/me` (talab qilingan yo'l).
