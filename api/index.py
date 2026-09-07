from flask import Flask, request, jsonify
from supabase import create_client
from datetime import datetime, timedelta
import os

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_expenses():
    response = (
        supabase
        .table("expenses")
        .select("*")
        .order("id")
        .execute()
    )

    return response.data or []


@app.route("/expenses", methods=["GET"])
def expenses_get():
    try:
        return jsonify(get_expenses())
    except Exception as error:
        print(error)
        return jsonify({"error": "Could not load expenses."}), 500


@app.route("/expenses", methods=["POST"])
def expenses_post():

    data = request.get_json() or {}

    category = str(data.get("category", "")).strip()
    note = str(data.get("note", "")).strip()
    expense_date = str(data.get("date", "")).strip()

    try:
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount."}), 400

    if not category:
        return jsonify({"error": "Category is required."}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0."}), 400

    if not expense_date:
        expense_date = datetime.now().strftime("%Y-%m-%d")

    try:
        selected_date = datetime.strptime(
            expense_date,
            "%Y-%m-%d"
        ).date()
    except ValueError:
        return jsonify({"error": "Invalid date."}), 400

    if selected_date > datetime.now().date():
        return jsonify({"error": "Future dates are not allowed."}), 400

    try:
        result = (
            supabase
            .table("expenses")
            .insert({
                "category": category,
                "amount": amount,
                "note": note,
                "date": expense_date
            })
            .execute()
        )

        return jsonify(result.data[0]), 201

    except Exception as error:
        print(error)
        return jsonify({"error": "Could not add expense."}), 500


@app.route("/expenses/<int:expense_id>", methods=["PUT"])
def edit_expense(expense_id):

    data = request.get_json() or {}

    category = str(data.get("category", "")).strip()
    note = str(data.get("note", "")).strip()
    expense_date = str(data.get("date", "")).strip()

    try:
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid amount."}), 400

    if not category:
        return jsonify({"error": "Category is required."}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0."}), 400

    try:
        selected_date = datetime.strptime(
            expense_date,
            "%Y-%m-%d"
        ).date()
    except ValueError:
        return jsonify({"error": "Invalid date."}), 400

    if selected_date > datetime.now().date():
        return jsonify({"error": "Future dates are not allowed."}), 400

    try:
        result = (
            supabase
            .table("expenses")
            .update({
                "category": category,
                "amount": amount,
                "note": note,
                "date": expense_date
            })
            .eq("id", expense_id)
            .execute()
        )

        if not result.data:
            return jsonify({"error": "Expense not found."}), 404

        return jsonify(result.data[0])

    except Exception as error:
        print(error)
        return jsonify({"error": "Could not update expense."}), 500


@app.route("/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):

    try:
        existing = (
            supabase
            .table("expenses")
            .select("id")
            .eq("id", expense_id)
            .execute()
        )

        if not existing.data:
            return jsonify({"error": "Expense not found."}), 404

        supabase.table("expenses").delete().eq(
            "id",
            expense_id
        ).execute()

        return jsonify({
            "message": "Expense deleted successfully."
        })

    except Exception as error:
        print(error)
        return jsonify({"error": "Could not delete expense."}), 500


@app.route("/dashboard", methods=["GET"])
def dashboard():

    try:
        expenses = get_expenses()

        total = sum(
            float(expense.get("amount", 0))
            for expense in expenses
        )

        categories = {
            expense.get("category")
            for expense in expenses
            if expense.get("category")
        }

        return jsonify({
            "total": total,
            "count": len(expenses),
            "categories": len(categories)
        })

    except Exception as error:
        print(error)
        return jsonify({"error": "Could not load dashboard."}), 500


@app.route("/analytics/day/<date>", methods=["GET"])
def day_analytics(date):

    try:
        selected_date = datetime.strptime(
            date,
            "%Y-%m-%d"
        ).date()
    except ValueError:
        return jsonify({"error": "Invalid date."}), 400

    try:
        response = (
            supabase
            .table("expenses")
            .select("*")
            .eq("date", date)
            .execute()
        )

        day_expenses = response.data or []

        category_totals = {}

        for expense in day_expenses:

            category = expense.get("category", "Other")
            amount = float(expense.get("amount", 0))

            category_totals[category] = (
                category_totals.get(category, 0) + amount
            )

        categories = [
            {
                "category": category,
                "total": total
            }
            for category, total in category_totals.items()
        ]

        total = sum(
            item["total"]
            for item in categories
        )

        return jsonify({
            "date": date,
            "formatted_date": selected_date.strftime("%d %B %Y"),
            "total": total,
            "count": len(day_expenses),
            "categories": categories,
            "expenses": day_expenses
        })

    except Exception as error:
        print(error)
        return jsonify({"error": "Could not load analytics."}), 500


@app.route("/expenses/3weeks", methods=["GET"])
def three_weeks():

    try:
        expenses = get_expenses()

        today = datetime.now().date()

        days = []

        for i in range(20, -1, -1):

            current_date = today - timedelta(days=i)

            date_string = current_date.strftime("%Y-%m-%d")

            matching = [
                expense
                for expense in expenses
                if str(expense.get("date")) == date_string
            ]

            total = sum(
                float(expense.get("amount", 0))
                for expense in matching
            )

            days.append({
                "date": date_string,
                "day": current_date.strftime("%a"),
                "day_number": current_date.strftime("%d"),
                "total": total,
                "count": len(matching)
            })

        return jsonify({
            "days": days,
            "total": sum(day["total"] for day in days),
            "count": sum(day["count"] for day in days)
        })

    except Exception as error:
        print(error)
        return jsonify({"error": "Could not load weekly data."}), 500
