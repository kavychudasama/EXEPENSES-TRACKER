# pyright: reportMissingImports=false

from flask import Flask, request, jsonify, send_file
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

FILE_NAME = "expenses.json"


# =========================================================
# LOAD EXPENSES
# =========================================================

def load_expenses():

    if not os.path.exists(FILE_NAME):
        return []

    try:

        with open(FILE_NAME, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("expenses", [])

    except (json.JSONDecodeError, FileNotFoundError):

        return []


# =========================================================
# SAVE EXPENSES
# =========================================================

def save_expenses(expenses):

    data = {
        "expenses": expenses
    }

    with open(FILE_NAME, "w", encoding="utf-8") as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return send_file("index.html")


# =========================================================
# GET ALL EXPENSES
# =========================================================

@app.route("/expenses", methods=["GET"])
def get_expenses():

    expenses = load_expenses()

    return jsonify(expenses)


# =========================================================
# ADD EXPENSE
# =========================================================

@app.route("/expenses", methods=["POST"])
def add_expense():

    data = request.get_json() or {}

    category = data.get("category", "").strip()
    note = data.get("note", "").strip()
    expense_date = data.get("date", "").strip()

    # -------------------------
    # AMOUNT
    # -------------------------

    try:

        amount = float(data.get("amount"))

    except (TypeError, ValueError):

        return jsonify({
            "error": "Invalid amount."
        }), 400

    # -------------------------
    # CATEGORY
    # -------------------------

    if category == "":

        return jsonify({
            "error": "Category is required."
        }), 400

    # -------------------------
    # AMOUNT CHECK
    # -------------------------

    if amount <= 0:

        return jsonify({
            "error": "Amount must be greater than 0."
        }), 400

    # -------------------------
    # DATE
    # -------------------------

    if expense_date == "":

        expense_date = datetime.now().strftime("%Y-%m-%d")

    try:

        selected_date = datetime.strptime(
            expense_date,
            "%Y-%m-%d"
        ).date()

        today = datetime.now().date()

    except ValueError:

        return jsonify({
            "error": "Invalid date."
        }), 400

    # -------------------------
    # FUTURE DATE CHECK
    # -------------------------

    if selected_date > today:

        return jsonify({
            "error": "Future dates are not allowed."
        }), 400

    # -------------------------
    # LOAD
    # -------------------------

    expenses = load_expenses()

    # -------------------------
    # CREATE ID
    # -------------------------

    if expenses:

        new_id = max(
            int(expense["id"])
            for expense in expenses
        ) + 1

    else:

        new_id = 1

    # -------------------------
    # NEW EXPENSE
    # -------------------------

    new_expense = {

        "id": new_id,

        "category": category,

        "amount": amount,

        "note": note,

        "date": expense_date

    }

    expenses.append(new_expense)

    save_expenses(expenses)

    return jsonify(new_expense), 201


# =========================================================
# EDIT EXPENSE
# =========================================================

@app.route(
    "/expenses/<int:expense_id>",
    methods=["PUT"]
)
def edit_expense(expense_id):

    data = request.get_json() or {}

    category = data.get("category", "").strip()
    note = data.get("note", "").strip()
    expense_date = data.get("date", "").strip()

    # -------------------------
    # AMOUNT
    # -------------------------

    try:

        amount = float(data.get("amount"))

    except (TypeError, ValueError):

        return jsonify({
            "error": "Invalid amount."
        }), 400

    # -------------------------
    # CATEGORY
    # -------------------------

    if category == "":

        return jsonify({
            "error": "Category is required."
        }), 400

    # -------------------------
    # AMOUNT
    # -------------------------

    if amount <= 0:

        return jsonify({
            "error": "Amount must be greater than 0."
        }), 400

    # -------------------------
    # DATE
    # -------------------------

    try:

        selected_date = datetime.strptime(
            expense_date,
            "%Y-%m-%d"
        ).date()

        today = datetime.now().date()

    except ValueError:

        return jsonify({
            "error": "Invalid date."
        }), 400

    # -------------------------
    # FUTURE DATE
    # -------------------------

    if selected_date > today:

        return jsonify({
            "error": "Future dates are not allowed."
        }), 400

    expenses = load_expenses()

    # -------------------------
    # FIND EXPENSE
    # -------------------------

    for expense in expenses:

        if int(expense["id"]) == expense_id:

            expense["category"] = category
            expense["amount"] = amount
            expense["note"] = note
            expense["date"] = expense_date

            save_expenses(expenses)

            return jsonify({
                "message": "Expense updated successfully."
            })

    return jsonify({
        "error": "Expense not found."
    }), 404


# =========================================================
# DELETE EXPENSE
# =========================================================

@app.route(
    "/expenses/<int:expense_id>",
    methods=["DELETE"]
)
def delete_expense(expense_id):

    expenses = load_expenses()

    new_expenses = [

        expense

        for expense in expenses

        if int(expense["id"]) != expense_id

    ]

    # Nothing was deleted

    if len(new_expenses) == len(expenses):

        return jsonify({
            "error": "Expense not found."
        }), 404

    # Actually update JSON

    save_expenses(new_expenses)

    return jsonify({
        "message": "Expense deleted successfully."
    })


# =========================================================
# DASHBOARD SUMMARY
# =========================================================

@app.route(
    "/dashboard",
    methods=["GET"]
)
def dashboard():

    expenses = load_expenses()

    total = 0

    categories = set()

    for expense in expenses:

        total += float(
            expense.get("amount", 0)
        )

        categories.add(
            expense.get("category", "")
        )

    return jsonify({

        "total": total,

        "count": len(expenses),

        "categories": len(categories)

    })


# =========================================================
# ALL DAYS ANALYTICS
# =========================================================

@app.route(
    "/analytics/all-days",
    methods=["GET"]
)
def all_days_analytics():

    expenses = load_expenses()

    daily_totals = {}

    for expense in expenses:

        date = expense.get("date")

        if not date:
            continue

        amount = float(
            expense.get("amount", 0)
        )

        if date not in daily_totals:

            daily_totals[date] = 0

        daily_totals[date] += amount

    result = []

    for date in sorted(daily_totals.keys()):

        date_object = datetime.strptime(
            date,
            "%Y-%m-%d"
        )

        result.append({

            "date": date,

            "day": date_object.strftime("%a"),

            "day_number": date_object.strftime("%d"),

            "total": daily_totals[date]

        })

    return jsonify(result)


# =========================================================
# SELECTED DAY - CATEGORY ANALYTICS
# =========================================================

@app.route(
    "/analytics/day/<date>",
    methods=["GET"]
)
def day_analytics(date):

    try:

        selected_date = datetime.strptime(
            date,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        return jsonify({
            "error": "Invalid date."
        }), 400

    expenses = load_expenses()

    category_totals = {}

    day_expenses = []

    for expense in expenses:

        if expense.get("date") == date:

            amount = float(
                expense.get("amount", 0)
            )

            category = expense.get(
                "category",
                "Other"
            )

            if category not in category_totals:

                category_totals[category] = 0

            category_totals[category] += amount

            day_expenses.append(expense)

    categories = []

    for category, total in category_totals.items():

        categories.append({

            "category": category,

            "total": total

        })

    total = sum(
        item["total"]
        for item in categories
    )

    return jsonify({

        "date": date,

        "formatted_date":
            selected_date.strftime(
                "%d %B %Y"
            ),

        "total": total,

        "count": len(day_expenses),

        "categories": categories,

        "expenses": day_expenses

    })


# =========================================================
# LAST 3 WEEKS (21 DAYS)
# =========================================================

@app.route(
    "/expenses/3weeks",
    methods=["GET"]
)
def three_weeks():
    """
    Returns the last 21 days (3 full weeks) of daily
    spending totals, oldest first, newest (today) last.
    """

    expenses = load_expenses()

    today = datetime.now().date()

    DAYS_TO_SHOW = 21  # 3 weeks

    days = []

    for i in range(DAYS_TO_SHOW - 1, -1, -1):

        current_date = (
            today -
            timedelta(days=i)
        )

        date_string = current_date.strftime(
            "%Y-%m-%d"
        )

        total = 0

        count = 0

        for expense in expenses:

            if expense.get("date") == date_string:

                total += float(
                    expense.get(
                        "amount",
                        0
                    )
                )

                count += 1

        days.append({

            "date": date_string,

            "day":
                current_date.strftime("%a"),

            "day_number":
                current_date.strftime("%d"),

            "total":
                total,

            "count":
                count

        })

    weekly_total = sum(
        day["total"]
        for day in days
    )

    weekly_count = sum(
        day["count"]
        for day in days
    )

    return jsonify({

        "days": days,

        "total":
            weekly_total,

        "count":
            weekly_count

    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    if not os.path.exists(FILE_NAME):

        save_expenses([])

    app.run(
        debug=True
    )