#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"


EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}


financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str maybe_dt: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    date_parts = maybe_dt.split("-")
    if len(date_parts) != 3:
        return None

    day_raw, month_raw, year_raw = date_parts
    if not day_raw.isdigit() or not month_raw.isdigit() or not year_raw.isdigit():
        return None

    day = int(day_raw)
    month = int(month_raw)
    year = int(year_raw)

    if year <= 0 or month < 1 or month > 12:
        return None

    max_day = 31
    if month in (4, 6, 9, 11):
        max_day = 30
    elif month == 2:
        max_day = 29 if is_leap_year(year) else 28

    if day < 1 or day > max_day:
        return None

    return day, month, year


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    parsed_date = extract_date(income_date)
    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({"amount": amount, "date": parsed_date})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= 0:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    parsed_date = extract_date(income_date)
    if parsed_date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    category_parts = category_name.split("::")
    if len(category_parts) != 2:
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY

    common_category, target_category = category_parts
    if common_category not in EXPENSE_CATEGORIES or target_category not in EXPENSE_CATEGORIES[common_category]:
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY

    financial_transactions_storage.append({"category": category_name, "amount": amount, "date": parsed_date})
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    return "\n".join(f"{common}::{target}" for common, targets in EXPENSE_CATEGORIES.items() for target in targets)


def stats_handler(report_date: str) -> str:
    parsed_report_date = extract_date(report_date)
    if parsed_report_date is None:
        return INCORRECT_DATE_MSG

    report_y, report_m, report_d = parsed_report_date[2], parsed_report_date[1], parsed_report_date[0]
    total_income = 0.0
    total_cost = 0.0
    category_details: dict[str, float] = {}

    for transaction in financial_transactions_storage:
        if not transaction:
            continue

        amount = transaction.get("amount")
        if not isinstance(amount, (int, float)):
            continue

        raw_date = transaction.get("date")
        parsed_transaction_date: tuple[int, int, int] | None = None
        if isinstance(raw_date, tuple) and len(raw_date) == 3:
            day, month, year = raw_date
            if isinstance(day, int) and isinstance(month, int) and isinstance(year, int):
                parsed_transaction_date = day, month, year
        elif isinstance(raw_date, str):
            parsed_transaction_date = extract_date(raw_date)

        if parsed_transaction_date is None:
            continue

        tr_y, tr_m, tr_d = parsed_transaction_date[2], parsed_transaction_date[1], parsed_transaction_date[0]
        if (tr_y, tr_m, tr_d) > (report_y, report_m, report_d):
            continue

        category_name = transaction.get("category")
        if isinstance(category_name, str):
            total_cost += amount
            if category_name not in category_details:
                category_details[category_name] = 0.0
            category_details[category_name] += amount
        else:
            total_income += amount

    total_cost = round(total_cost, 2)
    total_income = round(total_income, 2)
    total_capital = round(total_cost - total_income, 2)
    amount_word = "loss" if total_capital < 0 else "profit"
    category_stats = "\n".join(f"{i}. {category}: {amount}" for i, (category, amount) in enumerate(category_details.items()))

    return (
        f"Your statistics as of {report_date}:\n"
        f"Total capital: {total_capital} rubles\n"
        f"This month, the {amount_word} amounted to {total_capital} rubles.\n"
        f"Income: {total_cost} rubles\n"
        f"Expenses: {total_income} rubles\n\n"
        f"Details (category: amount):\n"
        f"{category_stats}\n"
    )


def main() -> None:
    while True:
        try:
            user_input = input().strip()
        except EOFError:
            break

        if not user_input:
            continue

        args = user_input.split()

        if len(args) == 3 and args[0] == "income":
            amount_raw = args[1].replace(",", ".")
            digits = amount_raw.replace(".", "", 1)
            if amount_raw in {"", "."} or amount_raw.count(".") > 1 or not digits.isdigit():
                print(UNKNOWN_COMMAND_MSG)
            else:
                print(income_handler(float(amount_raw), args[2]))
            continue

        if len(args) == 2 and args[0] == "cost" and args[1] == "categories":
            print(cost_categories_handler())
            continue

        if len(args) == 4 and args[0] == "cost":
            amount_raw = args[2].replace(",", ".")
            digits = amount_raw.replace(".", "", 1)
            if amount_raw in {"", "."} or amount_raw.count(".") > 1 or not digits.isdigit():
                print(UNKNOWN_COMMAND_MSG)
            else:
                print(cost_handler(args[1], float(amount_raw), args[3]))
            continue

        if len(args) == 2 and args[0] == "stats":
            print(stats_handler(args[1]))
            continue

        print(UNKNOWN_COMMAND_MSG)


if __name__ == "__main__":
    main()
