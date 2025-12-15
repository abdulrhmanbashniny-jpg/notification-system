"""
🚀 Supabase Database Engine - محرك قاعدة البيانات
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """محرك قاعدة البيانات الاحترافي"""
    
    def __init__(self):
        self.connection_string = os.environ.get('DATABASE_URL')
        if not self.connection_string:
            raise Exception("DATABASE_URL مفقود")
        
        if self.connection_string.startswith('postgres://'):
            self.connection_string = self.connection_string.replace('postgres://', 'postgresql://', 1)
        
        logger.info("✅ Database initialized")
    
    def get_connection(self):
        """إنشاء اتصال بقاعدة البيانات"""
        return psycopg2.connect(self.connection_string, connect_timeout=10)
    
    def execute_query(self, query, params=None, fetch=True):
        """تنفيذ استعلام"""
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
    
    # ==================== المستخدمين ====================
    
    def get_user(self, user_id):
        """جلب معلومات مستخدم"""
        query = """
            SELECT u.*,
                   (SELECT COUNT(*) FROM transactions 
                    WHERE user_id = u.user_id AND is_active = true) as total_transactions,
                   (SELECT COUNT(*) FROM transactions 
                    WHERE user_id = u.user_id AND is_active = true 
                    AND DATE(end_date) - CURRENT_DATE <= 3) as critical_count
            FROM users u
            WHERE u.user_id = %s
        """
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def get_all_users(self, active_only=True):
        """جلب جميع المستخدمين"""
        query = "SELECT * FROM users WHERE 1=1"
        if active_only:
            query += " AND is_active = true"
        query += " ORDER BY full_name"
        return self.execute_query(query)
    
    def add_user(self, user_id, phone_number, full_name, role='user', 
                 department=None, email=None, telegram_username=None):
        """إضافة أو تحديث مستخدم"""
        query = """
            INSERT INTO users (user_id, phone_number, full_name, role, department, email, telegram_username)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                full_name = EXCLUDED.full_name,
                telegram_username = EXCLUDED.telegram_username,
                last_active = CURRENT_TIMESTAMP
        """
        try:
            self.execute_query(query, (user_id, phone_number, full_name, role, 
                                      department, email, telegram_username), fetch=False)
            logger.info(f"✅ User saved: {full_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save user: {e}")
            return False
    
    # ==================== أنواع المعاملات ====================
    
    def get_transaction_types(self, level=None, parent_id=None):
        """جلب أنواع المعاملات"""
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
        """جلب الأنواع الرئيسية (Level 1)"""
        return self.get_transaction_types(level=1)
    
    def get_subtypes(self, parent_id):
        """جلب التفريعات لنوع معين"""
        return self.get_transaction_types(parent_id=parent_id)
    
    # ==================== المعاملات ====================
    
    def add_transaction(self, transaction_type_id, user_id, title, end_date, 
                       responsible_person_id=None, reminder_recipients=None, 
                       description=None, priority='normal', data=None, start_date=None):
        """إضافة معاملة جديدة مع إنشاء تنبيهات تلقائية"""
        
        recipients = reminder_recipients or []
        data_json = json.dumps(data) if data else '{}'
        
        query = """
            INSERT INTO transactions (
                transaction_type_id, user_id, responsible_person_id,
                title, description, data, start_date, end_date,
                reminder_recipients, priority
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING transaction_id
        """
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, (
                transaction_type_id, user_id, responsible_person_id,
                title, description, data_json, start_date, end_date,
                recipients, priority
            ))
            
            transaction_id = cursor.fetchone()[0]
            conn.commit()
            
            # إنشاء تنبيهات تلقائياً
            if recipients:
                self._create_auto_notifications(conn, transaction_id, recipients)
            
            logger.info(f"✅ Created transaction #{transaction_id}: {title}")
            return transaction_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to create transaction: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def _create_auto_notifications(self, conn, transaction_id, recipients):
        """إنشاء تنبيهات تلقائية (30، 15، 7، 3، 0 يوم)"""
        
        days_before_list = [30, 15, 7, 3, 0]
        
        query = """
            INSERT INTO notifications (transaction_id, days_before, recipients, notification_type)
            VALUES (%s, %s, %s, 'scheduled')
        """
        
        cursor = conn.cursor()
        try:
            for days in days_before_list:
                cursor.execute(query, (transaction_id, days, recipients))
            conn.commit()
            logger.info(f"✅ Created {len(days_before_list)} notifications for transaction #{transaction_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to create auto notifications: {e}")
        finally:
            cursor.close()
    
    def get_active_transactions(self):
        """جلب جميع المعاملات النشطة"""
        query = """
            SELECT t.*,
                   tt.name as type_name,
                   tt.icon as type_icon,
                   u.full_name as user_name,
                   r.full_name as responsible_person_name,
                   DATE(t.end_date) - CURRENT_DATE as days_left
            FROM transactions t
            JOIN transaction_types tt ON t.transaction_type_id = tt.id
            JOIN users u ON t.user_id = u.user_id
            LEFT JOIN users r ON t.responsible_person_id = r.user_id
            WHERE t.is_active = true
            ORDER BY t.end_date ASC
        """
        
        result = self.execute_query(query)
        
        # تحويل JSONB و arrays
        for trans in result:
            if trans.get('data'):
                trans['data'] = dict(trans['data'])
            if trans.get('reminder_recipients'):
                trans['reminder_recipients'] = list(trans['reminder_recipients'])
        
        return result
    
    def get_transaction(self, transaction_id):
        """جلب معاملة واحدة بالتفصيل"""
        query = """
            SELECT t.*,
                   tt.name as type_name,
                   tt.icon as type_icon,
                   u.full_name as user_name,
                   r.full_name as responsible_person_name,
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
        """جلب معاملات حسب صلاحية المستخدم"""
        query = """
            SELECT t.*,
                   tt.name as type_name,
                   tt.icon as type_icon,
                   u.full_name as user_name,
                   DATE(t.end_date) - CURRENT_DATE as days_left
            FROM transactions t
            JOIN transaction_types tt ON t.transaction_type_id = tt.id
            JOIN users u ON t.user_id = u.user_id
            WHERE t.is_active = true 
              AND (t.user_id = %s OR %s = ANY(t.reminder_recipients))
            ORDER BY t.end_date ASC
        """
        
        result = self.execute_query(query, (user_id, user_id))
        
        for trans in result:
            if trans.get('data'):
                trans['data'] = dict(trans['data'])
            if trans.get('reminder_recipients'):
                trans['reminder_recipients'] = list(trans['reminder_recipients'])
        
        return result
    
    def update_transaction(self, transaction_id, **kwargs):
        """تحديث معاملة"""
        allowed_fields = ['title', 'description', 'end_date', 'responsible_person_id', 
                         'reminder_recipients', 'priority', 'status']
        
        updates = []
        values = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = %s")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(transaction_id)
        query = f"UPDATE transactions SET {', '.join(updates)} WHERE transaction_id = %s"
        
        try:
            self.execute_query(query, tuple(values), fetch=False)
            logger.info(f"✅ Updated transaction #{transaction_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update transaction: {e}")
            return False
    
    def delete_transaction(self, transaction_id):
        """حذف معاملة (soft delete)"""
        query = "UPDATE transactions SET is_active = false WHERE transaction_id = %s"
        try:
            self.execute_query(query, (transaction_id,), fetch=False)
            logger.info(f"✅ Deleted transaction #{transaction_id}")
            return True
        except:
            return False
    
    # ==================== الإحصائيات ====================
    
    def get_stats(self, user_id=None):
        """جلب إحصائيات شاملة"""
        
        # إذا كان هناك user_id محدد، فقط معاملاته
        base_filters = "WHERE is_active = true"
        params = []
        
        if user_id:
            base_filters += " AND (user_id = %s OR %s = ANY(reminder_recipients))"
            params = [user_id, user_id]
        
        query = f"""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE <= 3 THEN 1 END) as critical,
                COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE BETWEEN 4 AND 7 THEN 1 END) as warning,
                COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE BETWEEN 8 AND 30 THEN 1 END) as upcoming,
                COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE > 30 THEN 1 END) as safe
            FROM transactions {base_filters}
        """
        
        result = self.execute_query(query, tuple(params) if params else None)[0]
        return dict(result)
    
    # ==================== التنبيهات ====================
    
    def get_pending_notifications(self):
        """جلب التنبيهات المعلقة التي يجب إرسالها"""
        query = """
            SELECT n.*,
                   t.title,
                   t.end_date,
                   t.priority,
                   tt.name as type_name,
                   tt.icon as type_icon,
                   u.full_name as user_name
            FROM notifications n
            JOIN transactions t ON n.transaction_id = t.transaction_id
            JOIN transaction_types tt ON t.transaction_type_id = tt.id
            JOIN users u ON t.user_id = u.user_id
            WHERE n.sent = false
              AND t.is_active = true
              AND t.status = 'active'
              AND DATE(t.end_date) - CURRENT_DATE = n.days_before
            ORDER BY t.priority DESC, t.end_date ASC
        """
        
        result = self.execute_query(query)
        
        # تحويل arrays
        for notif in result:
            if notif.get('recipients'):
                notif['recipients'] = list(notif['recipients'])
        
        return result
    
    def mark_notification_sent(self, notification_id):
        """تعليم تنبيه كمُرسل"""
        query = """
            UPDATE notifications 
            SET sent = true, sent_at = CURRENT_TIMESTAMP 
            WHERE notification_id = %s
        """
        try:
            self.execute_query(query, (notification_id,), fetch=False)
            logger.info(f"✅ Notification #{notification_id} marked as sent")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to mark notification: {e}")
            return False
    
    def send_immediate_notification(self, transaction_id, recipients, message, sent_by):
        """إرسال تنبيه فوري خارج الجدولة"""
        query = """
            INSERT INTO notifications (
                transaction_id, days_before, recipients, message,
                notification_type, sent, sent_at
            )
            VALUES (%s, -1, %s, %s, 'immediate', true, CURRENT_TIMESTAMP)
            RETURNING notification_id
        """
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, (transaction_id, recipients, message))
            notification_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"✅ Immediate notification #{notification_id} sent")
            return notification_id
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to send immediate notification: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    # ==================== البحث والفلترة ====================
    
    def search_transactions(self, search_term=None, transaction_type_id=None, 
                          priority=None, user_id=None, status='active'):
        """البحث عن معاملات بفلترة متقدمة"""
        query = """
            SELECT t.*,
                   tt.name as type_name,
                   tt.icon as type_icon,
                   u.full_name as user_name,
                   DATE(t.end_date) - CURRENT_DATE as days_left
            FROM transactions t
            JOIN transaction_types tt ON t.transaction_type_id = tt.id
            JOIN users u ON t.user_id = u.user_id
            WHERE t.is_active = true AND t.status = %s
        """
        
        params = [status]
        
        if search_term:
            query += " AND (t.title ILIKE %s OR t.description ILIKE %s)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
        
        if transaction_type_id:
            query += " AND t.transaction_type_id = %s"
            params.append(transaction_type_id)
        
        if priority:
            query += " AND t.priority = %s"
            params.append(priority)
        
        if user_id:
            query += " AND (t.user_id = %s OR %s = ANY(t.reminder_recipients))"
            params.extend([user_id, user_id])
        
        query += " ORDER BY t.end_date ASC"
        
        result = self.execute_query(query, tuple(params))
        
        for trans in result:
            if trans.get('data'):
                trans['data'] = dict(trans['data'])
            if trans.get('reminder_recipients'):
                trans['reminder_recipients'] = list(trans['reminder_recipients'])
        
        return result
