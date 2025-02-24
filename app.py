import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from extensions import db
from models import User, Expense, Budget, Category
from services.ai_service import (
    analyze_spending_patterns, 
    generate_saving_tip,
    simulate_financial_scenario,
    analyze_purchase_value,
    analyze_expense_cause,
    categorize_transaction
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///budget.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Login manager configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.password_hash = generate_password_hash(password)

        db.session.add(user)
        db.session.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5).all()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()

    # Get AI-generated insights
    ai_insights = analyze_spending_patterns(current_user)
    saving_tip = generate_saving_tip()

    return render_template('dashboard.html', 
                         expenses=expenses, 
                         budgets=budgets,
                         ai_insights=ai_insights,
                         saving_tip=saving_tip)

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        description = request.form.get('description', '')

        # Use NLP to categorize the expense if category not provided
        category_id = request.form.get('category')
        if not category_id:
            suggested_category = categorize_transaction(description, amount)
            category = Category.query.filter_by(name=suggested_category).first()
            if category:
                category_id = category.id
            else:
                # Default to first category if suggestion fails
                category_id = Category.query.first().id
        else:
            category_id = int(category_id)

        expense = Expense(
            amount=amount,
            category_id=category_id,
            description=description,
            user_id=current_user.id,
            date=datetime.now()
        )

        db.session.add(expense)
        db.session.commit()

        # Check if this expense pushes the category over the notification threshold
        budget = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=category_id
        ).first()

        if budget:
            total_expenses = sum(e.amount for e in Expense.query.filter_by(
                user_id=current_user.id,
                category_id=category_id
            ).all())

            percentage = (total_expenses / budget.amount) * 100
            if percentage >= budget.notify_threshold:
                flash(f'Warning: You\'ve reached {int(percentage)}% of your {expense.category.name} budget!', 'warning')

        flash('Expense added successfully!', 'success')

    categories = Category.query.all()
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return render_template('expenses.html', categories=categories, expenses=expenses)

@app.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    if request.method == 'POST':
        category_id = int(request.form.get('category'))
        amount = float(request.form.get('amount'))
        notify_threshold = float(request.form.get('notify_threshold', 90))  # Default to 90% if not provided

        existing_budget = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=category_id
        ).first()

        if existing_budget:
            existing_budget.amount = amount
            existing_budget.notify_threshold = notify_threshold
        else:
            new_budget = Budget(
                user_id=current_user.id,
                category_id=category_id,
                amount=amount,
                notify_threshold=notify_threshold
            )
            db.session.add(new_budget)

        db.session.commit()
        flash('Budget updated successfully!', 'success')

    categories = Category.query.all()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    return render_template('budget.html', categories=categories, budgets=budgets)

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    message = request.json.get('message', '').lower()
    if not message:
        return jsonify({'response': 'Please provide a message'}), 400

    try:
        # Handle different types of financial queries
        if any(word in message for word in ['simulate', 'job', 'income']):
            response = simulate_financial_scenario(message, current_user)
        elif any(word in message for word in ['worth', 'buy', 'purchase']):
            # Extract price from message if available
            import re
            price_match = re.search(r'\$?(\d+(?:\.\d{2})?)', message)
            price = float(price_match.group(1)) if price_match else 0
            response = analyze_purchase_value(message, price, current_user)
        elif any(word in message for word in ['overspend', 'spent', 'spending']):
            response = analyze_expense_cause(current_user)
        else:
            # General financial advice
            response = analyze_spending_patterns(current_user)

        return jsonify({'response': response})
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'response': 'Sorry, I encountered an error. Please try again later.'}), 500

# Initialize database
with app.app_context():
    db.create_all()

    # Create default categories if they don't exist
    default_categories = ['Food', 'Transportation', 'Education', 'Entertainment', 'Utilities']
    for category_name in default_categories:
        if not Category.query.filter_by(name=category_name).first():
            category = Category(name=category_name)
            db.session.add(category)
    db.session.commit()