from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from expense_tracker.models import PredefinedDataManager, UserProfile

class Command(BaseCommand):
    help = 'Create predefined categories and income sources for existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Create predefined data for specific username',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Create predefined data for all existing users',
        )

    def handle(self, *args, **options):
        if options['username']:
            try:
                user = User.objects.get(username=options['username'])
                PredefinedDataManager.create_predefined_data_for_user(user)
                self.stdout.write(
                    self.style.SUCCESS(f'Predefined data created for user: {user.username}')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User {options["username"]} does not exist')
                )
        
        elif options['all']:
            users = User.objects.all()
            for user in users:
                profile, created = UserProfile.objects.get_or_create(user=user)
                if not profile.has_predefined_data:
                    PredefinedDataManager.create_predefined_data_for_user(user)
                    self.stdout.write(
                        self.style.SUCCESS(f'Predefined data created for user: {user.username}')
                    )
        else:
            self.stdout.write(
                self.style.WARNING('Please specify --username or --all flag')
            )