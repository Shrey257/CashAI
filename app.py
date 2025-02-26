import os
import logging
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

from extensions import db
from models import User, Expense, Budget, Category, FinancialGoal # Added FinancialGoal import
from services.ai_service import (
    analyze_spending_patterns, 
    generate_saving_tip,
    simulate_financial_scenario,
    analyze_expense_cause,
    categorize_transaction
)
from services.voice_service import voice_assistant

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure SQLAlchemy with PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database
with app.app_context():
    # Create all database tables
    db.create_all()

    # Create default categories with recommended student budget amounts
    default_categories = [
        ('🍽️ Food', 350),  # Monthly food budget including groceries and dining
        ('🚌 Transportation', 125),  # Public transit, ride-sharing
        ('📚 Education', 175),  # Books, supplies, software
        ('🎮 Entertainment', 75),  # Social activities, streaming services
        ('🏠 Utilities', 75),  # Phone, internet, shared utilities
    ]

    for category_name, default_amount in default_categories:
        if not Category.query.filter_by(name=category_name).first():
            category = Category(name=category_name)
            db.session.add(category)
            db.session.commit()  # Commit to get the category ID

            # Get all users and create default budgets for them
            users = User.query.all()
            for user in users:
                if not Budget.query.filter_by(user_id=user.id, category_id=category.id).first():
                    budget = Budget(
                        amount=default_amount,
                        category_id=category.id,
                        user_id=user.id,
                        notify_threshold=90.0
                    )
                    db.session.add(budget)

    db.session.commit()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get recent expenses and budgets
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5).all()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    goals = FinancialGoal.query.filter_by(user_id=current_user.id).order_by(FinancialGoal.created_at.desc()).all()

    try:
        from services.expense_predictor import predict_monthly_expenses
        from services.goals_advisor import suggest_saving_strategies
        
        # Get AI-generated insights and predictions
        ai_insights = analyze_spending_patterns(current_user)
        saving_tip = generate_saving_tip()
        expense_predictions = predict_monthly_expenses(current_user)
        
        # Get saving strategies for each goal
        goal_strategies = {}
        for goal in goals:
            goal_strategies[goal.id] = suggest_saving_strategies(current_user, goal)
    except Exception as e:
        logging.error(f"Error generating AI insights: {str(e)}")
        ai_insights = "• Start by tracking your daily expenses to understand your spending patterns\n• Set budgets for different categories to manage your finances better\n• Look for student discounts and deals to save money"
        saving_tip = "Consider using student discounts and comparing prices before making purchases to maximize your savings."

    return render_template('dashboard.html', 
                         expenses=expenses, 
                         budgets=budgets,
                         goals=goals,
                         ai_insights=ai_insights,
                         saving_tip=saving_tip,
                         expense_predictions=expense_predictions,
                         goal_strategies=goal_strategies)

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        message = request.json.get('message', '').lower()
        if not message:
            return jsonify({'response': 'Please ask me a question about your finances.'}), 400

        # Handle different types of financial queries
        # Enhanced topic detection for more varied responses
        if any(word in message for word in ['budget', 'plan', 'allocate']):
            response = analyze_spending_patterns(current_user)
        elif any(word in message for word in ['save', 'saving', 'savings', 'tips']):
            response = generate_saving_tip()
        elif any(word in message for word in ['invest', 'investment', 'stock', 'future']):
            response = simulate_financial_scenario("investment advice " + message, current_user)
        elif any(word in message for word in ['debt', 'loan', 'credit']):
            response = simulate_financial_scenario("debt management " + message, current_user)
        elif any(word in message for word in ['earn', 'job', 'income', 'work']):
            response = simulate_financial_scenario("income opportunities " + message, current_user)
        elif any(word in message for word in ['emergency', 'fund', 'safety']):
            response = simulate_financial_scenario("emergency fund " + message, current_user)
        elif any(word in message for word in ['overspend', 'spent', 'spending']):
            response = analyze_expense_cause(current_user)
        else:
            # General financial advice with enhanced context
            response = analyze_spending_patterns(current_user)

        if not response or response.isspace():
            response = "I'm here to help you with budgeting, expense tracking, and financial advice. What would you like to know?"

        return jsonify({'response': response})
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'response': "I'm having trouble processing your request right now. Let me know if you'd like tips on budgeting, saving, or expense tracking."
        }), 500

@app.route('/api/voice/process', methods=['POST'])
@login_required
def process_voice():
    try:
        # Get audio data from request
        audio_data = np.array(request.json.get('audio'), dtype=np.float32)

        # Convert speech to text
        text = voice_assistant.listen(audio_data)

        # Generate response
        response_text = voice_assistant.generate_response(text, current_user)

        # Convert response to speech
        audio_response = voice_assistant.speak(response_text)

        return jsonify({
            'text': text,
            'response': response_text,
            'audio': audio_response
        })
    except Exception as e:
        logging.error(f"Error in voice processing: {str(e)}")
        return jsonify({'error': str(e)}), 500


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
            # Try to find an existing category that matches
            category = Category.query.filter(Category.name.ilike(f'%{suggested_category}%')).first()
            if category:
                category_id = category.id
            else:
                # Default to 'Other' or first category if suggestion fails
                category = Category.query.filter(Category.name.ilike('%other%')).first()
                if not category:
                    category = Category.query.first()
                category_id = category.id
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
        notify_threshold = float(request.form.get('notify_threshold', 90))

        existing_budget = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=category_id
        ).first()

        if existing_budget:
            existing_budget.amount = amount
            existing_budget.notify_threshold = notify_threshold
            db.session.commit()
            flash('Budget updated successfully!', 'success')
        else:
            new_budget = Budget(
                user_id=current_user.id,
                category_id=category_id,
                amount=amount,
                notify_threshold=notify_threshold
            )
            db.session.add(new_budget)
            db.session.commit()
            flash('Budget created successfully!', 'success')

    categories = Category.query.all()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    return render_template('budget.html', categories=categories, budgets=budgets)

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

        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/goals/add', methods=['POST'])
@login_required
def add_goal():
    try:
        name = request.form.get('name')
        target_amount = float(request.form.get('target_amount'))
        deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d')

        goal = FinancialGoal(
            name=name,
            target_amount=target_amount,
            deadline=deadline,
            user_id=current_user.id
        )

        db.session.add(goal)
        db.session.commit()
        flash('Financial goal added successfully!', 'success')
    except Exception as e:
        logging.error(f"Error adding financial goal: {str(e)}")
        flash('Error adding financial goal. Please try again.', 'danger')

    return redirect(url_for('dashboard'))

@app.route('/goals/update/<int:goal_id>', methods=['POST'])
@login_required
def update_goal(goal_id):
    try:
        goal = FinancialGoal.query.get_or_404(goal_id)
        if goal.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        current_amount = float(request.form.get('current_amount'))
        goal.current_amount = current_amount

        if current_amount >= goal.target_amount:
            goal.status = 'completed'
        elif goal.deadline < datetime.now() and current_amount < goal.target_amount:
            goal.status = 'missed'

        db.session.commit()
        return jsonify({
            'success': True,
            'progress': int((current_amount / goal.target_amount) * 100),
            'status': goal.status
        })
    except Exception as e:
        logging.error(f"Error updating goal: {str(e)}")
        return jsonify({'error': 'Failed to update goal'}), 500