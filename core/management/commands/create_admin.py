from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import getpass


class Command(BaseCommand):
    help = 'Create an admin user for the SMS-to-AI Agent dashboard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the admin user',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the admin user',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the admin user (not recommended for security)',
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Create a superuser instead of staff user',
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            default=True,
            help='Run in interactive mode (default)',
        )
        parser.add_argument(
            '--no-input',
            action='store_false',
            dest='interactive',
            help='Run in non-interactive mode',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')
        is_superuser = options.get('superuser', False)
        interactive = options.get('interactive', True)

        if interactive:
            self.stdout.write(
                self.style.SUCCESS('Creating admin user for SMS-to-AI Agent Dashboard')
            )
            self.stdout.write('')

            # Get username
            if not username:
                username = input('Username: ')
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                raise CommandError(f'User with username "{username}" already exists.')

            # Get email
            if not email:
                email = input('Email (optional): ')
                if not email:
                    email = None

            # Get password
            if not password:
                password = None
                while not password:
                    password = getpass.getpass('Password: ')
                    if not password:
                        self.stdout.write('Password cannot be empty.')
                        continue
                    
                    try:
                        validate_password(password)
                    except ValidationError as e:
                        self.stdout.write(
                            self.style.ERROR('Password validation failed:')
                        )
                        for error in e.messages:
                            self.stdout.write(f'  - {error}')
                        password = None
                        continue
                    
                    password_confirm = getpass.getpass('Password (again): ')
                    if password != password_confirm:
                        self.stdout.write('Passwords do not match.')
                        password = None

            # Confirm user type
            if not is_superuser:
                user_type = input('Create superuser? (y/n) [n]: ').lower()
                is_superuser = user_type.startswith('y')

        else:
            # Non-interactive mode
            if not username:
                raise CommandError('Username is required in non-interactive mode.')
            
            if User.objects.filter(username=username).exists():
                raise CommandError(f'User with username "{username}" already exists.')
            
            if not password:
                raise CommandError('Password is required in non-interactive mode.')

        try:
            # Create the user
            if is_superuser:
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                user_type_str = "superuser"
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                user.is_staff = True
                user.save()
                user_type_str = "staff user"

            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {user_type_str}: {username}'
                )
            )
            
            self.stdout.write('')
            self.stdout.write('You can now login to the dashboard at:')
            self.stdout.write('  http://localhost:5001/dashboard/')
            self.stdout.write('')
            self.stdout.write('Credentials:')
            self.stdout.write(f'  Username: {username}')
            self.stdout.write('  Password: [hidden]')

        except Exception as e:
            raise CommandError(f'Failed to create user: {e}') 