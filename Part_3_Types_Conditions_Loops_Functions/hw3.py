#!/usr/bin/env python
UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
OP_SUCCESS_MSG = "Added"

INCOME_ARGS_COUNT = 3
COST_ARGS_COUNT = 4
STATS_ARGS_COUNT = 2

DATE_PARTS_COUNT = 3
DAY_TEXT_LEN = 2
MONTH_TEXT_LEN = 2
YEAR_TEXT_LEN = 4

MIN_DAY = 1
MIN_MONTH = 1
MAX_MONTH = 12

DAYS_IN_LONG_MONTH = 31
DAYS_IN_SHORT_MONTH = 30
DAYS_IN_FEBRUARY = 28
DAYS_IN_LEAP_FEBRUARY = 29

MONTHS_WITH_THIRTY_DAYS = (4, 6, 9, 11)
FEBRUARY = 2

Date = tuple[int, int, int]
IncomeRecord = tuple[float, Date]
CostRecord = tuple[str, float, Date]
IncomeStats = tuple[float, float]
CostStats = tuple[float, float, dict[str, float]]


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def has_valid_date_lengths(day_text: str, month_text: str, year_text: str) -> bool:
    return (
        len(day_text),
        len(month_text),
        len(year_text),
    ) == (
        DAY_TEXT_LEN,
        MONTH_TEXT_LEN,
        YEAR_TEXT_LEN,
    )


def has_only_date_digits(day_text: str, month_text: str, year_text: str) -> bool:
    return day_text.isdigit() and month_text.isdigit() and year_text.isdigit()


def is_valid_date_text(parts: list[str]) -> bool:
    day_text = parts[0]
    month_text = parts[1]
    year_text = parts[2]
    return has_valid_date_lengths(day_text, month_text, year_text) and has_only_date_digits(
        day_text,
        month_text,
        year_text,
    )


def get_days_in_month(month: int, year: int) -> int:
    if month in MONTHS_WITH_THIRTY_DAYS:
        return DAYS_IN_SHORT_MONTH
    if month == FEBRUARY:
        if is_leap_year(year):
            return DAYS_IN_LEAP_FEBRUARY
        return DAYS_IN_FEBRUARY
    return DAYS_IN_LONG_MONTH


def is_valid_date_values(day: int, month: int, year: int) -> bool:
    if month < MIN_MONTH or month > MAX_MONTH:
        return False
    if day < MIN_DAY:
        return False
    return day <= get_days_in_month(month, year)


def parse_date_parts(parts: list[str]) -> Date | None:
    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])
    if not is_valid_date_values(day, month, year):
        return None
    return day, month, year


def extract_date(maybe_dt: str) -> Date | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS_COUNT:
        return None
    if not is_valid_date_text(parts):
        return None
    return parse_date_parts(parts)


def remove_sign(number_text: str) -> str:
    if number_text != "" and number_text[0] in "+-":
        return number_text[1:]
    return number_text


def is_valid_unsigned_number(number_text: str) -> bool:
    if number_text == "":
        return False
    if number_text.count(".") > 1:
        return False
    if "." not in number_text:
        return number_text.isdigit()

    left_part, right_part = number_text.split(".", maxsplit=1)
    if left_part == "" and right_part == "":
        return False

    left_is_ok = left_part == "" or left_part.isdigit()
    right_is_ok = right_part == "" or right_part.isdigit()
    return left_is_ok and right_is_ok


def extract_amount(raw_amount: str) -> float | None:
    normalized = raw_amount.replace(",", ".")
    body = remove_sign(normalized)
    if not is_valid_unsigned_number(body):
        return None
    return float(normalized)


def is_not_later(record_date: Date, target_date: Date) -> bool:
    return (
        record_date[2],
        record_date[1],
        record_date[0],
    ) <= (
        target_date[2],
        target_date[1],
        target_date[0],
    )


def is_in_target_month(record_date: Date, target_date: Date) -> bool:
    if record_date[2] != target_date[2]:
        return False
    if record_date[1] != target_date[1]:
        return False
    return record_date[0] <= target_date[0]


def format_detail_amount(value: float) -> str:
    text = f"{value:.2f}"
    if text == "-0.00":
        text = "0.00"
    return text.rstrip("0").rstrip(".")


def collect_income_stats(target_date: Date, incomes: list[IncomeRecord]) -> IncomeStats:
    total_capital = float(0)
    monthly_income = float(0)
    for amount, record_date in incomes:
        if is_not_later(record_date, target_date):
            total_capital += amount
        if is_in_target_month(record_date, target_date):
            monthly_income += amount
    return total_capital, monthly_income


def add_category_amount(monthly_categories: dict[str, float], category: str, amount: float) -> None:
    existing_amount = monthly_categories.get(category, float(0))
    monthly_categories[category] = existing_amount + amount


def collect_cost_stats(target_date: Date, costs: list[CostRecord]) -> CostStats:
    total_cost_until_date = float(0)
    monthly_cost = float(0)
    monthly_categories: dict[str, float] = {}
    for cost in costs:
        if is_not_later(cost[2], target_date):
            total_cost_until_date += cost[1]
        if is_in_target_month(cost[2], target_date):
            monthly_cost += cost[1]
            add_category_amount(monthly_categories, cost[0], cost[1])
    return total_cost_until_date, monthly_cost, monthly_categories


def print_profit_or_loss(monthly_balance: float) -> None:
    if monthly_balance >= 0:
        print(f"\u0412 этом месяце прибыль составила {monthly_balance:.2f} рублей")
        return
    print(f"\u0412 этом месяце убыток составил {abs(monthly_balance):.2f} рублей")


def print_category_details(monthly_categories: dict[str, float]) -> None:
    print("Детализация (категория: сумма):")
    index = 1
    for category in sorted(monthly_categories):
        print(f"{index}. {category}: {format_detail_amount(monthly_categories[category])}")
        index += 1


def print_stats(target_date_text: str, target_date: Date, incomes: list[IncomeRecord], costs: list[CostRecord]) -> None:
    income_stats = collect_income_stats(target_date, incomes)
    cost_stats = collect_cost_stats(target_date, costs)
    monthly_balance = income_stats[1] - cost_stats[1]
    total_capital = income_stats[0] - cost_stats[0]

    print(f"Ваша статистика по состоянию на {target_date_text}:")
    print(f"Суммарный капитал: {total_capital:.2f} рублей")
    print_profit_or_loss(monthly_balance)
    print(f"Доходы: {income_stats[1]:.2f} рублей")
    print(f"Расходы: {cost_stats[1]:.2f} рублей")
    print()
    print_category_details(cost_stats[2])


def process_income(parts: list[str], incomes: list[IncomeRecord]) -> None:
    if len(parts) != INCOME_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = extract_amount(parts[1])
    if amount is None or amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return

    parsed_date = extract_date(parts[2])
    if parsed_date is None:
        print(INCORRECT_DATE_MSG)
        return

    incomes.append((amount, parsed_date))
    print(OP_SUCCESS_MSG)


def process_cost(parts: list[str], costs: list[CostRecord]) -> None:
    if len(parts) != COST_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return

    category = parts[1]
    if category == "" or "." in category or "," in category:
        print(UNKNOWN_COMMAND_MSG)
        return

    amount = extract_amount(parts[2])
    if amount is None or amount <= 0:
        print(NONPOSITIVE_VALUE_MSG)
        return

    parsed_date = extract_date(parts[3])
    if parsed_date is None:
        print(INCORRECT_DATE_MSG)
        return

    costs.append((category, amount, parsed_date))
    print(OP_SUCCESS_MSG)


def process_stats(parts: list[str], incomes: list[IncomeRecord], costs: list[CostRecord]) -> None:
    if len(parts) != STATS_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return

    target_date_text = parts[1]
    parsed_date = extract_date(target_date_text)
    if parsed_date is None:
        print(INCORRECT_DATE_MSG)
        return

    print_stats(target_date_text, parsed_date, incomes, costs)


def process_command(parts: list[str], incomes: list[IncomeRecord], costs: list[CostRecord]) -> None:
    command = parts[0]
    if command == "income":
        process_income(parts, incomes)
        return
    if command == "cost":
        process_cost(parts, costs)
        return
    if command == "stats":
        process_stats(parts, incomes, costs)
        return
    print(UNKNOWN_COMMAND_MSG)


def process_input(incomes: list[IncomeRecord], costs: list[CostRecord]) -> None:
    with open(0) as stdin:
        for raw_line in stdin:
            line = raw_line.strip()
            if line == "":
                continue
            parts = line.split()
            process_command(parts, incomes, costs)


def main() -> None:
    incomes: list[IncomeRecord] = []
    costs: list[CostRecord] = []
    process_input(incomes, costs)


if __name__ == "__main__":
    main()
