// Show notifications when budget limits are approached
function checkBudgetLimits() {
    const expenses = document.querySelectorAll('[data-expense]');
    const budgets = document.querySelectorAll('[data-budget]');
    
    expenses.forEach((expense, index) => {
        const expenseAmount = parseFloat(expense.dataset.expense);
        const budgetAmount = parseFloat(budgets[index].dataset.budget);
        const category = expense.dataset.category;
        
        if (expenseAmount >= budgetAmount * 0.9) {
            showNotification(`Warning: You've reached 90% of your ${category} budget!`, 'warning');
        }
        if (expenseAmount > budgetAmount) {
            showNotification(`Alert: You've exceeded your ${category} budget!`, 'danger');
        }
    });
}

// Display toast notifications
function showNotification(message, type) {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    checkBudgetLimits();
});
