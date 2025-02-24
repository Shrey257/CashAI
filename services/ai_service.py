import os
from openai import OpenAI
from datetime import datetime, timedelta
from models import Expense, Budget, Category
from extensions import db

# Initialize OpenAI client with the provided API key
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_spending_patterns(user):
    """Analyze user's spending patterns and generate insights."""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    expenses = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= thirty_days_ago
    ).all()

    # Prepare context for OpenAI
    if not expenses:
        try:
            # Generate general advice for new users
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """You are a financial advisor for college students.
                    Provide 3 specific tips for getting started with budgeting.
                    Keep the advice practical and student-focused.
                    Format the response as bullet points."""},
                    {"role": "user", "content": "Give advice for a student just starting to track their expenses."}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return """• Start by tracking all your expenses, no matter how small
• Set realistic budget categories based on your income
• Look for student discounts and deals to maximize savings"""

    # If there is spending data, analyze it
    category_spending = {}
    for expense in expenses:
        category = expense.category.name
        if category not in category_spending:
            category_spending[category] = 0
        category_spending[category] += expense.amount

    budgets = {budget.category.name: budget.amount for budget in user.budgets}

    spending_context = "Here's the student's spending data for the last 30 days:\n"
    for category, amount in category_spending.items():
        budget = budgets.get(category, 0)
        spending_context += f"- {category}: Spent ${amount:.2f}"
        if budget:
            percentage = (amount / budget) * 100
            spending_context += f" (Budget: ${budget:.2f}, {percentage:.1f}% used)"
        spending_context += "\n"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a financial advisor helping a college student understand their spending.
                Analyze their recent expenses and provide 3 specific, actionable insights.
                Focus on areas of improvement and practical saving opportunities.
                Use bullet points and be specific about numbers and percentages."""},
                {"role": "user", "content": spending_context}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "• Track your daily expenses to build better spending habits\n• Set budget alerts to avoid overspending\n• Look for student discounts on essential purchases"

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
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Consider buying used textbooks or renting them through your campus bookstore to save significantly on course materials."

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
            ]
        )
        category = response.choices[0].message.content.strip()
        return category if category in ['Food', 'Transportation', 'Education', 'Entertainment', 'Utilities'] else 'Other'
    except Exception as e:
        return 'Other'

def analyze_expense_cause(user):
    """Analyze spending patterns and provide insights."""
    expenses = Expense.query.filter_by(user_id=user.id).all()
    if not expenses:
        return "Start tracking your expenses to get personalized spending insights!"

    total_spent = sum(e.amount for e in expenses)
    categories = {}
    for expense in expenses:
        if expense.category.name not in categories:
            categories[expense.category.name] = 0
        categories[expense.category.name] += expense.amount

    try:
        context = f"Total spent: ${total_spent:.2f}\nBreakdown by category:\n"
        for category, amount in categories.items():
            percentage = (amount / total_spent) * 100
            context += f"- {category}: ${amount:.2f} ({percentage:.1f}%)\n"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Analyze the spending patterns and explain:
                1. Which categories had the highest spending
                2. Potential areas for savings
                3. Specific recommendations for improvement
                Keep the tone helpful and student-focused."""},
                {"role": "user", "content": context}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Unable to analyze spending patterns at the moment. Try again later."

def simulate_financial_scenario(description, user):
    """Simulate the impact of financial changes."""
    current_expenses = sum(e.amount for e in user.expenses) if user.expenses else 0
    budgets = {b.category.name: b.amount for b in user.budgets}

    try:
        context = f"""Current monthly expenses: ${current_expenses:.2f}
Current budgets: {', '.join(f'{cat}: ${amt:.2f}' for cat, amt in budgets.items())}
Scenario to analyze: {description}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a financial simulator helping a student understand potential scenarios.
                Analyze the situation and provide:
                1. Projected financial impact
                2. Potential benefits and risks
                3. Specific recommendations
                Use bullet points and include numbers where possible."""},
                {"role": "user", "content": context}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Unable to simulate this scenario at the moment. Please try again later."

def summarize_expenses(expenses):
    """Helper function to summarize expenses by category"""
    summary = {}
    for expense in expenses:
        category = expense.category.name
        if category not in summary:
            summary[category] = 0
        summary[category] += expense.amount
    return {k: f"${v:.2f}" for k, v in summary.items()}