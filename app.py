import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Database configuration
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///budget.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Login manager configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models after db initialization
from models import User, Expense, Budget, Category

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
    return render_template('dashboard.html', expenses=expenses, budgets=budgets)

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        category_id = int(request.form.get('category'))
        description = request.form.get('description')
        
        expense = Expense(
            amount=amount,
            category_id=category_id,
            description=description,
            user_id=current_user.id,
            date=datetime.now()
        )
        
        db.session.add(expense)
        db.session.commit()
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
        
        existing_budget = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=category_id
        ).first()
        
        if existing_budget:
            existing_budget.amount = amount
        else:
            new_budget = Budget(
                user_id=current_user.id,
                category_id=category_id,
                amount=amount
            )
            db.session.add(new_budget)
            
        db.session.commit()
        flash('Budget updated successfully!', 'success')
        
    categories = Category.query.all()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    return render_template('budget.html', categories=categories, budgets=budgets)

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
