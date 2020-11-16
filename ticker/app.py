__author__ = "Sanket Verma <sanketverma14@gmail.com"
# Purpose: Main application file

from flask import Flask, request, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

engine = create_engine('sqlite:///demo.db')
Session = sessionmaker(bind=engine)


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker_symbol = db.Column(db.String(50))
    avg_buy_price = db.Column(db.Float)
    no_of_shares = db.Column(db.Integer)


db.init_app(app)
db.create_all()


@app.route("/create-portfolio", methods=['POST'])
def create_portfolio() -> Response:
    """
    API to create portfolio

    :return:
        Response: success/failed
    """
    status = "success"
    try:
        portfolio = request.get_json()
        session = Session()
        for trade in portfolio:
            new_trade = Portfolio(ticker_symbol=trade['ticker_symbol'], avg_buy_price=trade['avg_buy_price'],
                                  no_of_shares=trade['no_of_shares'])
            session.add(new_trade)
            session.commit()
        session.close()
        message = "portfolio created successfully"
    except Exception as e:
        status = "failed"
        message = str(e)
    resp = {"status": status, "message": message}

    return jsonify(resp)


@app.route("/add-trades", methods=['PATCH'])
def add_trades() -> Response:
    """
    API to add trades

    :return:
        Response: success/failed
    """
    status = 'success'
    message = ""
    try:
        stock_type = request.args.get("stock_type", None).lower()
        ticker_symbol = request.args.get("ticker_symbol", None)
        new_count = int(request.args.get("count", None))
        new_stock_price = float(request.args.get("new_stock_price", None))
        session = Session()
        db_obj = session.query(Portfolio).filter(Portfolio.ticker_symbol == ticker_symbol)
        current_count = db_obj.first().no_of_shares
        avg_buy_price = db_obj.first().avg_buy_price
        if stock_type == 'buy':
            share_count = current_count + new_count
            new_avg_buy_price = ((avg_buy_price * current_count) + (new_stock_price * new_count)) / share_count
            db_obj.update({Portfolio.avg_buy_price: new_avg_buy_price, Portfolio.no_of_shares: share_count})
            message = "trade bought successfully"
        elif stock_type == 'sell':
            if current_count >= new_count:
                share_count = current_count - new_count
            else:
                raise Exception
            db_obj.update({Portfolio.no_of_shares: share_count})
            message = "trade sold successfully"
        session.commit()
        session.close()
    except Exception as e:
        status = "failed"
        message = str(e)
    resp = {"status": status, "message": message}
    return jsonify(resp)


@app.route("/update-trades", methods=['PATCH'])
def update_trade() -> Response:
    """
    API to update trades

    :return:
        Response: success/failed
    """
    status = "success"
    try:
        update_body = request.get_json()
        session = Session()
        update_object = session.query(Portfolio).filter(
            Portfolio.ticker_symbol == update_body.get('current_ticker_symbol'))
        if update_body.get('new_ticker_symbol'):
            update_object.update({Portfolio.ticker_symbol: update_body.get('new_ticker_symbol')})
        if update_body.get('new_avg_buy_price'):
            update_object.update({Portfolio.avg_buy_price: update_body.get('new_avg_buy_price')})
        if update_body.get('new_no_of_shares'):
            update_object.update({Portfolio.no_of_shares: update_body.get('new_no_of_shares')})
        session.commit()
        session.close()
        message = "trade updated successfully"
    except Exception as e:
        status = 'failed'
        message = str(e)

    resp = {"status": status, "message": message}
    return jsonify(resp)


@app.route("/delete-trades", methods=['DELETE'])
def remove_trade() -> Response:
    """
    API to remove trade

    :return:
        Response: success/failed
    """
    status = "success"
    try:
        ticker_symbol = request.args.get("ticker_symbol", None)
        session = Session()
        get_data_to_delete = session.query(Portfolio).filter(Portfolio.ticker_symbol == ticker_symbol)
        get_data_to_delete.delete()
        session.commit()
        session.close()
        message = "trade deleted successfully"
    except Exception as e:
        status = "failed"
        message = str(e)

    resp = {"status": status, "message": message}
    return jsonify(resp)


@app.route("/fetch-trades", methods=['GET'])
def fetch_trades() -> Response:
    """
    API to fetch trades

    :return:
        Response: trade details
    """
    status = "success"
    trade_data = {}
    try:
        ticker_symbol = request.args.get("ticker_symbol", None)
        session = Session()
        trade = session.query(Portfolio).filter(Portfolio.ticker_symbol == ticker_symbol).first()
        trade_data['ticker_symbol'] = trade.ticker_symbol
        trade_data['avg_buy_price'] = trade.avg_buy_price
        trade_data['no_of_shares'] = trade.no_of_shares
        session.close()
        message = "data fetched successfully"
    except Exception as e:
        status = "failed"
        message = str(e)

    resp = {"status": status, "message": message, "data": trade_data}
    return jsonify(resp)


@app.route("/fetch-portfolio", methods=['GET'])
def fetch_portfolio() -> Response:
    """
    API to fetch Portfolio

    :return:
        Response: complete portfolio
    """
    status = "success"
    portfolio_data = []
    try:
        session = Session()
        portfolio = session.query(Portfolio).all()
        for trade in portfolio:
            portfolio_data.append({'ticker_symbol': trade.ticker_symbol, 'avg_buy_price': trade.avg_buy_price,
                                   'no_of_shares': trade.no_of_shares})
        session.close()
        message = "portfolio fetched successfully"
    except Exception as e:
        status = "failed"
        message = str(e)
    resp = {"status": status, "message": message, "data": portfolio_data}

    return jsonify(resp)


@app.route("/fetch-returns", methods=['GET'])
def fetch_returns() -> Response:
    """
    API to fetch returns

    :return:
        Response:  aggregated results of portfolio
    """
    status = "success"
    returns = 0
    try:
        session = Session()
        portfolio = session.query(Portfolio).all()
        session.close()
        for trade in portfolio:
            returns += (100 - trade.avg_buy_price if trade.avg_buy_price <= 100 else trade.avg_buy_price - 100) * trade.no_of_shares

        message = "returns fetched successfully"
    except Exception as e:
        status = "failed"
        message = str(e)

    resp = {"status": status, "message": message, "data": returns}
    return jsonify(resp)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500)
