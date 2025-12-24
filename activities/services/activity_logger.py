import json
import time
import traceback
from datetime import datetime
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from ..models import ActivityLog, ActionType


class ActivityLogger:
    """
    Service for logging activities with structured JSON data
    """

    @staticmethod
    def log_device_control(user, house, component, action_type, parameters, result, **kwargs):
        """
        Log device control activities
        """
        log_data = {
            'user': user,
            'house': house,
            'component': component,
            'action_type': action_type,
            'action_name': 'device_control',
            'action_parameters': {
                'component_id': str(component.id) if component else None,
                'component_name': component.name if component else None,
                'component_type': component.component_type.name if component else None,
                'action_type': action_type.name if action_type else None,
                'parameters': parameters,
                'device_state_before': kwargs.get('previous_state', {}),
                'source': kwargs.get('source', 'mobile_app'),
                'request_id': kwargs.get('request_id'),
                'session_id': kwargs.get('session_id'),
            },
            'action_result': {
                'success': result.get('success', True),
                'new_state': result.get('new_state', {}),
                'device_status': result.get('device_status', 'unknown'),
                'execution_time': result.get('execution_time'),
                'error_message': result.get('error_message'),
                'error_code': result.get('error_code'),
                'ack_received': result.get('ack_received', False),
                'ack_timestamp': result.get('ack_timestamp'),
                'microcontroller_id': result.get('microcontroller_id'),
            },
            'log_level': 'info' if result.get('success', True) else 'error',
            'source': kwargs.get('source', 'mobile_app'),
            'ip_address': kwargs.get('ip_address'),
            'user_agent': kwargs.get('user_agent', ''),
            'execution_time': kwargs.get('execution_time'),
        }

        return ActivityLogger._create_log(log_data)

    @staticmethod
    def log_user_authentication(user, house, action, result, **kwargs):
        """
        Log user authentication activities
        """
        log_data = {
            'user': user,
            'house': house,
            'action_name': f'user_{action}',
            'action_parameters': {
                'action': action,
                'email': kwargs.get('email'),
                'device_type': kwargs.get('device_type'),
                'app_version': kwargs.get('app_version'),
                'login_method': kwargs.get('login_method', 'email_password'),
                'remember_me': kwargs.get('remember_me', False),
                'two_factor_used': kwargs.get('two_factor_used', False),
            },
            'action_result': {
                'success': result.get('success', False),
                'user_id': str(user.id) if user else None,
                'session_token': result.get('session_token'),
                'expires_at': result.get('expires_at'),
                'error_message': result.get('error_message'),
                'error_code': result.get('error_code'),
                'failed_attempts': result.get('failed_attempts', 0),
            },
            'log_level': 'info' if result.get('success', False) else 'warning',
            'source': kwargs.get('source', 'mobile_app'),
            'ip_address': kwargs.get('ip_address'),
            'user_agent': kwargs.get('user_agent', ''),
        }

        return ActivityLogger._create_log(log_data)

    @staticmethod
    def log_house_management(user, house, action, parameters, result, **kwargs):
        """
        Log house management activities
        """
        log_data = {
            'user': user,
            'house': house,
            'action_name': f'house_{action}',
            'action_parameters': {
                'action': action,
                'house_id': str(house.id) if house else None,
                'house_name': house.name if house else None,
                'parameters': parameters,
                'affected_users': kwargs.get('affected_users', []),
                'permission_changes': kwargs.get('permission_changes', {}),
            },
            'action_result': {
                'success': result.get('success', True),
                'new_house_id': result.get('new_house_id'),
                'updated_fields': result.get('updated_fields', []),
                'affected_count': result.get('affected_count', 0),
                'error_message': result.get('error_message'),
            },
            'log_level': 'info' if result.get('success', True) else 'error',
            'source': kwargs.get('source', 'web_app'),
            'ip_address': kwargs.get('ip_address'),
            'user_agent': kwargs.get('user_agent', ''),
        }

        return ActivityLogger._create_log(log_data)

    @staticmethod
    def log_automation_trigger(house, component, automation_rule, trigger_data, result, **kwargs):
        """
        Log automation rule triggers
        """
        log_data = {
            'user': kwargs.get('user'),
            'house': house,
            'component': component,
            'action_name': 'automation_trigger',
            'action_parameters': {
                'automation_rule_id': str(automation_rule.id) if automation_rule else None,
                'rule_name': automation_rule.name if automation_rule else None,
                'trigger_type': trigger_data.get('trigger_type'),
                'trigger_conditions': trigger_data.get('conditions', {}),
                'trigger_value': trigger_data.get('trigger_value'),
                'scheduled_time': trigger_data.get('scheduled_time'),
            },
            'action_result': {
                'success': result.get('success', True),
                'actions_executed': result.get('actions_executed', []),
                'execution_order': result.get('execution_order'),
                'total_execution_time': result.get('total_execution_time'),
                'error_messages': result.get('error_messages', []),
            },
            'log_level': 'info' if result.get('success', True) else 'warning',
            'source': 'automation',
            'execution_time': result.get('total_execution_time'),
        }

        return ActivityLogger._create_log(log_data)

    @staticmethod
    def log_microcontroller_activity(microcontroller, action, data, result, **kwargs):
        """
        Log microcontroller activities
        """
        log_data = {
            'house': microcontroller.house,
            'action_name': f'microcontroller_{action}',
            'action_parameters': {
                'microcontroller_id': str(microcontroller.id),
                'microcontroller_name': microcontroller.name,
                'mac_address': microcontroller.mac_address,
                'firmware_version': microcontroller.firmware_version,
                'action': action,
                'data_received': data,
                'signal_strength': kwargs.get('signal_strength'),
                'battery_level': kwargs.get('battery_level'),
            },
            'action_result': {
                'success': result.get('success', True),
                'response_data': result.get('response_data', {}),
                'command_acknowledged': result.get('acknowledged', False),
                'execution_time': result.get('execution_time'),
                'hardware_errors': result.get('hardware_errors', []),
            },
            'log_level': 'info' if result.get('success', True) else 'error',
            'source': 'microcontroller',
            'ip_address': kwargs.get('ip_address'),
        }

        return ActivityLogger._create_log(log_data)

    @staticmethod
    def log_security_event(user, house, event_type, details, **kwargs):
        """
        Log security events
        """
        log_data = {
            'user': user,
            'house': house,
            'action_name': f'security_{event_type}',
            'action_parameters': {
                'event_type': event_type,
                'severity': kwargs.get('severity', 'medium'),
                'details': details,
                'suspicious_activity': kwargs.get('suspicious_activity', {}),
                'previous_attempts': kwargs.get('previous_attempts', 0),
                'blocked': kwargs.get('blocked', False),
            },
            'action_result': {
                'action_taken': kwargs.get('action_taken', 'logged'),
                'user_blocked': kwargs.get('user_blocked', False),
                'ip_blocked': kwargs.get('ip_blocked', False),
                'notification_sent': kwargs.get('notification_sent', False),
                'admin_notified': kwargs.get('admin_notified', False),
            },
            'log_level': 'security',
            'source': kwargs.get('source', 'system'),
            'ip_address': kwargs.get('ip_address'),
            'user_agent': kwargs.get('user_agent', ''),
            'request_path': kwargs.get('request_path', ''),
        }

        return ActivityLogger._create_log(log_data)

    @staticmethod
    def log_system_health(metric_name, value, threshold, status, **kwargs):
        """
        Log system health metrics
        """
        log_data = {
            'action_name': 'system_health_check',
            'action_parameters': {
                'metric_name': metric_name,
                'metric_value': value,
                'threshold': threshold,
                'check_timestamp': timezone.now().isoformat(),
                'component': kwargs.get('component'),
                'service': kwargs.get('service'),
            },
            'action_result': {
                'status': status,
                'is_healthy': status in ['healthy', 'warning'],
                'recommendation': kwargs.get('recommendation'),
                'recovery_action': kwargs.get('recovery_action'),
            },
            'log_level': 'warning' if status == 'warning' else 'error' if status == 'critical' else 'info',
            'source': 'system',
            'house': kwargs.get('house'),
        }

        return ActivityLogger._create_log(log_data)

    @staticmethod
    def _create_log(log_data):
        """
        Create the actual ActivityLog entry
        """
        try:
            # Handle action_type - it could be ActionType instance or string
            action_type_value = log_data.get('action_type')
            action_type_instance = None

            if action_type_value:
                if isinstance(action_type_value, ActionType):
                    # It's already an ActionType instance
                    action_type_instance = action_type_value
                elif hasattr(action_type_value, 'name'):
                    # It has a .name attribute (might be ActionType instance)
                    try:
                        action_type_instance = ActionType.objects.filter(name=action_type_value.name).first()
                    except:
                        # If that fails, try to find by string
                        try:
                            action_type_instance = ActionType.objects.filter(name=str(action_type_value)).first()
                        except:
                            pass
                else:
                    # It's a string or something else
                    try:
                        action_type_instance = ActionType.objects.filter(name=str(action_type_value)).first()
                    except:
                        pass

            # Create the log entry
            return ActivityLog.objects.create(
                user=log_data.get('user'),
                house=log_data.get('house'),
                component=log_data.get('component'),
                action_type=action_type_instance,  # Pass the instance or None
                action_name=log_data.get('action_name'),
                action_parameters=log_data.get('action_parameters', {}),
                action_result=log_data.get('action_result', {}),
                log_level=log_data.get('log_level', 'info'),
                source=log_data.get('source', 'api'),
                ip_address=log_data.get('ip_address'),
                user_agent=log_data.get('user_agent', ''),
                request_path=log_data.get('request_path', ''),
                execution_time=log_data.get('execution_time'),
                status_code=log_data.get('status_code'),
            )
        except Exception as e:
            # Fallback logging if primary logging fails
            print(f"Failed to create activity log: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            print(f"Log data that failed: {log_data}")
            return None