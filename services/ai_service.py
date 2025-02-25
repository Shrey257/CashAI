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
                    {"role": "system", "content": """You are a friendly and engaging financial advisor for college students.
                    Provide 3 specific tips for getting started with budgeting.
                    Format your response with:
                    - Emojis for visual engagement
                    - Bold text for key points (use markdown **text**)
                    - Short, clear bullet points
                    - A motivational tone
                    Keep it practical and student-focused."""},
                    {"role": "user", "content": "Give advice for a student just starting to track their expenses."}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return """💡 **Start Small, Think Big!**
• Track every expense, no matter how small - they add up!
• Set realistic budget goals that match your lifestyle
• Use student discounts to maximize your savings"""

    # If there is spending data, analyze it
    category_spending = {}
    for expense in expenses:
        category = expense.category.name
        if category not in category_spending:
            category_spending[category] = 0
        category_spending[category] += expense.amount

    budgets = {budget.category.name: budget.amount for budget in user.budgets}

    spending_context = "Here's your spending data for the last 30 days:\n"
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
                {"role": "system", "content": """You are a friendly and insightful financial advisor helping a college student understand their spending.
                Analyze their expenses and provide 3 personalized insights.
                Format your response with:
                - Emojis for each insight
                - Bold text for key numbers and findings
                - Clear action items
                - Encouraging tone
                Make it visually engaging and easy to read."""},
                {"role": "user", "content": spending_context}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return """💰 **Track Your Spending**
• Monitor daily expenses to build better habits
• Set up budget alerts to stay on track
• Look for student discounts on essential purchases"""

def generate_saving_tip():
    """Generate an engaging saving tip for students."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a savvy financial advisor for college students.
                Provide one creative money-saving tip specifically for students.
                Format your response with:
                - An appropriate emoji
                - Bold text for key points
                - A practical, actionable suggestion
                - An encouraging tone
                Keep it concise (max 2 sentences) and engaging."""},
                {"role": "user", "content": "Give me a money-saving tip for college students."}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "📚 **Save on Textbooks**: Compare prices across different platforms and consider renting or buying used textbooks to save significantly on course materials."

def analyze_expense_cause(user):
    """Analyze spending patterns and provide insights."""
    expenses = Expense.query.filter_by(user_id=user.id).all()
    if not expenses:
        return "📊 Start tracking your expenses to get personalized insights! I'll help you understand your spending patterns and find ways to save."

    total_spent = sum(e.amount for e in expenses)
    categories = {}
    for expense in expenses:
        if expense.category.name not in categories:
            categories[expense.category.name] = 0
        categories[expense.category.name] += expense.amount

    try:
        context = f"Total spent: **${total_spent:.2f}**\n\nBreakdown by category:\n"
        for category, amount in categories.items():
            percentage = (amount / total_spent) * 100
            context += f"• {category}: **${amount:.2f}** ({percentage:.1f}%)\n"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Analyze the spending patterns and provide insights with:
                - Emoji indicators for different spending levels
                - Bold text for important numbers
                - Clear recommendations
                - A supportive, non-judgmental tone
                Make your response visually appealing and easy to understand."""},
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
        context = f"""Current monthly expenses: **${current_expenses:.2f}**
Current budgets: {', '.join(f'{cat}: **${amt:.2f}**' for cat, amt in budgets.items())}
Scenario to analyze: {description}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a financial simulator helping a student understand potential scenarios.
                Provide analysis with:
                - Emojis for different aspects (💰 for income, 📊 for expenses, etc.)
                - Bold text for key numbers
                - Clear bullet points
                - Visual organization
                Make it engaging and easy to understand."""},
                {"role": "user", "content": context}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Unable to simulate this scenario at the moment. Please try again later."

def categorize_transaction(description, amount):
    """Use NLP to categorize a transaction based on its description."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a smart transaction categorization system.
                Analyze the transaction and categorize it into:
                - 🍽️ Food
                - 🚌 Transportation
                - 📚 Education
                - 🎮 Entertainment
                - 🏠 Utilities
                Respond with ONLY the category name."""},
                {"role": "user", "content": f"Transaction: {description} - ${amount}"}
            ]
        )
        category = response.choices[0].message.content.strip()
        category_map = {
            'Food': '🍽️ Food',
            'Transportation': '🚌 Transportation',
            'Education': '📚 Education',
            'Entertainment': '🎮 Entertainment',
            'Utilities': '🏠 Utilities'
        }
        return category_map.get(category, 'Other')
    except Exception as e:
        return 'Other'

def summarize_expenses(expenses):
    """Helper function to summarize expenses by category"""
    summary = {}
    for expense in expenses:
        category = expense.category.name
        if category not in summary:
            summary[category] = 0
        summary[category] += expense.amount
    return {k: f"${v:.2f}" for k, v in summary.items()}