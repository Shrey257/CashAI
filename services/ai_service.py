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
