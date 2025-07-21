from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone


class Command(BaseCommand):
    help = 'List admin users for the SMS-to-AI Agent dashboard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Show only active users',
        )

    def handle(self, *args, **options):
        active_only = options.get('active_only', False)

        # Get admin users (staff or superuser)
        admin_users = User.objects.filter(
            models_Q(is_staff=True) | models_Q(is_superuser=True)
        )

        if active_only:
            admin_users = admin_users.filter(is_active=True)

        admin_users = admin_users.order_by('username')

        if not admin_users.exists():
            self.stdout.write(
                self.style.WARNING('No admin users found.')
            )
            self.stdout.write('')
            self.stdout.write('Create an admin user with:')
            self.stdout.write('  python manage.py create_admin')
            return

        self.stdout.write(
            self.style.SUCCESS('Admin Users for SMS-to-AI Agent Dashboard:')
        )
        self.stdout.write('')

        # Table header
        self.stdout.write(
            f"{'Username':<20} {'Email':<30} {'Type':<10} {'Active':<8} {'Last Login':<20}"
        )
        self.stdout.write('-' * 90)

        for user in admin_users:
            user_type = 'superuser' if user.is_superuser else 'staff'
            active_status = 'Yes' if user.is_active else 'No'
            last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
            
            self.stdout.write(
                f"{user.username:<20} {user.email or 'N/A':<30} {user_type:<10} {active_status:<8} {last_login:<20}"
            )

        self.stdout.write('')
        self.stdout.write(f'Total admin users: {admin_users.count()}')
        
        if not active_only:
            inactive_count = admin_users.filter(is_active=False).count()
            if inactive_count > 0:
                self.stdout.write(f'Inactive users: {inactive_count}')


# Import Q from django.db.models
from django.db import models
models_Q = models.Q 