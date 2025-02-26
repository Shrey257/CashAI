
from datetime import datetime, timedelta
from models import FinancialGoal, Expense
import anthropic

def analyze_goal_feasibility(user, goal_amount, deadline):
    """Analyze if a financial goal is realistic based on spending patterns"""
    monthly_income = sum(e.amount for e in user.expenses if e.category.name == "Income")
    monthly_expenses = sum(e.amount for e in user.expenses if e.category.name != "Income")
    savings_capacity = monthly_income - monthly_expenses
    
    months_to_goal = (deadline - datetime.now()).days / 30
    required_monthly_saving = goal_amount / months_to_goal
    
    if required_monthly_saving > savings_capacity:
        return False, f"This goal might be challenging. You need to save ${required_monthly_saving:.2f} monthly, but your current saving capacity is ${savings_capacity:.2f}"
    return True, f"Goal looks achievable! Keep saving ${required_monthly_saving:.2f} monthly"

def suggest_saving_strategies(user, goal):
    """Generate personalized saving strategies"""
    expenses = Expense.query.filter_by(user_id=user.id).all()
    highest_category = max(expenses, key=lambda x: x.amount).category.name
    
    strategies = f"""Based on your spending patterns, here are personalized strategies to reach your {goal.name}:
    1. Reduce {highest_category} expenses by 20% to save extra ${sum(e.amount for e in expenses if e.category.name == highest_category) * 0.2:.2f} monthly
    2. Set up automatic transfers of ${goal.target_amount / (goal.deadline - datetime.now()).days * 30:.2f} monthly
    3. Look for additional income opportunities in your field"""
    
    return strategies
