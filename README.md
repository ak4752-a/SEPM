# AURA — Automated User Revenue Assistant

AURA is a self-hosted Flask web application for freelancers and small agencies to track contracts, milestones, invoicing, and payments in one place.

## Features

- **Contract Management** — Create, edit, and delete client contracts with payment terms
- **Milestone Tracking** — Break contracts into milestones with planned delivery dates and payment amounts
- **Invoice Eligibility** — Automatically mark milestones invoice-eligible when delivered
- **Delivery Date** — Record actual delivery with any date (including past dates); defaults to today for convenience
- **Overdue Detection** — Automatically highlights overdue payments based on delivery date + payment terms
- **Payment Recording** — Record when payments are received
- **Dashboard** — Summary cards with total received, pending, and overdue amounts
- **PDF Reminders** — Generate professional payment reminder PDFs per milestone (Normal, Overdue, Penalty modes)
- **Single-user** — Secure SHA-256 password hashing with per-user salt

## Setup

### Prerequisites

- Python 3.9+
- pip

### Install

```bash
git clone <repo-url>
cd <repo-name>
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

### Using Gunicorn + Nginx

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
```

Configure Nginx to proxy to port 8000 and handle SSL termination.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-change-in-production` | Flask session secret — **change in production** |
| `DATABASE_URL` | `sqlite:///aura.db` | SQLAlchemy database URI |
| `FLASK_ENV` | `default` | `development` or `production` |
| `HTTPS` | `false` | Set to `true` to enable secure session cookies |

### Security Notes

- Set a strong random `SECRET_KEY` in production
- Set `HTTPS=true` when running behind HTTPS to enable `Secure` cookies
- Use PostgreSQL in production instead of SQLite for better concurrency

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
