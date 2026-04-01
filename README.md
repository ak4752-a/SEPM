# AURA (Automated User Revenue Assistant)

AURA is a self hosted Flask web application for freelancers and small agencies to track client contracts, project milestones, invoices, and payments.
## Live Link (Render)

[Open the app](https://aura-automated-user-revenue-assistant.onrender.com/)

## Features

- **Contract Management** — Create, edit, and delete client contracts with payment terms
- **Milestone Tracking** — Break contracts into milestones with planned delivery dates and payment amounts
- **Invoice Eligibility** — Automatically mark milestones invoice eligible when delivered
- **Delivery Date** — Record actual delivery with any date (including past dates); defaults to today for convenience
- **Overdue Detection** — Automatically highlights overdue payments based on delivery date + payment terms
- **Payment Recording** — Record when payments are received
- **Dashboard** — Summary cards with total received, pending, and overdue amounts
- **PDF Reminders** — Generate professional payment reminder PDFs per milestone (Normal, Overdue, Penalty modes)
- **Single-user** — authentication — Secure SHA-256 password hashing with per user salt.
## Setup

### Prerequisites

- Python 3.9+
- pip

### Install

```bash
git clone https://github.com/ak4752-a/SEPM.git
cd SEPM
pip install -r requirements.txt
```

### Initialize User

```bash
export FLASK_APP=run.py
flask aura init-user <username>
# You will be prompted for a password
```

### Run (Development)

```bash
export FLASK_APP=run.py
flask run
# or
python run.py
```

Navigate to http://localhost:5000

### Run Tests

```bash
pip install pytest
FLASK_APP=run.py python -m pytest tests/ -v
```

## Production Deployment

### Deploying to Render + Supabase

#### 1. Create a Supabase project

1. Sign in at [supabase.com](https://supabase.com) and create a new project.
2. In the Supabase dashboard, go to **Project Settings → Database**.
3. Under **Connection string**, copy the **URI**.  
   It looks like: `postgresql://postgres:PASSWORD@db.XXXX.supabase.co:5432/postgres`

#### 2. Deploy on Render

1. Connect your GitHub repo at [render.com](https://render.com) and create a **New Web Service**.
2. Render will detect `render.yaml` and pre-fill the build/start commands.
3. In **Environment → Environment Variables**, add:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | Your Supabase connection string (from step 1) |
   | `ADMIN_USERNAME` | Your admin username |
   | `ADMIN_PASSWORD` | Your admin password |

   > `SECRET_KEY` and `HTTPS=true` are already set by `render.yaml`.

4. Click **Deploy**. On the first boot, the app will:
   - Create all database tables automatically.
   - Create the admin user from `ADMIN_USERNAME` / `ADMIN_PASSWORD` if it doesn't exist yet.
5. Open the deployed URL and log in with your admin credentials.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key` | Flask session secret — **change in production** |
| `DATABASE_URL` | `sqlite:////tmp/aura.db` | SQLAlchemy database URI (set to Supabase URL in production) |
| `FLASK_ENV` | `default` (production) | `development` or `production` |
| `HTTPS` | `false` | Set to `true` to enable `Secure` + `HttpOnly` session cookies (always set on Render) |
| `ADMIN_USERNAME` | *(unset)* | If set together with `ADMIN_PASSWORD`, the app auto-creates this user on first boot |
| `ADMIN_PASSWORD` | *(unset)* | Password for the auto-created admin user |

## Architecture

```
aura/
├── __init__.py        # App factory (create_app)
├── extensions.py      # SQLAlchemy instance
├── models.py          # User, Contract, Milestone, Payment models
├── cli.py             # flask aura init-user CLI command
└── blueprints/
    ├── auth.py        # Login/logout + login_required decorator
    ├── contracts.py   # Contract CRUD
    ├── milestones.py  # Milestone management (deliver, pay, delete)
    ├── dashboard.py   # Financial summary dashboard
    └── pdf_bp.py      # ReportLab PDF generation
```

### Data Model

- **User** → has many **Contracts**
- **Contract** → has many **Milestones** (with payment_term_days)
- **Milestone** → has one optional **Payment**
- Overdue = `actual_delivery_date + payment_term_days < today` and no payment recorded

## Delivery Flow

On the contract detail page, each undelivered milestone shows a date input (defaulting to today) and a **Deliver** button. You can set any date on or after the contract start date, including past dates.

## PDF Modes

PDF generation buttons appear in the milestone table according to these rules:

| Mode | When available |
|---|---|
| **Normal / Quotation** | Milestone is delivered (`actual_delivery_date` is set) |
| **Overdue** | Milestone is overdue (`due_date < today`) **and** unpaid |
| **Penalty** | Milestone is overdue **and** unpaid **and** penalty is enabled |
