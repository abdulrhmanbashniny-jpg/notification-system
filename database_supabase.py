import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection_string = os.environ.get('DATABASE_URL')
        if not self.connection_string:
            raise Exception("DATABASE_URL مفقود")
        
        if self.connection_string.startswith('postgres://'):
            self.connection_string = self.connection_string.replace('postgres://', 'postgresql://', 1)
        
        logger.info("✅ Database initialized")
    
    def get_connection(self):
        return psycopg2.connect(self.connection_string, connect_timeout=10)
    
    def execute_query(self, query, params=None, fetch=True):
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logger.error(f"Query error: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_user(self, user_id):
        query = "SELECT * FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def get_all_users(self):
        query = "SELECT * FROM users WHERE is_active = true ORDER BY full_name"
        return self.execute_query(query)
    
    def add_user(self, user_id, phone_number, full_name, role='user', department=None, email=None, telegram_username=None):
        query = """
            INSERT INTO users (user_id, phone_number, full_name, role, department, email, telegram_username)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET full_name = EXCLUDED.full_name, last_active = CURRENT_TIMESTAMP
        """
        try:
            self.execute_query(query, (user_id, phone_number, full_name, role, department, email, telegram_username), fetch=False)
            return True
        except:
            return False
    
    def get_transaction_types(self, level=None, parent_id=None):
        query = "SELECT * FROM transaction_types WHERE is_active = true"
        params = []
        if level:
            query += " AND level = %s"
            params.append(level)
        if parent_id is not None:
            query += " AND parent_id = %s"
            params.append(parent_id)
        query += " ORDER BY level, id"
        return self.execute_query(query, tuple(params) if params else None)
    
    def get_main_types(self):
        return self.get_transaction_types(level=1)
    
    def get_subtypes(self, parent_id):
        return self.get_transaction_types(parent_id=parent_id)
    
    def add_transaction(self, transaction_type_id, user_id, title, end_date, 
                       responsible_person_id=None, reminder_recipients=None, 
                       description=None, priority='normal', data=None, start_date=None):
        recipients = reminder_recipients or []
        data_json = json.dumps(data) if data else '{}'
        
        query = """
            INSERT INTO transactions (transaction_type_id, user_id, responsible_person_id,
                                    title, description, data, start_date, end_date,
                                    reminder_recipients, priority)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING transaction_id
        """
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, (transaction_type_id, user_id, responsible_person_id,
                                  title, description, data_json, start_date, end_date,
                                  recipients, priority))
            transaction_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"✅ Created transaction #{transaction_id}")
            return transaction_id
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to create transaction: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def get_active_transactions(self):
        query = """
            SELECT t.*, tt.name as type_name, tt.icon as type_icon,
                   u.full_name as user_name, r.full_name as responsible_person_name,
                   DATE(t.end_date) - CURRENT_DATE as days_left
            FROM transactions t
            JOIN transaction_types tt ON t.transaction_type_id = tt.id
            JOIN users u ON t.user_id = u.user_id
            LEFT JOIN users r ON t.responsible_person_id = r.user_id
            WHERE t.is_active = true
            ORDER BY t.end_date ASC
        """
        result = self.execute_query(query)
        for trans in result:
            if trans.get('data'):
                trans['data'] = dict(trans['data'])
            if trans.get('reminder_recipients'):
                trans['reminder_recipients'] = list(trans['reminder_recipients'])
        return result
    
    def get_transaction(self, transaction_id):
        query = """
            SELECT t.*, tt.name as type_name, tt.icon as type_icon,
                   u.full_name as user_name, r.full_name as responsible_person_name,
                   DATE(t.end_date) - CURRENT_DATE as days_left
            FROM transactions t
            JOIN transaction_types tt ON t.transaction_type_id = tt.id
            JOIN users u ON t.user_id = u.user_id
            LEFT JOIN users r ON t.responsible_person_id = r.user_id
            WHERE t.transaction_id = %s
        """
        result = self.execute_query(query, (transaction_id,))
        if result:
            trans = result[0]
            if trans.get('data'):
                trans['data'] = dict(trans['data'])
            if trans.get('reminder_recipients'):
                trans['reminder_recipients'] = list(trans['reminder_recipients'])
            return trans
        return None
    
    def get_transactions_by_role(self, user_id):
        query = """
            SELECT t.*, tt.name as type_name, tt.icon as type_icon,
                   u.full_name as user_name, DATE(t.end_date) - CURRENT_DATE as days_left
            FROM transactions t
            JOIN transaction_types tt ON t.transaction_type_id = tt.id
            JOIN users u ON t.user_id = u.user_id
            WHERE t.is_active = true AND (t.user_id = %s OR %s = ANY(t.reminder_recipients))
            ORDER BY t.end_date ASC
        """
        result = self.execute_query(query, (user_id, user_id))
        for trans in result:
            if trans.get('data'):
                trans['data'] = dict(trans['data'])
            if trans.get('reminder_recipients'):
                trans['reminder_recipients'] = list(trans['reminder_recipients'])
        return result
    
    def get_stats(self, user_id=None):
        query = """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE <= 3 THEN 1 END) as critical,
                   COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE BETWEEN 4 AND 7 THEN 1 END) as warning,
                   COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE BETWEEN 8 AND 30 THEN 1 END) as upcoming,
                   COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE > 30 THEN 1 END) as safe
            FROM transactions WHERE is_active = true
        """
        result = self.execute_query(query)[0]
        return dict(result)
    
    def get_pending_notifications(self):
        query = """
            SELECT n.*, t.title, t.end_date, t.priority,
                   tt.name as type_name, tt.icon as type_icon, u.full_name as user_name
            FROM notifications n
            JOIN transactions t ON n.transaction_id = t.transaction_id
            JOIN transaction_types tt ON t.transaction_type_id = tt.id
            JOIN users u ON t.user_id = u.user_id
            WHERE n.sent = false AND t.is_active = true
              AND DATE(t.end_date) - CURRENT_DATE = n.days_before
            ORDER BY t.priority DESC, t.end_date ASC
        """
        result = self.execute_query(query)
        for notif in result:
            if notif.get('recipients'):
                notif['recipients'] = list(notif['recipients'])
        return result
    
    def mark_notification_sent(self, notification_id):
        query = "UPDATE notifications SET sent = true, sent_at = CURRENT_TIMESTAMP WHERE notification_id = %s"
        try:
            self.execute_query(query, (notification_id,), fetch=False)
            return True
        except:
            return False
