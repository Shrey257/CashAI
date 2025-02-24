import os
import anthropic
from datetime import datetime, timedelta
from models import Expense, Budget, Category
from extensions import db

# Note that the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def get_expense_context(user):
    """Get user's expense and budget context for AI analysis"""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    expenses = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= thirty_days_ago
    ).all()
    
    budgets = Budget.query.filter_by(user_id=user.id).all()
    
    context = "User's last 30 days financial data:\n"
    
    # Aggregate expenses by category
    category_spending = {}
    for expense in expenses:
        category = expense.category.name
        if category not in category_spending:
            category_spending[category] = {'total': 0, 'budget': 0, 'transactions': []}
        category_spending[category]['total'] += expense.amount
        category_spending[category]['transactions'].append({
            'amount': expense.amount,
            'date': expense.date.strftime('%Y-%m-%d'),
            'description': expense.description
        })
    
    # Add budget information
    for budget in budgets:
        category = budget.category.name
        if category in category_spending:
            category_spending[category]['budget'] = budget.amount
    
    # Format context string
    for category, data in category_spending.items():
        context += f"\n{category}:\n"
        context += f"- Total Spent: ${data['total']:.2f}\n"
        if data['budget'] > 0:
            percentage = (data['total'] / data['budget']) * 100
            context += f"- Monthly Budget: ${data['budget']:.2f} ({percentage:.1f}% used)\n"
        context += "- Recent Transactions:\n"
        for transaction in data['transactions'][-3:]:  # Show last 3 transactions
            context += f"  * ${transaction['amount']:.2f} on {transaction['date']}"
            if transaction['description']:
                context += f" - {transaction['description']}"
            context += "\n"
    
    return context

def get_financial_advice(user_query, user):
    """Get AI-powered financial advice based on user query and financial data"""
    context = get_expense_context(user)
    
    system_prompt = """You are a financial advisor specialized in helping college students manage their budgets effectively. 
    You have access to the student's recent spending data and budgets.
    Provide specific, actionable advice based on their actual spending patterns and financial goals.
    Keep responses concise and focused on practical solutions.
    If suggesting budget adjustments, explain the reasoning and potential impact.
    
    Focus areas:
    1. Expense categorization and tracking
    2. Budget setting and adjustment
    3. Money-saving strategies
    4. Financial goal planning
    5. Smart spending habits
    
    Always maintain a supportive and encouraging tone while being realistic about financial constraints."""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context: {context}\n\nUser Question: {user_query}"}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return "I apologize, but I'm having trouble providing financial advice at the moment. Please try again later."

def suggest_budget_allocation(income, user_categories):
    """Get AI suggestions for budget allocation based on income and categories"""
    categories_str = ", ".join([cat.name for cat in user_categories])
    
    prompt = f"""Given a monthly income of ${income}, suggest a realistic budget allocation for a college student across these categories: {categories_str}.
    Consider typical student expenses and lifestyle.
    Format the response as a JSON-like structure with category names and percentages/amounts."""
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[
                {"role": "system", "content": "You are a financial advisor specializing in student budget planning."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return "Unable to generate budget suggestions at the moment. Please try again later."

def categorize_expense(description, amount):
    """Use AI to suggest a category for an expense based on its description"""
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[
                {"role": "system", "content": "You are a financial categorization assistant. Respond with only the category name."},
                {"role": "user", "content": f"Categorize this expense: ${amount} for {description}. Choose from: Food, Transportation, Education, Entertainment, Utilities"}
            ]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return "Uncategorized"
