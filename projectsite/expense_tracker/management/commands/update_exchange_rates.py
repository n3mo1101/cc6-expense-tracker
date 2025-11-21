"""
Management command to update exchange rates.
Run with: python manage.py update_exchange_rates

Can be scheduled as a daily cron job or run manually.
"""

from django.core.management.base import BaseCommand
from expense_tracker.services.currency_service import CurrencyService


class Command(BaseCommand):
    help = 'Fetch and update currency exchange rates from API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh even if cache is still valid',
        )

    def handle(self, *args, **options):
        self.stdout.write('Updating exchange rates...\n')
        
        try:
            if options['force']:
                CurrencyService.force_refresh()
            else:
                CurrencyService._refresh_cache_if_needed()
            
            # Display current rates
            currencies = CurrencyService.get_all_currencies()
            
            self.stdout.write(self.style.SUCCESS(f'\nCached {len(currencies)} currencies:'))
            for currency in currencies:
                self.stdout.write(f"  {currency['code']}: {currency['name']}")
            
            self.stdout.write(self.style.SUCCESS('\nExchange rates updated successfully!'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error updating rates: {e}'))