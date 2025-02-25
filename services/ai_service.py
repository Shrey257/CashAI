import os
from openai import OpenAI
from datetime import datetime, timedelta
from models import Expense, Budget, Category
from extensions import db

# Initialize OpenAI client with the provided API key
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_spending_patterns(user):
    """Analyze user's spending patterns and generate comprehensive insights."""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    expenses = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= thirty_days_ago
    ).all()

    # Calculate total spending and category breakdown
    total_spent = sum(expense.amount for expense in expenses)
    category_spending = {}
    for expense in expenses:
        cat_name = expense.category.name
        if cat_name not in category_spending:
            category_spending[cat_name] = 0
        category_spending[cat_name] += expense.amount

    # Get user's budgets
    budgets = {budget.category.name: budget.amount for budget in user.budgets}
    
    # Build detailed spending analysis
    analysis = "Here's your spending analysis:\n\n"
    for category, amount in category_spending.items():
        budget = budgets.get(category, 0)
        percentage = (amount / budget * 100) if budget > 0 else 0
        analysis += f"- {category}: Spent ${amount:.2f}"
        if budget:
            analysis += f" (Budget: ${budget:.2f}, {percentage:.1f}% used)\n"
            if percentage > 100:
                analysis += f"⚠️ Over budget by ${amount - budget:.2f}\n"
            elif percentage > 90:
                analysis += "⚠️ Approaching budget limit\n"

    # Prepare context for OpenAI
    if not expenses:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """You are an expert financial advisor specializing in student finances.
                    Provide specific, actionable advice focusing on:
                    
                    1. Immediate Action Items:
                    - Concrete steps to improve financial health
                    - Specific dollar amounts and percentages
                    - Local campus resources and opportunities
                    
                    2. Spending Analysis:
                    - Compare to typical student benchmarks
                    - Identify concerning patterns
                    - Highlight positive financial habits
                    
                    3. Money-Saving Opportunities:
                    - Student-specific discounts and deals
                    - Campus resource alternatives
                    - Seasonal saving strategies
                    
                    Use emojis and clear formatting to make advice engaging and actionable.
                    
                    Budget Recommendations:
                    - 🍽️ Food & Groceries: 30-35% (meal prep, campus dining, groceries)
                    - 📚 Education: 15-20% (books, supplies, software)
                    - 🚌 Transportation: 10-15% (public transit, ride-sharing)
                    - 🎮 Entertainment: 5-10% (social activities, streaming)
                    - 🏠 Housing/Utilities: 25-30% (if applicable)
                    
                    Additional Topics:
                    - 💰 Emergency fund building
                    - 📈 Basic investing (apps, micro-investing)
                    - 💳 Student credit building
                    - 🎓 Student loan management
                    - 💼 Part-time work opportunities
                    - 🏪 Student discounts and deals
                    - 📱 Money-saving apps
                    - 📅 Seasonal savings tips
                    
                    Response Style:
                    - Use emojis for engagement
                    - Provide specific dollar examples
                    - Include campus-specific opportunities
                    - Share real student success stories
                    - Highlight free campus resources
                    - Suggest tech tools and apps
                    - Mix immediate and long-term advice"""},
                    {"role": "user", "content": "I'm a student starting to budget. What are realistic spending targets?"}
                ]
            )
            return response.choices[0].message.content.replace('**', '')
        except Exception as e:
            return """💰 **Recommended Student Budget Breakdown:**
• 🍽️ Food & Groceries: **$300-400** monthly (includes meal plans and groceries)
• 📚 Education: **$150-200** monthly (books, supplies, software)
• 🚌 Transportation: **$100-150** monthly (public transit, ride-sharing)
• 🎮 Entertainment: **$50-100** monthly (social activities, streaming services)
• 🏠 Utilities: **$50-100** monthly (phone, internet, shared utilities)"""

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
                {"role": "system", "content": """You are a financial advisor specializing in student finances.
                Analyze their spending with consideration for typical student expenses and provide:
                1. Comparison to typical student spending patterns
                2. Specific areas where they could save money
                3. Student-specific saving opportunities (student discounts, campus resources, etc.)

                Format with:
                - Category-specific emojis
                - Bold text for key numbers
                - Clear action items
                - Student-focused recommendations"""},
                {"role": "user", "content": spending_context}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return """🎓 **Student Budget Analysis:**
• Compare prices for textbooks across different platforms and consider rentals
• Use student meal plans strategically to reduce food costs
• Take advantage of student discounts on transportation and entertainment"""

def generate_saving_tip():
    """Generate an engaging saving tip for students."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a savvy financial advisor for students.
                Provide one creative money-saving tip specifically for students.
                Include:
                - Specific amounts that could be saved
                - Real student examples
                - Campus-specific opportunities
                Use emojis but avoid markdown formatting."""},
                {"role": "user", "content": "Give me a creative money-saving tip for college students."}
            ]
        )
        return response.choices[0].message.content.strip().replace('**', '')
    except Exception as e:
        return "💡 Smart Student Savings: Use your student ID for discounts on software, entertainment, and food. Many restaurants near campus offer 10-25% off with student ID!"

def categorize_transaction(description, amount):
    """Use enhanced NLP to categorize transactions based on typical student spending."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are an expert at categorizing student expenses.
                Analyze the transaction and categorize it into:
                - 🍽️ Food & Groceries (restaurants, cafes, grocery stores, meal plans)
                - 📚 Education (textbooks, supplies, software, courses)
                - 🚌 Transportation (public transit, ride-sharing, gas)
                - 🎮 Entertainment (streaming, events, games, social activities)
                - 🏠 Utilities (phone, internet, electricity)

                Consider:
                - Common student vendors and services
                - Typical price ranges for student purchases
                - Campus-related expenses

                Respond with ONLY the category emoji + name."""},
                {"role": "user", "content": f"Categorize this student expense: {description} - ${amount}"}
            ]
        )
        category = response.choices[0].message.content.strip()
        category_map = {
            'Food & Groceries': '🍽️ Food',
            'Education': '📚 Education',
            'Transportation': '🚌 Transportation',
            'Entertainment': '🎮 Entertainment',
            'Utilities': '🏠 Utilities'
        }

        # Extract the category name without emoji
        for full_category, mapped_category in category_map.items():
            if full_category.lower() in category.lower():
                return mapped_category
        return 'Other'
    except Exception as e:
        return 'Other'

def analyze_expense_cause(user):
    """Analyze spending patterns with student-specific insights."""
    expenses = Expense.query.filter_by(user_id=user.id).all()
    if not expenses:
        return """📊 **Start Your Financial Journey!**
• Track your daily expenses to understand your spending
• Set realistic budgets based on student lifestyle
• Look for student-specific savings opportunities"""

    total_spent = sum(e.amount for e in expenses)
    categories = {}
    for expense in expenses:
        if expense.category.name not in categories:
            categories[expense.category.name] = 0
        categories[expense.category.name] += expense.amount

    try:
        context = f"Total spent: **${total_spent:.2f}**\n\nYour spending by category:\n"
        for category, amount in categories.items():
            percentage = (amount / total_spent) * 100
            context += f"• {category}: **${amount:.2f}** ({percentage:.1f}%)\n"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Analyze student spending patterns and provide:
                1. Comparison to typical student budgets
                2. Specific saving opportunities on campus
                3. Student discount recommendations

                Format with:
                - Category-specific emojis
                - Bold text for important numbers
                - Student-focused action items"""},
                {"role": "user", "content": context}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "Unable to analyze spending patterns at the moment. Try again later."

def simulate_financial_scenario(description, user):
    """Simulate financial scenarios for students."""
    current_expenses = sum(e.amount for e in user.expenses) if user.expenses else 0
    budgets = {b.category.name: b.amount for b in user.budgets}

    try:
        context = f"""Current monthly expenses: **${current_expenses:.2f}**
Current budgets: {', '.join(f'{cat}: **${amt:.2f}**' for cat, amt in budgets.items())}
Scenario to analyze: {description}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """You are a financial advisor helping a student plan their finances.
                Consider:
                - Typical student income sources (part-time jobs, internships)
                - Campus work opportunities
                - Student-specific expenses
                - Academic schedule impact

                Format with:
                - Emojis for different aspects
                - Bold text for key numbers
                - Practical student examples
                - Campus-specific recommendations"""},
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