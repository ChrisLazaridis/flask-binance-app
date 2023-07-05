from flask import Blueprint , render_template , request , flash , redirect , url_for
from flask_login import login_required , current_user
from . import db
import json
from binance.client import Client
from binance.exceptions import BinanceAPIException
import datetime
import pytz
from .models import User

views = Blueprint ( 'views' , __name__ )

SYMBOLS = [ 'BTC' , 'ETH' , 'USDT' , 'ADA' , 'XRP' ]
DURATION_OPTIONS = [ '1 month' , '3 months' , '6 months' , '9 months' , '12 months' , 'Lifetime' ]


class BinanceAPI:
    def __init__(self, key, secret_key):
        self.client = Client(key, secret_key)

    def get_account_info(self):
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            print(str(e))
            return None

    def get_my_trades(self, symbol, start_time):
        try:
            return self.client.get_my_trades(symbol=symbol, startTime=start_time)
        except BinanceAPIException as e:
            print(str(e))
            return None

def validate_inputs(duration, symbol_pair):
    if symbol_pair not in [f"{s1}{s2}" for s1 in SYMBOLS for s2 in SYMBOLS if s1 != s2]:
        print("Invalid symbol pair selected")
        return False
    if duration not in DURATION_OPTIONS:
        print("Invalid duration selected")
        return False
    else:
        return True

def calculate_stats(trades):
    total_profit = 0
    total_wins = 0
    total_losses = 0
    total_win_amount = 0
    total_loss_amount = 0
    for trade in trades:
        if trade['isBuyer']:
            profit = float(trade['quoteQty']) - float(trade['quoteQty']) * float(trade['commission']) / 100
        else:
            profit = float(trade['quoteQty']) + float(trade['quoteQty']) * float(trade['commission']) / 100
        total_profit += profit
        if profit > 0:
            total_wins += 1
            total_win_amount += profit
        else:
            total_losses += 1
            total_loss_amount += profit
    if total_wins > 0:
        win_ratio = total_wins / (total_wins + total_losses) * 100
        avg_win = total_win_amount / total_wins
    else:
        win_ratio = 0
        avg_win = 0
    if total_losses > 0:
        avg_loss = total_loss_amount / total_losses
    else:
        avg_loss = 0
    return {'total_profit': total_profit, 'total_wins': total_wins, 'total_losses': total_losses,
            'win_ratio': win_ratio, 'avg_win': avg_win, 'avg_loss': avg_loss}
@views.route('/manager', methods=['GET', 'POST'])
@login_required
def manager():
    if request.method == 'POST':
        symbol_pair = request.form.get('symbol_pair')
        duration = request.form.get('duration')
        if symbol_pair == "-":
            flash('Please select a symbol pair', category='error')
            return redirect(url_for('views.manager'))
        if duration == "-":
            flash('Please select a duration', category='error')
            return redirect(url_for('views.manager'))
        if not validate_inputs(duration, symbol_pair):
            flash('you do not have sufficient data for the selected symbol and time scope', category='error')
            return redirect(url_for('views.manager'))
        else:
            binance_api = BinanceAPI(current_user.key, current_user.secret_key)
            account_info = binance_api.get_account_info()
            if not account_info:
                return redirect(url_for('views.home'))
                print("Invalid API key or secret key")

            balances = {}
            for balance in account_info['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                if free > 0 or locked > 0:
                    balances[asset] = free + locked

            if duration == '1 month':
                end_time = datetime.datetime.now(pytz.utc)
                start_time = end_time - datetime.timedelta(days=30)
            elif duration == '3 months':
                end_time = datetime.datetime.now(pytz.utc)
                start_time = end_time - datetime.timedelta(days=90)
            elif duration == '6 months':
                end_time = datetime.datetime.now(pytz.utc)
                start_time = end_time - datetime.timedelta(days=180)
            elif duration == '9 months':
                end_time = datetime.datetime.now(pytz.utc)
                start_time = end_time - datetime.timedelta(days=270)
            elif duration == '12 months':
                end_time = datetime.datetime.now(pytz.utc)
                start_time = end_time - datetime.timedelta(days=360)
            elif duration == 'Lifetime':
                start_time = None
                end_time = None

            trades = []
            if symbol_pair and start_time and end_time:
                trades = binance_api.get_my_trades(symbol_pair, int(start_time.timestamp() * 1000))
                trades = [trade for trade in trades if
                          start_time.timestamp() * 1000 <= trade['time'] <= end_time.timestamp() * 1000]
            elif symbol_pair:
                trades = binance_api.get_my_trades(symbol_pair, start_time)

            stats = calculate_stats(trades)

            return render_template('stats.html', balances=balances, trades=trades, stats=stats, duration=duration,
                                   symbol_pair=symbol_pair, user=current_user, symbols=SYMBOLS,
                                   duration_options=DURATION_OPTIONS)

    if request.method == 'GET':
        return render_template('manager.html', symbols=SYMBOLS, duration_options=DURATION_OPTIONS, user=current_user)





@views.route('/equity', methods=['GET', 'POST'])
@login_required
def equity():
    # Retrieve the user's Binance API credentials from the database
    user = User.query.filter_by(email=current_user.email).first()
    api_key = user.key
    secret_key = user.secret_key

    # Create a Binance client using the API credentials
    client = Client(api_key, secret_key)

    # Retrieve the user's Binance wallet balances
    balances = client.get_account()['balances']

    # Filter out balances with zero balance and no usd value
    balances = [b for b in balances if float(b['free']) + float(b['locked']) > 0 and b['asset'] != 'USDT']
    for b in balances:
        symbol = b['asset'] + 'USDT'
        ticker = client.get_symbol_ticker(symbol=symbol)
        if ticker is None:
            b['usd_value'] = 'N/A'
        else:
            b['usd_value'] = '{:.2f}'.format(float(ticker['price']) * float(b['free']) + float(ticker['price']) * float(b['locked']))

    # Sort balances by USD value
    balances = sorted(balances, key=lambda x: float(x['usd_value']), reverse=True)

    return render_template('equity.html', balances=balances, user=current_user)
@views.route('/', methods =['GET'])
def home():
    return render_template('home.html', user=current_user)
