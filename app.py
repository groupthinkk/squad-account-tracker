from flask import Flask, make_response, render_template, request, redirect, url_for
import collect_follower_count
import turk_functions
import collect_like_decay
from flask.ext.basicauth import BasicAuth
from hashlib import sha512
import datetime as dt

app = Flask(__name__)
app.secret_key = sha512("cybersec").hexdigest()
app.config['BASIC_AUTH_USERNAME'] = 'groupthinkmanager'
app.config['BASIC_AUTH_PASSWORD'] = 'accounts'

env = app.jinja_env
env.line_statement_prefix = '='

basic_auth = BasicAuth(app)

@app.route('/', methods = ["GET", "POST"])
@basic_auth.required
def index():
    if request.method == "POST":
        if 'account_list' in request.form:
            raw_account_string = request.form['account_list']
            if raw_account_string != "":
                account_list = request.form['account_list'].split(",")
                for account in account_list:
                    collect_follower_count.add_username(account)
        if 'like_account_list' in request.form:
            raw_account_string = request.form['like_account_list']
            if raw_account_string != "":
                account_list = sorted(request.form['like_account_list'].split(","))
                for account in account_list:
                    collect_like_decay.add_username(account)
        elif 'bonus' in request.form:
            worker_id_list = request.form['worker_id_list'].split(",")
            hit_id = request.form['hit_id']
            bonus = float(request.form['bonus'])
            reason = request.form['reason']
            turk_functions.give_bonus(worker_id_list, hit_id, bonus, reason)
        else:
            worker_id_list = request.form['worker_id_list'].split(",")
            subject = request.form['subject']
            message_text = request.form['message_text']
            turk_functions.send_workers_message(worker_id_list, subject, message_text)
    username_list=collect_follower_count.get_account_list()
    return render_template("home.html", username_list=username_list)

@app.route('/downloadcsv', methods = ["GET"])
def download_csv():
    output = collect_follower_count.serve_account_data()
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=account_data_" + str(dt.datetime.now().date()) + ".csv"
    return response

@app.route('/downloadlikecsv', methods = ["GET"])
def download_like_csv():
    output = collect_like_decay.write_data_to_server()
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=like_data_" + str(dt.datetime.now().date()) + ".csv"
    return response

@app.route('/initapikeys', methods = ["GET"])
def init_api_keys():
    collect_like_decay.init_API_queue()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)