import urllib.parse
import json
from django.db.models import Sum, Count
from datetime import datetime, timedelta

class QuickChartService:
    """Service class for generating QuickChart URLs"""
    
    @staticmethod
    def generate_chart_url(chart_config, width=600, height=400, format='png'):
        """Generate QuickChart URL from chart configuration"""
        encoded_config = urllib.parse.quote(json.dumps(chart_config))
        return f"https://quickchart.io/chart?c={encoded_config}&width={width}&height={height}&format={format}"
    
    @staticmethod
    def generate_monthly_trend_chart(expenses, width=800, height=400):
        """Generate monthly spending trend chart"""
        if not expenses:
            return None
        
        # Process monthly data
        monthly_data = {}
        for expense in expenses:
            month_key = expense.expense_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = 0
            monthly_data[month_key] += float(expense.amount)
        
        # Sort by month and get last 6 months
        sorted_months = sorted(monthly_data.keys())[-6:]
        labels = [datetime.strptime(month, '%Y-%m').strftime('%b %Y') for month in sorted_months]
        data = [monthly_data[month] for month in sorted_months]
        
        chart_config = {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Monthly Spending',
                    'data': data,
                    'backgroundColor': 'rgba(255, 107, 107, 0.1)',
                    'borderColor': 'rgba(255, 107, 107, 1)',
                    'borderWidth': 3,
                    'tension': 0.4,
                    'fill': True,
                    'pointBackgroundColor': 'rgba(255, 107, 107, 1)',
                    'pointBorderColor': '#ffffff',
                    'pointBorderWidth': 2,
                    'pointRadius': 5
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': '📈 Monthly Spending Trends',
                        'font': {'size': 16, 'weight': 'bold'}
                    },
                    'legend': {
                        'display': True,
                        'position': 'top'
                    },
                    'tooltip': {
                        'mode': 'index',
                        'intersect': False,
                        'callbacks': {
                            'label': 'function(context) { return `$${context.parsed.y.toFixed(2)}`; }'
                        }
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Amount ($)',
                            'font': {'weight': 'bold'}
                        },
                        'ticks': {
                            'callback': 'function(value) { return `$${value}`; }'
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Month',
                            'font': {'weight': 'bold'}
                        }
                    }
                }
            }
        }
        
        return QuickChartService.generate_chart_url(chart_config, width, height)
    
    @staticmethod
    def generate_category_pie_chart(expenses, width=600, height=400):
        """Generate category-wise donut chart"""
        if not expenses:
            return None
        
        # Process category data
        category_data = {}
        for expense in expenses:
            category_name = expense.category.name
            if category_name not in category_data:
                category_data[category_name] = 0
            category_data[category_name] += float(expense.amount)
        
        # Sort by amount (descending) and take top 8 categories
        sorted_categories = sorted(category_data.items(), key=lambda x: x[1], reverse=True)[:8]
        labels = [item[0] for item in sorted_categories]
        data = [round(item[1], 2)for item in sorted_categories]
        
        chart_config = {
            'type': 'doughnut',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': data,
                    'backgroundColor': [
                        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFEAA7', 
                        '#DDA0DD', '#98D8C8', '#F7DC6F', '#FF9F45'
                    ],
                    'borderColor': '#ffffff',
                    'borderWidth': 3,
                    'hoverOffset': 8
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': '🥧 Spending by Category',
                        'font': {'size': 16, 'weight': 'bold'}
                    },
                    'legend': {
                        'position': 'right',
                        'labels': {
                            'font': {'size': 12},
                            'usePointStyle': True,
                            'padding': 20
                        }
                    },
                    'tooltip': {
                        'callbacks': {
                            'label': 'function(context) { const label = context.label || ""; const value = context.parsed || 0; const total = context.dataset.data.reduce((a, b) => a + b, 0); const percentage = ((value / total) * 100).toFixed(1); return `${label}: $${value.toFixed(2)} (${percentage}%)`; }'
                        }
                    }
                },
                'cutout': '60%'
            }
        }
        
        return QuickChartService.generate_chart_url(chart_config, width, height)
    
    @staticmethod
    def generate_budget_comparison_chart(budgets, expenses, width=800, height=400):
        """Generate budget vs actual comparison chart"""
        if not budgets:
            return None
        
        comparison_data = []
        
        for budget in budgets:
            budget_categories = budget.budget_categories.all()
            for bc in budget_categories:
                # Calculate actual spending
                actual_spent = expenses.filter(
                    category=bc.category,
                    expense_date__range=[budget.start_date, budget.end_date]
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                comparison_data.append({
                    'category': bc.category.name,
                    'budgeted': float(bc.allocated_amount),
                    'actual': float(actual_spent)
                })
        
        if not comparison_data:
            return None
        
        # Aggregate by category
        category_totals = {}
        for item in comparison_data:
            category = item['category']
            if category not in category_totals:
                category_totals[category] = {'budgeted': 0, 'actual': 0}
            category_totals[category]['budgeted'] += item['budgeted']
            category_totals[category]['actual'] += item['actual']
        
        categories = list(category_totals.keys())
        budgeted_data = [category_totals[cat]['budgeted'] for cat in categories]
        actual_data = [category_totals[cat]['actual'] for cat in categories]
        
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': categories,
                'datasets': [
                    {
                        'label': '💰 Budgeted',
                        'data': budgeted_data,
                        'backgroundColor': 'rgba(54, 162, 235, 0.8)',
                        'borderColor': 'rgba(54, 162, 235, 1)',
                        'borderWidth': 1
                    },
                    {
                        'label': '💸 Actual',
                        'data': actual_data,
                        'backgroundColor': 'rgba(255, 99, 132, 0.8)',
                        'borderColor': 'rgba(255, 99, 132, 1)',
                        'borderWidth': 1
                    }
                ]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': '📊 Budget vs Actual Spending',
                        'font': {'size': 16, 'weight': 'bold'}
                    },
                    'legend': {
                        'position': 'top'
                    },
                    'tooltip': {
                        'callbacks': {
                            'label': 'function(context) { return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`; }'
                        }
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Amount ($)',
                            'font': {'weight': 'bold'}
                        },
                        'ticks': {
                            'callback': 'function(value) { return `$${value}`; }'
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Categories',
                            'font': {'weight': 'bold'}
                        }
                    }
                }
            }
        }
        
        return QuickChartService.generate_chart_url(chart_config, width, height)
    
    @staticmethod
    def generate_income_vs_expenses_chart(expenses, incomes, width=600, height=400):
        """Generate income vs expenses comparison"""
        total_expenses = sum(float(exp.amount) for exp in expenses) if expenses else 0
        total_income = sum(float(inc.amount) for inc in incomes) if incomes else 0
        
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': ['Income vs Expenses'],
                'datasets': [
                    {
                        'label': '💰 Total Income',
                        'data': [total_income],
                        'backgroundColor': 'rgba(75, 192, 192, 0.8)',
                        'borderColor': 'rgba(75, 192, 192, 1)',
                        'borderWidth': 1
                    },
                    {
                        'label': '💸 Total Expenses',
                        'data': [total_expenses],
                        'backgroundColor': 'rgba(255, 99, 132, 0.8)',
                        'borderColor': 'rgba(255, 99, 132, 1)',
                        'borderWidth': 1
                    }
                ]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': '💰 Income vs Expenses',
                        'font': {'size': 16, 'weight': 'bold'}
                    },
                    'legend': {
                        'position': 'top'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Amount ($)',
                            'font': {'weight': 'bold'}
                        },
                        'ticks': {
                            'callback': 'function(value) { return `$${value}`; }'
                        }
                    }
                }
            }
        }
        
        return QuickChartService.generate_chart_url(chart_config, width, height)