from datetime import date, timedelta
from .extensions import db

ALLOWED_CURRENCIES = ('INR', 'USD')

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    password_iterations = db.Column(db.Integer, nullable=False, default=1)
    contracts = db.relationship('Contract', backref='user', lazy=True, cascade='all, delete-orphan')

class Contract(db.Model):
    __tablename__ = 'contracts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    client_name = db.Column(db.String(200), nullable=False)
    contract_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    total_value = db.Column(db.Float, nullable=False)
    payment_term_days = db.Column(db.Integer, nullable=False, default=30)
    currency = db.Column(db.String(3), nullable=False, default='INR')
    created_at = db.Column(db.DateTime, default=db.func.now())
    milestones = db.relationship('Milestone', backref='contract', lazy=True, cascade='all, delete-orphan')

class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    planned_delivery_date = db.Column(db.Date, nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    actual_delivery_date = db.Column(db.Date, nullable=True)
    invoice_eligible = db.Column(db.Boolean, default=False)
    penalty_enabled = db.Column(db.Boolean, default=False, nullable=False)
    penalty_rate_percent = db.Column(db.Float, default=0.0, nullable=False)
    penalty_unit = db.Column(db.String(5), default='day', nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    payment = db.relationship('Payment', backref='milestone', uselist=False, cascade='all, delete-orphan')

    @property
    def due_date(self):
        if self.actual_delivery_date:
            return self.actual_delivery_date + timedelta(days=self.contract.payment_term_days)
        return None

    @property
    def is_overdue(self):
        d = self.due_date
        if d and date.today() > d and not self.payment:
            return True
        return False

    @property
    def overdue_days(self):
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0

    def compute_penalty(self, as_of=None):
        """Return penalty amount as of as_of date (defaults to today).
        Returns 0.0 if penalty not applicable."""
        if not self.penalty_enabled or self.payment:
            return 0.0
        due = self.due_date
        if not due:
            return 0.0
        if as_of is None:
            as_of = date.today()
        days_overdue = max(0, (as_of - due).days)
        if days_overdue == 0:
            return 0.0
        if self.penalty_unit == 'month':
            units = -(-days_overdue // 30)
        else:
            units = days_overdue
        return round(self.payment_amount * (self.penalty_rate_percent / 100) * units, 2)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=False, unique=True)
    received_date = db.Column(db.Date, nullable=False)
    amount_received = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
