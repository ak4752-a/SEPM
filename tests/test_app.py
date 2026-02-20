import hashlib
import io
import os
import pytest
from datetime import date, timedelta
from aura import create_app
from aura.extensions import db as _db
from aura.models import User, Contract, Milestone, Payment


@pytest.fixture
def app():
    os.environ['FLASK_ENV'] = 'testing'
    application = create_app('default')
    application.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret',
    })
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    with app.app_context():
        salt = 'testsalt'
        password_hash = hashlib.sha256((salt + 'password').encode()).hexdigest()
        u = User(username='testuser', password_hash=password_hash, salt=salt)
        _db.session.add(u)
        _db.session.commit()
        return u.id


@pytest.fixture
def auth_client(client, user):
    client.post('/login', data={'username': 'testuser', 'password': 'password'})
    return client


@pytest.fixture
def contract(app, user):
    with app.app_context():
        c = Contract(
            user_id=user,
            client_name='Acme Corp',
            contract_name='Project Alpha',
            start_date=date(2024, 1, 1),
            total_value=10000.0,
            payment_term_days=30,
        )
        _db.session.add(c)
        _db.session.commit()
        return c.id


def test_app_creates(app):
    assert app is not None


def test_unauthenticated_redirect(client):
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_login_correct(client, user):
    response = client.post('/login', data={'username': 'testuser', 'password': 'password'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data


def test_login_wrong_password(client, user):
    response = client.post('/login', data={'username': 'testuser', 'password': 'wrongpassword'}, follow_redirects=True)
    assert b'Invalid' in response.data


def test_create_contract(app, auth_client):
    response = auth_client.post('/contracts/new', data={
        'client_name': 'Test Client',
        'contract_name': 'Test Contract',
        'start_date': '2024-01-01',
        'total_value': '5000',
        'payment_term_days': '30',
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        c = Contract.query.filter_by(contract_name='Test Contract').first()
        assert c is not None
        assert c.client_name == 'Test Client'


def test_add_milestone(app, auth_client, contract):
    response = auth_client.post(f'/contracts/{contract}/milestones/new', data={
        'name': 'Milestone 1',
        'planned_delivery_date': '2024-03-01',
        'payment_amount': '2500',
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        m = Milestone.query.filter_by(name='Milestone 1').first()
        assert m is not None
        assert m.payment_amount == 2500.0


def test_delivery_sets_invoice_eligible(app, auth_client, contract):
    with app.app_context():
        m = Milestone(
            contract_id=contract,
            name='M1',
            planned_delivery_date=date(2024, 3, 1),
            payment_amount=1000.0,
        )
        _db.session.add(m)
        _db.session.commit()
        mid = m.id

    response = auth_client.post(f'/milestones/{mid}/deliver', data={
        'actual_delivery_date': '2024-03-01',
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        m = Milestone.query.get(mid)
        assert m.invoice_eligible is True
        assert m.actual_delivery_date == date(2024, 3, 1)


def test_overdue_detection(app, user):
    with app.app_context():
        c = Contract(
            user_id=user,
            client_name='Client',
            contract_name='Contract',
            start_date=date(2020, 1, 1),
            total_value=1000.0,
            payment_term_days=30,
        )
        _db.session.add(c)
        _db.session.commit()
        past_delivery = date.today() - timedelta(days=60)
        m = Milestone(
            contract_id=c.id,
            name='Overdue M',
            planned_delivery_date=past_delivery,
            payment_amount=500.0,
            actual_delivery_date=past_delivery,
            invoice_eligible=True,
        )
        _db.session.add(m)
        _db.session.commit()
        assert m.is_overdue is True
        assert m.overdue_days > 0


def test_dashboard_sums(app, auth_client, user):
    with app.app_context():
        c = Contract(
            user_id=user,
            client_name='Client',
            contract_name='Contract',
            start_date=date(2024, 1, 1),
            total_value=10000.0,
            payment_term_days=30,
        )
        _db.session.add(c)
        _db.session.commit()
        m1 = Milestone(
            contract_id=c.id,
            name='M1',
            planned_delivery_date=date(2024, 2, 1),
            payment_amount=3000.0,
            actual_delivery_date=date(2024, 2, 1),
            invoice_eligible=True,
        )
        m2 = Milestone(
            contract_id=c.id,
            name='M2',
            planned_delivery_date=date(2024, 3, 1),
            payment_amount=2000.0,
            actual_delivery_date=date(2024, 3, 1),
            invoice_eligible=True,
        )
        _db.session.add_all([m1, m2])
        _db.session.commit()
        p = Payment(milestone_id=m1.id, received_date=date(2024, 2, 15), amount_received=3000.0)
        _db.session.add(p)
        _db.session.commit()

    response = auth_client.get('/dashboard')
    assert response.status_code == 200
    assert b'3000' in response.data
    assert b'2000' in response.data


def test_pdf_generation(app, auth_client, user):
    with app.app_context():
        c = Contract(
            user_id=user,
            client_name='PDF Client',
            contract_name='PDF Contract',
            start_date=date(2024, 1, 1),
            total_value=5000.0,
            payment_term_days=30,
        )
        _db.session.add(c)
        _db.session.commit()
        past = date.today() - timedelta(days=45)
        m = Milestone(
            contract_id=c.id,
            name='PDF Milestone',
            planned_delivery_date=past,
            payment_amount=1000.0,
            actual_delivery_date=past,
            invoice_eligible=True,
        )
        _db.session.add(m)
        _db.session.commit()
        mid = m.id

    response = auth_client.get(f'/milestones/{mid}/pdf')
    assert response.status_code == 200
    assert response.content_type == 'application/pdf'
    assert response.data[:4] == b'%PDF'
