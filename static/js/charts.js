function initializeCharts() {
    const ctx = document.getElementById('expenseChart').getContext('2d');
    
    // Collect data from the page
    const categories = Array.from(document.querySelectorAll('[data-category]')).map(el => el.dataset.category);
    const expenses = Array.from(document.querySelectorAll('[data-expense]')).map(el => parseFloat(el.dataset.expense));
    const budgets = Array.from(document.querySelectorAll('[data-budget]')).map(el => parseFloat(el.dataset.budget));

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [
                {
                    label: 'Expenses',
                    data: expenses,
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Budget',
                    data: budgets,
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', initializeCharts);
