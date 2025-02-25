
// Auto-fill budget form based on selected category
document.addEventListener('DOMContentLoaded', function() {
    const categorySelect = document.getElementById('category');
    const amountInput = document.getElementById('amount');
    const thresholdInput = document.getElementById('notify_threshold');

    function updateFormValues() {
        const selectedOption = categorySelect.options[categorySelect.selectedIndex];
        const amount = selectedOption.getAttribute('data-amount');
        const threshold = selectedOption.getAttribute('data-threshold');
        
        if (amount) {
            amountInput.value = amount;
        } else {
            amountInput.value = '';
        }
        
        thresholdInput.value = threshold;
    }

    // Update on page load
    updateFormValues();

    // Update when category changes
    categorySelect.addEventListener('change', updateFormValues);
});


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

document.addEventListener('DOMContentLoaded', function() {
    // Handle goal updates
    document.querySelectorAll('.update-goal').forEach(button => {
        button.addEventListener('click', function() {
            const goalId = this.dataset.goalId;
            const amount = prompt('Enter current amount saved:');

            if (amount !== null && !isNaN(amount)) {
                fetch(`/goals/update/${goalId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `current_amount=${amount}`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update the progress bar
                        const goalCard = this.closest('.card');
                        const progressBar = goalCard.querySelector('.progress-bar');
                        progressBar.style.width = data.progress + '%';
                        progressBar.setAttribute('aria-valuenow', data.progress);
                        progressBar.textContent = data.progress + '%';

                        // Update status if completed
                        if (data.status === 'completed') {
                            progressBar.classList.remove('bg-primary', 'bg-info');
                            progressBar.classList.add('bg-success');
                        }

                        // Refresh the page to update all information
                        location.reload();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to update goal progress');
                });
            }
        });
    });
});