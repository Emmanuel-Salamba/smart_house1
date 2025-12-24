"""
Django management command to generate sample activity logs for testing
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from activities.services.activity_logger import ActivityLogger
from users.models import User
from houses.models import House
from devices.models import Component
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Generate sample activity logs for testing and demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of sample logs to generate (default: 20)'
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete existing activity logs before generating new ones'
        )

    def handle(self, *args, **options):
        count = options['count']

        # Delete existing logs if requested
        if options['delete']:
            from activities.models import ActivityLog
            deleted_count, _ = ActivityLog.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing activity logs'))

        # Get available users, houses, and components
        users = list(User.objects.all())
        houses = list(House.objects.all())

        if not users:
            self.stdout.write(self.style.ERROR('❌ No users found. Please create users first.'))
            return

        if not houses:
            self.stdout.write(self.style.ERROR('❌ No houses found. Please create houses first.'))
            return

        # Get components for each house
        house_components = {}
        for house in houses:
            components = list(Component.objects.filter(house=house))
            if components:
                house_components[house.id] = components

        self.stdout.write(f'📊 Generating {count} sample activity logs...')
        self.stdout.write(f'👥 Using {len(users)} users')
        self.stdout.write(f'🏠 Using {len(houses)} houses')

        generated_count = 0

        for i in range(count):
            try:
                # Randomly select user and house
                user = random.choice(users)
                house = random.choice(houses)

                # Randomly choose log type with probabilities
                log_type = random.choices(
                    ['device', 'login', 'security', 'house', 'automation'],
                    weights=[40, 30, 15, 10, 5],  # Device logs most common
                    k=1
                )[0]

                # Generate different types of logs
                if log_type == 'device' and house.id in house_components and house_components[house.id]:
                    # Device control log
                    component = random.choice(house_components[house.id])

                    # Random device action
                    actions = ['turn_on', 'turn_off', 'dim', 'set_temperature', 'change_color']
                    action = random.choice(actions)

                    # Random parameters based on action
                    if action == 'dim':
                        parameters = {'brightness': random.randint(10, 100)}
                    elif action == 'set_temperature':
                        parameters = {'temperature': random.randint(16, 30)}
                    elif action == 'change_color':
                        colors = ['white', 'warm', 'cool', 'red', 'blue', 'green']
                        parameters = {'color': random.choice(colors)}
                    else:
                        parameters = {}

                    # Random result (mostly successful)
                    success = random.random() > 0.1  # 90% success rate

                    if success:
                        result = {
                            'success': True,
                            'new_state': {'power': 'on' if action == 'turn_on' else 'off'},
                            'device_status': random.choice(['online', 'online', 'online', 'slow']),
                            'ack_received': True,
                            'ack_timestamp': timezone.now().isoformat(),
                            'execution_time': random.uniform(0.1, 2.0)
                        }
                        log_level = 'info'
                    else:
                        result = {
                            'success': False,
                            'error_message': random.choice([
                                'Device not responding',
                                'Connection timeout',
                                'Invalid command',
                                'Device offline'
                            ]),
                            'device_status': 'offline',
                            'ack_received': False
                        }
                        log_level = 'error'

                    ActivityLogger.log_device_control(
                        user=user,
                        house=house,
                        component=component,
                        action_type=None,
                        parameters=parameters,
                        result=result,
                        source=random.choice(['mobile_app', 'web_app', 'api']),
                        ip_address=f'192.168.1.{random.randint(1, 254)}',
                        user_agent=random.choice([
                            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
                            'Mozilla/5.0 (Android 11; Mobile)',
                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                            'SmartHomeApp/2.1.0'
                        ]),
                        log_level=log_level,
                        execution_time=result.get('execution_time')
                    )
                    generated_count += 1

                elif log_type == 'login':
                    # User authentication log
                    if random.random() > 0.2:  # 80% successful logins
                        result = {
                            'success': True,
                            'session_token': 'sample_jwt_token',
                            'expires_at': (timezone.now() + timedelta(hours=1)).isoformat()
                        }
                        action = 'login'
                        log_level = 'info'
                    else:
                        result = {
                            'success': False,
                            'error_message': 'Invalid credentials',
                            'failed_attempts': random.randint(1, 5)
                        }
                        action = 'login_failed'
                        log_level = 'warning'

                    ActivityLogger.log_user_authentication(
                        user=user if action == 'login' else None,
                        house=house if action == 'login' else None,
                        action=action,
                        result=result,
                        email=user.email,
                        source=random.choice(['mobile_app', 'web_app']),
                        ip_address=f'10.0.2.{random.randint(1, 254)}',
                        user_agent=random.choice([
                            'SmartHomeMobile/1.5.2',
                            'Mozilla/5.0 (Android; Mobile)'
                        ]),
                        log_level=log_level
                    )
                    generated_count += 1

                elif log_type == 'security':
                    # Security event log
                    event_types = ['failed_login', 'access_denied', 'unusual_activity', 'device_tamper']
                    event_type = random.choice(event_types)

                    severity_weights = {
                        'failed_login': ['low', 'medium', 'high'],
                        'access_denied': ['medium', 'high'],
                        'unusual_activity': ['medium', 'high', 'critical'],
                        'device_tamper': ['high', 'critical']
                    }

                    severity = random.choice(severity_weights[event_type])

                    details_map = {
                        'failed_login': f'{random.randint(3, 10)} failed attempts from IP 192.168.1.{random.randint(100, 200)}',
                        'access_denied': f'Unauthorized access attempt to admin panel',
                        'unusual_activity': f'Rapid device switching detected ({random.randint(10, 50)} changes in 5 minutes)',
                        'device_tamper': f'Physical tampering detected on device {random.choice(["Front Door", "Living Room Camera", "Garage Sensor"])}'
                    }

                    ActivityLogger.log_security_event(
                        user=user if random.random() > 0.5 else None,
                        house=house,
                        event_type=event_type,
                        details=details_map[event_type],
                        severity=severity,
                        source='system',
                        ip_address=f'203.0.113.{random.randint(1, 254)}',
                        action_taken=random.choice(['logged', 'ip_blocked', 'user_notified', 'admin_alerted']),
                        user_blocked=random.random() > 0.7
                    )
                    generated_count += 1

                elif log_type == 'house':
                    # House management log
                    actions = ['created', 'updated', 'user_added', 'user_removed']
                    action = random.choice(actions)

                    parameters = {
                        'house_name': house.name,
                        'changes': random.choice(['name updated', 'location changed', 'permissions updated'])
                    }

                    result = {
                        'success': True,
                        'affected_count': random.randint(1, 5)
                    }

                    ActivityLogger.log_house_management(
                        user=user,
                        house=house,
                        action=action,
                        parameters=parameters,
                        result=result,
                        source='web_app',
                        ip_address=f'172.16.1.{random.randint(1, 254)}'
                    )
                    generated_count += 1

                elif log_type == 'automation':
                    # Automation trigger log (no user needed)
                    if house.id in house_components and house_components[house.id]:
                        component = random.choice(house_components[house.id])

                        trigger_types = ['schedule', 'device_state', 'sensor_value', 'time_of_day']
                        trigger_type = random.choice(trigger_types)

                        trigger_data = {
                            'trigger_type': trigger_type,
                            'conditions': {'threshold': random.randint(20, 30)},
                            'scheduled_time': timezone.now().isoformat()
                        }

                        result = {
                            'success': random.random() > 0.1,  # 90% success
                            'actions_executed': [f'turn_{"on" if random.random() > 0.5 else "off"}'],
                            'total_execution_time': random.uniform(0.5, 3.0)
                        }

                        ActivityLogger.log_automation_trigger(
                            house=house,
                            component=component,
                            automation_rule=None,  # We don't have actual rules in sample
                            trigger_data=trigger_data,
                            result=result,
                            user=user if random.random() > 0.5 else None,
                            source='automation'
                        )
                        generated_count += 1

                # Show progress every 10 logs
                if (i + 1) % 10 == 0:
                    self.stdout.write(f'   Generated {i + 1}/{count} logs...')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error generating log {i}: {str(e)}'))
                continue

        # Final summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Sample Activity Logs Generated Successfully!'))
        self.stdout.write(self.style.SUCCESS(f'   Total logs created: {generated_count}'))
        self.stdout.write('')
        self.stdout.write('📊 Log Type Distribution:')
        self.stdout.write(f'   • Device Control: {count * 0.4:.0f} logs')
        self.stdout.write(f'   • User Authentication: {count * 0.3:.0f} logs')
        self.stdout.write(f'   • Security Events: {count * 0.15:.0f} logs')
        self.stdout.write(f'   • House Management: {count * 0.1:.0f} logs')
        self.stdout.write(f'   • Automation Triggers: {count * 0.05:.0f} logs')
        self.stdout.write('')
        self.stdout.write('🔍 View logs in Django Admin:')
        self.stdout.write('   http://localhost:8000/admin/activities/activitylog/')
        self.stdout.write('')
        self.stdout.write('🎯 Tips:')
        self.stdout.write('   • Run with --count=50 for more logs')
        self.stdout.write('   • Run with --delete to clear old logs first')
        self.stdout.write('   • Logs include realistic IPs, user agents, and error scenarios')