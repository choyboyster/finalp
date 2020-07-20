import os
import psycopg2

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
##app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

import sqlalchemy
# Configure CS50 Library to use SQLite database
db = SQL("postgres://hcpqudqiyyqbpv:2d315abf96a6615193c736e99205e869ca8e51f142e940517aa51109dbaab6fa@ec2-34-192-173-173.compute-1.amazonaws.com:5432/dfe1jmmdi0ojfu")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    return redirect("/inventory")



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():

    if request.method == "POST":

        # Ensure Form is Filled
        if not request.form.get("tooth"):
            return apology("Missing Tooth")

        elif not request.form.get("quantity"):
            return apology("Missing Quantity")

        # Ensure if Valid Tooth
        rows = db.execute("SELECT * FROM inventory WHERE tooth = :tooth",
                          tooth=request.form.get("tooth")).fetchall()
    
        if len(rows) != 1:
            return apology("Incorrect Tooth Imput")

        cost = 4 * int(request.form.get("quantity"))

        # Add into History Logs


        # Update Inventory Log
        current_inventory = db.execute("SELECT stock FROM inventory WHERE tooth=:tooth", tooth=request.form.get("tooth")).fetchall()

        new_inventory = current_inventory[0]["stock"] - int(request.form.get("quantity"))

        if new_inventory > -1:
            db.execute("UPDATE inventory SET stock=:stock WHERE tooth=:tooth",
                        stock=new_inventory,
                        tooth=request.form.get("tooth"))

            db.execute("INSERT INTO history (user_id, tooth, quantity, cost) VALUES(:user_id, :tooth, :quantity, :cost)",
                   user_id=session["user_id"],
                   tooth=request.form.get("tooth"),
                   quantity=request.form.get("quantity"),
                   cost=cost)
            db.commit()

        else:
            return apology("Sorry! Out of Teeth!", 403)

        return redirect("/")

    else:
        return render_template("buy.html")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    history = db.execute("SELECT * FROM history WHERE user_id= :id ORDER BY id DESC", id= session["user_id"]).fetchall()
    return render_template("history.html", histories = history)

@app.route("/acknowledged", methods=["GET", "POST"])
@login_required
def acknowledged():
    """Show history of transactions"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure transaction id was submitted
        if not request.form.get("id"):
            return apology("must provide transaction id", 403)

        # Query database for transaction id
        rows = (db.execute("SELECT * FROM history WHERE user_id = :user_id AND id = :id",
                          id=request.form.get("id"),
                          user_id=session["user_id"])).fetchall()

        # Ensure transaction id exists and password is correct
        if len(rows) != 1:
            return apology("invalid transaction id", 403)

        else:
            db.execute("UPDATE history SET acknowledged= 'YES' WHERE id = :id",
                          id=request.form.get("id"))
            db.commit()

        # Redirect user to home page
        return render_template("success.html")

    else:

        return render_template("acknowledged.html")



@app.route("/add", methods=["GET", "POST"])
@login_required
def add():

    if request.method == "POST":

        # Ensure Form is Filled
        if not request.form.get("tooth"):
            return apology("Missing Tooth")

        elif not request.form.get("quantity"):
            return apology("Missing Quantity")

        # Ensure if Valid Tooth
        rows = db.execute("SELECT * FROM inventory WHERE tooth = :tooth",
                          tooth=request.form.get("tooth")).fetchall()
        if len(rows) != 1:
            return apology("Incorrect Tooth Imput")

        # Check if is an admin
        rows = db.execute("SELECT * FROM users WHERE id = :user_id AND username = 'admin'",
                          user_id=session["user_id"]).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1:
            return apology("admin function only!", 403)


        # Update Inventory Log
        current_inventory = db.execute("SELECT stock FROM inventory WHERE tooth=:tooth", tooth=request.form.get("tooth")).fetchall()

        new_inventory = current_inventory[0]["stock"] + int(request.form.get("quantity"))

        if new_inventory > -1:
            db.execute("UPDATE inventory SET stock=:stock WHERE tooth=:tooth",
                        stock=new_inventory,
                        tooth=request.form.get("tooth"))
            db.commit()

        else:
            return apology("Sorry! Inventory cannot be less than zero", 403)

        return redirect("/")

    else:
        return render_template("add.html")



@app.route("/totalhist")
@login_required
def totalhist():
    """Show history of transactions"""

    history = db.execute("SELECT users.reg, users.name, users.grouping, history.tooth, history.quantity, history.cost, history.time_stamp, history.id, history.acknowledged FROM users JOIN history ON users.id = history.user_id ORDER BY history.id DESC").fetchall()
    return render_template("totalhist.html", histories = history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username")).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/inventory")
@login_required
def quote():
    """Show Inventory"""

    if request.method == "GET":

        list = []
        for i in range(11,18):
            a = db.execute("SELECT stock FROM inventory WHERE tooth = :tooth", tooth = i)
            list.append(a[0]["stock"]).fetchall()

        pist = []
        for i in range(21,28):
            a = db.execute("SELECT stock FROM inventory WHERE tooth = :tooth", tooth = i)
            pist.append(a[0]["stock"]).fetchall()

        gist = []
        for i in range(31,38):
            a = db.execute("SELECT stock FROM inventory WHERE tooth = :tooth", tooth = i)
            gist.append(a[0]["stock"]).fetchall()

        tist = []
        for i in range(41,48):
            a = db.execute("SELECT stock FROM inventory WHERE tooth = :tooth", tooth = i)
            tist.append(a[0]["stock"]).fetchall()

        return render_template("inventory.html", list=list, pist=pist, gist=gist, tist=tist)


@app.route("/register", methods=["GET", "POST"])
def register():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure reg was submitted
        if not request.form.get("reg"):
            return apology("must provide register number", 403)

        # Ensure name was submitted
        if not request.form.get("name"):
            return apology("must provide full name", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure group number was submitted
        if not request.form.get("group"):
            return apology("must provide group number", 403)

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        # Ensure passwords match
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("password must be the same", 403)

        # Add Register into SQL DB
        result = db.execute("INSERT INTO users (username, hash, reg, grouping, name) VALUES (:username, :hash, :reg, :group, :name)", username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")), reg=request.form.get("reg"), group=request.form.get("group"), name=request.form.get("name"))
        db.commit()
        if not result:
            return apology("Username Taken", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username")).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in.
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        # Ensure passwords match
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("password must be the same", 403)

        # Add Register into SQL DB
        db.execute("UPDATE users SET hash=:hash WHERE id=:id", id=session["user_id"], hash=generate_password_hash(request.form.get("password")))
        db.commit()

        # Redirect user to home page
        return render_template("password2.html", name=request.form.get("username"), password=request.form.get("password"))


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("password.html")

@app.route("/summary", methods=["GET", "POST"])
@login_required
def summary():
    if request.method == "GET":

        list = []
        for i in range(11,18):
            a = db.execute("SELECT sum(quantity) FROM history WHERE time_stamp = CURRENT_DATE AND tooth=:tooth", tooth=i)
            list.append(a[0]["sum(quantity)"]).fetchall()

        pist = []
        for i in range(21,28):
            a = db.execute("SELECT sum(quantity) FROM history WHERE time_stamp = CURRENT_DATE AND tooth=:tooth", tooth=i)
            pist.append(a[0]["sum(quantity)"]).fetchall()

        gist = []
        for i in range(31,38):
            a = db.execute("SELECT sum(quantity) FROM history WHERE time_stamp = CURRENT_DATE AND tooth=:tooth", tooth=i)
            gist.append(a[0]["sum(quantity)"]).fetchall()

        tist = []
        for i in range(41,48):
            a = db.execute("SELECT sum(quantity) FROM history WHERE time_stamp = CURRENT_DATE AND tooth=:tooth", tooth=i)
            tist.append(a[0]["sum(quantity)"]).fetchall()

        return render_template("summary.html", list=list, pist=pist, gist=gist, tist=tist)

    else:
        return render_template("summary.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
    
if __name__ == "__main__":
     port = int(os.environ.get("PORT", 8080))
     app.run(host="0.0.0.0", port=port)
