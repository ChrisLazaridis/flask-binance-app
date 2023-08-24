from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .models import User

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('something went wrong', category='error')
        else:
            flash('user does not exist', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        binance_key = request.form.get('binanceKey')
        binance_secret = request.form.get('binanceSecret')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email Already Exists', category='error')
        elif len(email) < 4:
            flash('email must be greater than 3 characters', category='error')
        elif len(first_name) < 2:
            flash('first name must be greater than 1 character', category='error')
        elif password1 != password2:
            flash('passwords must match', category='error')
        elif len(password1) < 8:
            flash('password must be at least 8 characters', category='error')
        elif len(binance_key) < 12:
            flash('please enter a valid Binance API Authenticator Key')
        else:
            new_user = User(email=email, first_name=first_name,
                            password=generate_password_hash(password1, method='sha256'), key=binance_key,
                            secret_key=binance_secret, time_created=func.now(), time_updated=func.now())
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('account created!', category='success')
            return redirect(url_for('views.manager'))
    return render_template("sign_up.html", user=current_user)


@auth.route('/edit-account', methods=['GET', 'POST'])
@login_required
def edit_account():
    if request.method == 'POST':
        new_binance_key = request.form.get('binanceKey')
        new_binance_secret = request.form.get('binanceSecret')
        passwordc = request.form.get('passwordc')
        new_password1 = request.form.get('newPassword1')
        new_password2 = request.form.get('newPassword2')

        user = User.query.filter_by(email=current_user.email).first()
        if check_password_hash(user.password, passwordc):
            changed = 0
            if new_password1:
                if new_password1 != new_password2:
                    flash("the two passwords don't match", category='error')
                elif len(new_password1) < 8:
                    flash('password must be at least 8 characters', category='error')
                else:
                    current_user.password = generate_password_hash(new_password1, method='sha256')
                    changed += 1
                    flash('password changes successfully', category='success')
            if new_binance_key:
                if len(new_binance_key) > 12:
                    current_user.key = new_binance_key
                    changed += 1
                    flash('binance API key changed successfully', category='success')
            if new_binance_secret:
                if len(new_binance_secret) > 12:
                    current_user.secret_key = new_binance_secret
                    changed += 1
                    flash('binance API secret key changed successfully', category='success')
        if changed > 0:
            current_user.time_updated = func.now()
            db.session.commit()
        else:
            flash('the password you entered is not correct', category='error')

    return render_template("edit_account.html", user=current_user)
