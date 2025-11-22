/* Dashboard Charts and Interactions */

let spendingChart;
let categoryChart;

// Initialize charts on page load
document.addEventListener('DOMContentLoaded', function() {
    initSpendingChart('yearly');
    initCategoryChart();
});

// Spending Trends Chart
function initSpendingChart(type) {
    const ctx = document.getElementById('spendingTrendsChart');
    if (!ctx) return;
    
    if (spendingChart) {
        spendingChart.destroy();
    }

    const data = type === 'yearly' ? spendingTrendsData : currentMonthData;
    const tooltipLabels = type === 'monthly' ? currentMonthData.tooltip_labels : null;

    spendingChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Expenses',
                data: data.data,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#667eea',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: '#1F2937',
                    titleColor: '#F9FAFB',
                    bodyColor: '#F9FAFB',
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            if (tooltipLabels && context[0]) {
                                return tooltipLabels[context[0].dataIndex];
                            }
                            return context[0].label;
                        },
                        label: function(context) {
                            return dashboardCurrency + ' ' + context.parsed.y.toLocaleString('en-US', {minimumFractionDigits: 2});
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                    },
                    ticks: {
                        maxRotation: 0,
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return dashboardCurrency + ' ' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Toggle between yearly and monthly view
function toggleTrendsChart(type) {
    initSpendingChart(type);
    
    const btnYearly = document.getElementById('btn-yearly');
    const btnMonthly = document.getElementById('btn-monthly');
    
    if (type === 'yearly') {
        btnYearly.classList.add('active');
        btnMonthly.classList.remove('active');
    } else {
        btnMonthly.classList.add('active');
        btnYearly.classList.remove('active');
    }
}

// Category Donut Chart
function initCategoryChart() {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;
    
    // Handle empty data
    if (!categoryData.data || categoryData.data.length === 0) {
        ctx.parentElement.innerHTML = '<div class="text-center text-muted py-5"><i class="bi bi-pie-chart fs-1 mb-2 d-block opacity-50"></i>No expenses this month</div>';
        return;
    }
    
    categoryChart = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: categoryData.labels,
            datasets: [{
                data: categoryData.data,
                backgroundColor: categoryData.colors,
                borderWidth: 0,
                hoverOffset: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: '#1F2937',
                    titleColor: '#F9FAFB',
                    bodyColor: '#F9FAFB',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return dashboardCurrency + ' ' + context.parsed.toLocaleString('en-US', {minimumFractionDigits: 2}) + ' (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });

    // Build custom legend
    buildCategoryLegend();
}

// Custom legend for category chart
function buildCategoryLegend() {
    const legendContainer = document.getElementById('categoryLegend');
    if (!legendContainer) return;
    
    if (!categoryData.labels || categoryData.labels.length === 0) {
        legendContainer.innerHTML = '';
        return;
    }
    
    legendContainer.innerHTML = '';
    const total = categoryData.data.reduce((a, b) => a + b, 0);

    categoryData.labels.forEach((label, index) => {
        const percentage = total > 0 ? ((categoryData.data[index] / total) * 100).toFixed(0) : 0;
        
        const item = document.createElement('div');
        item.className = 'category-legend-item';
        item.innerHTML = `
            <div class="d-flex align-items-center">
                <span class="category-dot" style="background-color: ${categoryData.colors[index]}"></span>
                <span class="text-muted">${label}</span>
            </div>
            <span class="fw-semibold">${percentage}%</span>
        `;
        legendContainer.appendChild(item);
    });
}

/* Transaction Modal Functions */

function openCreateIncomeModal() {
    document.getElementById('incomeForm').reset();
    document.getElementById('income-id').value = '';
    document.getElementById('incomeModalLabel').textContent = 'Add Income';
    document.getElementById('income-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('income-currency').value = dashboardCurrency;
    
    const modal = new bootstrap.Modal(document.getElementById('incomeModal'));
    modal.show();
}

function openCreateExpenseModal() {
    document.getElementById('expenseForm').reset();
    document.getElementById('expense-id').value = '';
    document.getElementById('expenseModalLabel').textContent = 'Add Expense';
    document.getElementById('expense-date').value = new Date().toISOString().split('T')[0];
    document.getElementById('expense-currency').value = dashboardCurrency;
    
    const modal = new bootstrap.Modal(document.getElementById('expenseModal'));
    modal.show();
}

function saveIncome() {
    const data = {
        source_id: document.getElementById('income-source').value,
        amount: document.getElementById('income-amount').value,
        currency: document.getElementById('income-currency').value,
        transaction_date: document.getElementById('income-date').value,
        description: document.getElementById('income-description').value,
        status: document.getElementById('income-status').value,
    };
    
    fetch('/api/income/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred');
    });
}

function saveExpense() {
    const data = {
        category_id: document.getElementById('expense-category').value,
        amount: document.getElementById('expense-amount').value,
        currency: document.getElementById('expense-currency').value,
        transaction_date: document.getElementById('expense-date').value,
        description: document.getElementById('expense-description').value,
        status: document.getElementById('expense-status').value,
        budget_id: document.getElementById('expense-budget').value || null,
    };
    
    fetch('/api/expense/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred');
    });
}