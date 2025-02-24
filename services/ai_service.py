import os
from openai import OpenAI
from datetime import datetime, timedelta
from models import Expense, Budget

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_spending_patterns(user):
    """Analyze user's spending patterns and generate insights."""
    # Get expenses from the last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    expenses = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= thirty_days_ago
    ).all()

    if not expenses:
        return "Not enough spending data to generate insights. Start tracking your expenses!"

    # Calculate total spending by category
    category_spending = {}
    for expense in expenses:
        category = expense.category.name
        if category not in category_spending:
            category_spending[category] = 0
        category_spending[category] += expense.amount

    # Get user's budgets
    budgets = {budget.category.name: budget.amount for budget in user.budgets}

    # Prepare context for OpenAI
    spending_context = "Here's the student's spending data for the last 30 days:\n"
    for category, amount in category_spending.items():
        budget = budgets.get(category, 0)
        spending_context += f"- {category}: Spent ${amount:.2f}"
        if budget:
            percentage = (amount / budget) * 100
            spending_context += f" (Budget: ${budget:.2f}, {percentage:.1f}% used)"
        spending_context += "\n"

    try:
        # Generate personalized insights using OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a financial advisor for college students.
                Analyze their spending patterns and provide 3 specific, actionable tips to help them save money.
                Keep the advice concise, practical, and relevant to students.
                Format the response as a bullet-pointed list."""},
                {"role": "user", "content": spending_context}
            ],
            max_tokens=300,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Unable to generate personalized insights at the moment. Please try again later."

def analyze_expense_cause(user, month=None):
    """Analyze why spending increased/decreased compared to previous month."""
    current_date = datetime.now()
    if month:
        current_date = datetime.strptime(month, '%Y-%m')

    current_month_start = current_date.replace(day=1)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

    current_expenses = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= current_month_start,
        Expense.date < current_month_start + timedelta(days=32)
    ).all()

    previous_expenses = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= previous_month_start,
        Expense.date < current_month_start
    ).all()

    try:
        spending_analysis = {
            "current_month": summarize_expenses(current_expenses),
            "previous_month": summarize_expenses(previous_expenses)
        }

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a financial analyst helping a college student understand their spending patterns.
                Compare the current and previous month's expenses and explain significant changes.
                Focus on actionable insights and specific patterns."""},
                {"role": "user", "content": f"Current month spending: {spending_analysis['current_month']}\n\nPrevious month spending: {spending_analysis['previous_month']}"}
            ],
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Unable to analyze spending patterns at the moment."

def simulate_financial_scenario(scenario_description, user):
    """Simulate financial scenarios based on user's current spending patterns."""
    # Get user's current financial data
    current_expenses = Expense.query.filter_by(user_id=user.id).all()
    current_budgets = Budget.query.filter_by(user_id=user.id).all()

    # Prepare financial context
    financial_context = f"""Current financial situation:
    Monthly Budgets: {', '.join([f'{b.category.name}: ${b.amount:.2f}' for b in current_budgets])}
    Recent Expenses: {', '.join([f'{e.category.name}: ${e.amount:.2f}' for e in current_expenses[-5:]])}
    Scenario: {scenario_description}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a financial simulator helping a college student understand potential financial scenarios.
                Analyze their current spending and simulate how their finances would change under the given scenario.
                Provide specific numbers and realistic projections.
                Consider both income and expenses.
                Format the response clearly with bullet points and specific recommendations."""},
                {"role": "user", "content": financial_context}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Unable to simulate scenario at the moment. Please try again later."

def analyze_purchase_value(item_description, price, user):
    """Analyze if a purchase is worth it based on user's budget and spending history."""
    try:
        # Get user's financial context
        monthly_expenses = sum([e.amount for e in user.expenses])
        monthly_budgets = {b.category.name: b.amount for b in user.budgets}

        context = f"""
        User's monthly expenses: ${monthly_expenses:.2f}
        Monthly budgets: {', '.join([f'{k}: ${v:.2f}' for k, v in monthly_budgets.items()])}
        Proposed purchase: {item_description} for ${price:.2f}
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a financial advisor helping a college student decide on a purchase.
                Analyze if the purchase is worth it based on their current financial situation.
                Consider: budget impact, necessity, alternatives, and long-term value.
                Provide a clear recommendation with reasoning."""},
                {"role": "user", "content": context}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Unable to analyze purchase value at the moment. Please try again later."

def categorize_transaction(description, amount):
    """Use NLP to categorize a transaction based on its description."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a transaction categorization system.
                Categorize the transaction into one of these categories:
                - Food
                - Transportation
                - Education
                - Entertainment
                - Utilities
                Respond with ONLY the category name."""},
                {"role": "user", "content": f"Transaction: {description} - ${amount}"}
            ],
            max_tokens=50
        )
        category = response.choices[0].message.content.strip()
        return category if category in ['Food', 'Transportation', 'Education', 'Entertainment', 'Utilities'] else 'Other'
    except Exception as e:
        return 'Other'

def generate_saving_tip():
    """Generate a general saving tip for students."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a financial advisor for college students.
                Provide one practical money-saving tip specifically for college students.
                Keep it concise (max 2 sentences) and actionable."""},
                {"role": "user", "content": "Give me a money-saving tip for college students."}
            ],
            max_tokens=100,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Look for student discounts on textbooks and supplies to save money."

def summarize_expenses(expenses):
    """Helper function to summarize expenses by category"""
    summary = {}
    for expense in expenses:
        category = expense.category.name
        if category not in summary:
            summary[category] = 0
        summary[category] += expense.amount
    return {k: f"${v:.2f}" for k, v in summary.items()}