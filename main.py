import pyodbc
import csv
from calendar import monthrange
from calendar import monthrange
from datetime import date


connection_string = (
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=ACU-HYD-LT-2006\SQLEXPRESS;"
    r"DATABASE=BillSubscription;"
    r"Trusted_Connection=yes;"
    r"Encrypt=yes;"
    r"TrustServerCertificate=yes;"
    )

conn = pyodbc.connect(connection_string)
curr = conn.cursor()

query1 = """CREATE TABLE Customers(
customer_id NVARCHAR(4) PRIMARY KEY,
name NVARCHAR(20),
coupon_code NVARCHAR(10),
coupon_percent FLOAT,
credit_balance FLOAT
)"""


query2 = """CREATE TABLE Subscriptions(
customer_id NVARCHAR(4) 
    REFERENCES Customers(customer_id),
event_date DATE,
event_type NVARCHAR(10),
plan_code NVARCHAR(10)
)"""

query3 = """CREATE TABLE Usage(
customer_id NVARCHAR(4) 
    REFERENCES Customers(customer_id),
usage_date DATE,
units INTEGER
)"""

# try:
#     curr.execute(query1)
#     print("Created successfully 1")

#     curr.execute(query2)
#     print("Created successfully 2")

#     curr.execute(query3)
#     print("Created successfully 3")

#     conn.commit()
# except Exception as e:
#     print(e)

def load_customers():
    try:
        file = open("customers.csv", "r")
        data = csv.reader(file)
        return data
    except FileNotFoundError:
        print("File not found..")

def load_subscriptions():
    try:
        file = open("subscription_events.csv", "r")
        data = csv.reader(file)
        return data
    except FileNotFoundError:
        print("File not found..")

def load_usage():
    try:
        file = open("usage.csv", "r")
        data = csv.reader(file)
        return data
    except FileNotFoundError:
        print("File not found..")

# Loading customer data
# customer = load_customers()

# insert_query1 = """INSERT INTO Customers VALUES(?,?,?,?,?)"""
# for c in customer:
#     try:
#         if len(c)!=5:
#             raise Exception("Feild cannot be less than 5")

#         # customer_id,name,coupon_code,coupon_percent,credit_balance

#         id , name , coupon_code, coupon_percent, credit = [x.strip() for x in c]

#         curr.execute(insert_query1, (id,name,coupon_code, coupon_percent,credit))
#         conn.commit()
#     except Exception as e:
#         print(e)

# insert_query2 = """INSERT INTO Subscriptions VALUES(?,?,?,?)"""

# # Loading subscription data

# subscription = load_subscriptions()

# for s in subscription:
#     try:
#         if len(s)!=4:
#             raise Exception("Feild cannot be less than 5")

#         # customer_id,event_date,event_type,plan_code

#         id, even_date, event_type, plan_code = [x.strip() for x in s]

#         curr.execute(insert_query2, (id, even_date, event_type, plan_code))
#         print("exceuted succesfully..")
#         conn.commit()
#     except Exception as e:
#         print(e)

usage = load_usage()

# insert_query3 = """INSERT INTO USAGE VALUES(?,?,?)"""

# for i in usage:
#     try:
#         if len(i)!=3:
#             raise Exception("Missing feields,,")

#         id, usage_date, units = i

#         curr.execute(insert_query3, (id, usage_date, units))

#         conn.commit()

#     except Exception as e:
#         print(e)

def load_plans():
    try:
        file = open("plans.csv","r")
        data = csv.reader(file)
        return data
    except Exception as e:
        print(e)

plans = load_plans()

# plan_code,monthly_fee,included_units

query4= """CREATE TABLE PLANS (
plan_code NVARCHAR(10),
monthly_fee FLOAT,
included_units INTEGER
)"""

# curr.execute(query4)
# conn.commit()

# insert_query4 = """INSERT INTO PLANS VALUES(?,?,?)"""

# for i in plans:
#     try:
#         if len(i)!=3:
#             raise Exception("Missing feields,,")

#         code, fee, units = i

#         curr.execute(insert_query4, (code, fee, units))

#         conn.commit()

#     except Exception as e:
#         print(e)

select_query1 = """
SELECT customer_id, event_date, event_type, plan_code
FROM Subscriptions
ORDER BY customer_id, event_date
"""

# curr.execute(select_query1)
# data = curr.fetchall()

# for i in data:
#     print(i)

billing_month = "2026-09"

year, month = map(int, billing_month.split("-"))

days_in_month = monthrange(year, month)[1]

# print("Billing month:", billing_month)
# print("Days in month:", days_in_month)

# select_query2 = """
# SELECT
#     customer_id,
#     event_date,
#     event_type,
#     plan_code
# FROM Subscriptions
# WHERE event_date <= ?
# ORDER BY customer_id, event_date
# """

month_end = date(year, month, days_in_month)

# curr.execute(select_query2, (month_end,))
# data = curr.fetchall()

month_start = date(year, month, 1)

query3 = """
SELECT s.customer_id, s.event_date, s.event_type, s.plan_code
FROM Subscriptions s
WHERE s.event_date = (
    SELECT MAX(s2.event_date)
    FROM Subscriptions s2
    WHERE s2.customer_id = s.customer_id
      AND s2.event_date < ?
)
AND s.event_type != 'CANCEL'
ORDER BY s.customer_id
"""

curr.execute(query3, (month_start,))
previous_events = curr.fetchall()

query4 = """
SELECT customer_id, event_date, event_type, plan_code
FROM Subscriptions
WHERE event_date >= ?
  AND event_date <= ?
ORDER BY customer_id, event_date
"""

curr.execute(query4, (month_start, month_end))
month_events = curr.fetchall()


query5 = """
SELECT DISTINCT plan_code, monthly_fee, included_units
FROM PLANS
ORDER BY plan_code
"""

curr.execute(query5)
plans_data = curr.fetchall()

all_events = previous_events + month_events

all_events.sort(key=lambda x: (x[0], x[1]))

plan_fees = {
    plan_code: float(str(monthly_fee))
    for plan_code, monthly_fee, included_units in plans_data
}

customer_segments = {}
active_plan = {}
segment_start = {}


for customer_id, event_date, event_type, plan_code in all_events:

    if customer_id not in customer_segments:
        customer_segments[customer_id] = []

    if event_date < month_start:
        if event_type == "START" or event_type == "CHANGE":
            active_plan[customer_id] = plan_code
        elif event_type == "CANCEL":
            active_plan.pop(customer_id, None)

    else:
        if event_type == "START":
            active_plan[customer_id] = plan_code
            segment_start[customer_id] = event_date

        elif event_type == "CHANGE":
            if customer_id in active_plan:
                end_date = event_date.fromordinal(event_date.toordinal() - 1)
                start_date = max(segment_start.get(customer_id, month_start), month_start)

                if start_date <= end_date:
                    customer_segments[customer_id].append(
                        (active_plan[customer_id], start_date, end_date)
                    )

            active_plan[customer_id] = plan_code
            segment_start[customer_id] = event_date

        elif event_type == "CANCEL":
            if customer_id in active_plan:
                start_date = max(segment_start.get(customer_id, month_start), month_start)

                if start_date <= event_date:
                    customer_segments[customer_id].append(
                        (active_plan[customer_id], start_date, event_date)
                    )

            active_plan.pop(customer_id, None)
            segment_start.pop(customer_id, None)

for customer_id, plan_code in active_plan.items():
    start_date = max(segment_start.get(customer_id, month_start), month_start)

    if start_date <= month_end:
        customer_segments[customer_id].append(
            (plan_code, start_date, month_end)
        )
for customer_id, segments in sorted(customer_segments.items()):
    for plan_code, start_date, end_date in segments:
        days = (end_date - start_date).days + 1

        fee = round(float(plan_fees[plan_code]) * days / days_in_month, 2)

        print(
            f"Customer: {customer_id}, "
            f"Plan: {plan_code}, "
            f"Start: {start_date}, "
            f"End: {end_date}, "
            f"Days: {days}, "
            f"Fee: {fee:.2f}"
        )

# or i can use this swl query

sgemnt_fee_query = """SELECT
    s.customer_id,
    s.plan_code,
    p.monthly_fee,
    DATEDIFF(DAY, '2026-09-01', '2026-09-10') + 1 AS days,
    CAST(
        p.monthly_fee *
        (DATEDIFF(DAY, '2026-09-01', '2026-09-10') + 1)
        / DAY(EOMONTH('2026-09-01'))
        AS DECIMAL(10, 2)
    ) AS segment_fee
FROM Subscriptions s
JOIN PLANS p
    ON s.plan_code = p.plan_code
WHERE s.customer_id = 'C003'
  AND s.plan_code = 'BASIC';
  """