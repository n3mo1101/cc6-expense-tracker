import os
import requests
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from expense_tracker.models import CurrencyCache


# ============================================================================
# CONFIGURATION
# ============================================================================

# FreecurrencyAPI - Free tier: 5,000 requests/month
# Sign up at: https://freecurrencyapi.com/
API_BASE_URL = 'https://api.freecurrencyapi.com/v1'
API_KEY = getattr(settings, 'CURRENCY_API_KEY', None) or os.getenv('CURRENCY_API_KEY', '')

# Cache duration (24 hours)
CACHE_DURATION_HOURS = 24

# Common currencies to support
COMMON_CURRENCIES = {
    'PHP': 'Philippine Peso',
    'USD': 'US Dollar',
    'EUR': 'Euro',
    'GBP': 'British Pound',
    'JPY': 'Japanese Yen',
    'AUD': 'Australian Dollar',
    'CAD': 'Canadian Dollar',
    'CHF': 'Swiss Franc',
    'CNY': 'Chinese Yuan',
    'SGD': 'Singapore Dollar',
}


# ============================================================================
# CURRENCY SERVICE
# ============================================================================

class CurrencyService:
    """Service for handling currency operations."""

    @classmethod
    def convert(cls, amount, from_currency, to_currency):
        # Convert amount from one currency to another.
        amount = Decimal(str(amount))
        
        # Same currency, no conversion needed
        if from_currency == to_currency:
            return {
                'converted_amount': amount,
                'rate': Decimal('1.00')
            }
        
        # Ensure cache is fresh
        cls._refresh_cache_if_needed()
        
        # Get rates
        from_rate = cls._get_rate(from_currency)
        to_rate = cls._get_rate(to_currency)
        
        if from_rate is None:
            raise ValueError(f"Invalid currency code: {from_currency}")
        if to_rate is None:
            raise ValueError(f"Invalid currency code: {to_currency}")
        
        # Convert: amount -> USD -> target currency
        # Formula: amount / from_rate * to_rate
        rate = (to_rate / from_rate).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
        converted = (amount * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return {
            'converted_amount': converted,
            'rate': rate
        }

    @classmethod
    def is_valid_currency(cls, currency_code):
        """Check if a currency code is valid."""
        cls._refresh_cache_if_needed()
        return CurrencyCache.objects.filter(code=currency_code.upper()).exists()

    @classmethod
    def get_all_currencies(cls):
        """Get list of all valid currencies."""
        cls._refresh_cache_if_needed()
        return list(
            CurrencyCache.objects.all().values('code', 'name').order_by('code')
        )

    @classmethod
    def get_currency_choices(cls):
        """Get currencies as Django choices tuple."""
        cls._refresh_cache_if_needed()
        currencies = CurrencyCache.objects.all().order_by('code')
        return [(c.code, f"{c.code} - {c.name}") for c in currencies]

    @classmethod
    def _get_rate(cls, currency_code):
        """Get exchange rate for a currency from cache."""
        try:
            currency = CurrencyCache.objects.get(code=currency_code.upper())
            return currency.exchange_rate
        except CurrencyCache.DoesNotExist:
            return None

    @classmethod
    def _refresh_cache_if_needed(cls):
        """Refresh cache if older than CACHE_DURATION_HOURS."""
        try:
            latest = CurrencyCache.objects.order_by('-last_updated').first()
            
            if latest is None:
                # No cache exists, fetch from API
                cls._fetch_and_cache_rates()
            elif timezone.now() - latest.last_updated > timedelta(hours=CACHE_DURATION_HOURS):
                # Cache is stale, refresh
                cls._fetch_and_cache_rates()
        except Exception as e:
            # If refresh fails, continue with existing cache
            print(f"Warning: Could not refresh currency cache: {e}")

    @classmethod
    def _fetch_and_cache_rates(cls):
        """Fetch latest rates from API and update cache."""
        try:
            # Build currency list for API request
            currencies = ','.join(COMMON_CURRENCIES.keys())
            
            response = requests.get(
                f"{API_BASE_URL}/latest",
                params={
                    'apikey': API_KEY,
                    'currencies': currencies,
                    'base_currency': 'USD'
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data:
                # Update cache
                for code, rate in data['data'].items():
                    CurrencyCache.objects.update_or_create(
                        code=code,
                        defaults={
                            'name': COMMON_CURRENCIES.get(code, code),
                            'exchange_rate': Decimal(str(rate))
                        }
                    )
                
                # Ensure USD is in cache (base currency, rate = 1)
                CurrencyCache.objects.update_or_create(
                    code='USD',
                    defaults={
                        'name': 'US Dollar',
                        'exchange_rate': Decimal('1.00')
                    }
                )
                
                print(f"Currency cache updated: {len(data['data'])} currencies")
        
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            # Fall back to defaults if no cache exists
            cls._populate_fallback_rates()
        
        except Exception as e:
            print(f"Error updating currency cache: {e}")
            cls._populate_fallback_rates()

    @classmethod
    def _populate_fallback_rates(cls):
        """Populate with fallback rates if API fails and cache is empty."""
        if CurrencyCache.objects.exists():
            return  # Use existing cache
        
        # Approximate fallback rates (as of 2024)
        fallback_rates = {
            'USD': ('US Dollar', Decimal('1.00')),
            'PHP': ('Philippine Peso', Decimal('56.50')),
            'EUR': ('Euro', Decimal('0.92')),
            'GBP': ('British Pound', Decimal('0.79')),
            'JPY': ('Japanese Yen', Decimal('154.50')),
            'AUD': ('Australian Dollar', Decimal('1.53')),
            'CAD': ('Canadian Dollar', Decimal('1.36')),
            'CHF': ('Swiss Franc', Decimal('0.88')),
            'CNY': ('Chinese Yuan', Decimal('7.24')),
            'SGD': ('Singapore Dollar', Decimal('1.34')),
        }
        
        for code, (name, rate) in fallback_rates.items():
            CurrencyCache.objects.update_or_create(
                code=code,
                defaults={'name': name, 'exchange_rate': rate}
            )
        
        print("Currency cache populated with fallback rates")

    @classmethod
    def force_refresh(cls):
        """Force refresh the cache regardless of age."""
        cls._fetch_and_cache_rates()