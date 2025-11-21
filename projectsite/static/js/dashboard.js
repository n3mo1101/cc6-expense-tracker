let spendingChart;
let categoryChart;

// Initialize charts on page load
document.addEventListener('DOMContentLoaded', function() {
    initSpendingChart('yearly');
    initCategoryChart();
});

// Spending Trends Chart
function initSpendingChart(type) {
    const ctx = document.getElementById('spendingTrendsChart').getContext('2d');
    
    if (spendingChart) {
        spendingChart.destroy();
    }

    const data = type === 'yearly' ? spendingTrendsData : currentMonthData;
    const tooltipLabels = type === 'monthly' ? currentMonthData.tooltip_labels : null;

    spendingChart = new Chart(ctx, {
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
                            return currency + ' ' + context.parsed.y.toLocaleString('en-US', {minimumFractionDigits: 2});
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
                            return currency + ' ' + value.toLocaleString();
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
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    // Handle empty data
    if (!categoryData.data || categoryData.data.length === 0) {
        document.getElementById('categoryChart').parentElement.innerHTML = '<div class="text-center text-muted py-5"><i class="bi bi-pie-chart fs-1 mb-2 d-block opacity-50"></i>No expenses this month</div>';
        return;
    }
    
    categoryChart = new Chart(ctx, {
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
                            return currency + ' ' + context.parsed.toLocaleString('en-US', {minimumFractionDigits: 2}) + ' (' + percentage + '%)';
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