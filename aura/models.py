from datetime import date, timedelta
from .extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(64), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
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

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'), nullable=False, unique=True)
    received_date = db.Column(db.Date, nullable=False)
    amount_received = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
