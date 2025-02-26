
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from models import Expense

def predict_monthly_expenses(user):
    """Predict next month's expenses using historical data"""
    expenses = Expense.query.filter_by(user_id=user.id).all()
    
    # Prepare training data
    dates = np.array([(e.date - datetime.now()).days for e in expenses]).reshape(-1, 1)
    amounts = np.array([e.amount for e in expenses])
    
    # Train model
    model = LinearRegression()
    model.fit(dates, amounts)
    
    # Predict next 30 days
    future_dates = np.array(range(1, 31)).reshape(-1, 1)
    predictions = model.predict(future_dates)
    
    return {
        'total_predicted': sum(predictions),
        'daily_breakdown': [{'day': i, 'amount': amount} for i, amount in enumerate(predictions, 1)]
    }
