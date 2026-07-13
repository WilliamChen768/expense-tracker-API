from flask import Flask
from flask import request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses.db"

db = SQLAlchemy(app)

def token_required(original_function):
    @wraps(original_function)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if auth_header is None or not auth_header.startswith("Bearer "):
            return {"message": "Token is missing"}, 401
        
        token = auth_header.split(" ")[1]
        try:
            decoded = jwt.decode(token, "some-secret-key", algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return {"message": "Token is invalid"}, 401
        
        return original_function(decoded["user_id"], *args, **kwargs)
    return wrapper

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(200), unique=False, nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

@app.route("/")
def home():
    return "Hello World"

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    hashed = generate_password_hash(data["password"])

    new_user = User(username=data["username"], password=hashed)
    db.session.add(new_user)
    db.session.commit()

    return {"message": "User created successfully"}, 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()
    if user is None:
        return {"message": "Username does not exist"}, 404

    if not check_password_hash(user.password, data["password"]):
        return {"message": "Incorrect password"}, 401

    token = jwt.encode({"user_id": user.id}, "some-secret-key", algorithm="HS256")
    return {"token": token}



@app.route("/expenses", methods=["POST"])
@token_required
def add_expense(user_id):
    data = request.get_json()
    try:
        parsed_date = datetime.strptime(data["date"], "%Y-%m-%d")
    except ValueError:
        return {"message": "Invalid date format, expected YYYY-MM-DD"}, 400

    new_expense = Expense(
        amount=data["amount"],
        category=data["category"],
        description=data["description"],
        date=parsed_date,
        user_id=user_id
    )
    db.session.add(new_expense)
    db.session.commit()

    return {"message": "Expense created successfully"}, 201

@app.route("/expenses", methods=["GET"])
@token_required
def list_expenses(user_id):
    filter_type = request.args.get("filter")
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    three_months_ago = now - timedelta(days=90)
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    
    if filter_type == "week":
        expenses = Expense.query.filter(Expense.user_id==user_id, Expense.date >= week_ago).all()
    elif filter_type == "month":
        expenses = Expense.query.filter(Expense.user_id==user_id, Expense.date >= month_ago).all()
    elif filter_type == "three-months":
        expenses = Expense.query.filter(Expense.user_id==user_id, Expense.date >= three_months_ago).all()
    elif filter_type == "custom":
        if start_str is None or end_str is None:
            return {"message": "Custom filter requires both start and end dates"}, 400
        try:
            parsed_start = datetime.strptime(start_str, "%Y-%m-%d")
            parsed_end = datetime.strptime(end_str, "%Y-%m-%d")
        except ValueError:
            return {"message": "Invalid date format, expected YYYY-MM-DD"}, 400
        expenses = Expense.query.filter(Expense.user_id == user_id, Expense.date >= parsed_start, Expense.date <= parsed_end).all()
    elif filter_type == None:
        expenses = Expense.query.filter_by(user_id=user_id).all()
    else:
        return {"message": "Invalid filter type"}, 400

    result = []
    for expense in expenses:
        result.append({
            "id": expense.id,
            "amount": expense.amount,
            "category": expense.category,
            "description": expense.description,
            "date": expense.date.isoformat()
        })
    return {"expenses": result}

@app.route("/expenses/<int:expense_id>", methods=["PUT"])
@token_required
def update_expense(user_id, expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
    if expense is None:
        return {"message": "Expense not found"}, 404

    data = request.get_json()
    try:
        parsed_date = datetime.strptime(data["date"], "%Y-%m-%d")
    except ValueError:
        return {"message": "Invalid date format, expected YYYY-MM-DD"}, 400
    
    expense.amount = data["amount"]
    expense.category = data["category"]
    expense.description = data["description"]
    expense.date = parsed_date

    db.session.commit()
    return {"message": "Expense updated successfully"}

@app.route("/expenses/<int:expense_id>", methods=["DELETE"])
@token_required
def delete_expense(user_id, expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
    if expense is None:
        return {"message": "Expense not found"}, 404
    
    db.session.delete(expense)
    db.session.commit()
    return {"message": "Expense deleted successfully"}



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)