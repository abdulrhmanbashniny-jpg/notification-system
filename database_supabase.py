"""
🚀 Supabase Database Engine - محرك قاعدة البيانات الاحترافي
نظام شامل مع صلاحيات، audit logging، وأداء عالي
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """محرك قاعدة البيانات الاحترافي"""
    
    def __init__(self):
        self.connection_string = os.environ.get('DATABASE_URL')
        if not self.connection_string:
            raise Exception("❌ DATABASE_URL غير موجود في متغيرات البيئة!")
        
        # تصحيح رابط Supabase
        if self.connection_string.startswith('postgres://'):
            self.connection_string = self.connection_string.replace('postgres://', 'postgresql://', 1)
        
        logger.info("✅ تم تهيئة الاتصال بـ Supabase")
    
    def get_connection(self):
        """إنشاء اتصال آمن بقاعدة البيانات"""
        try:
            conn = psycopg2.connect(
                self.connection_string,
                connect_timeout=10,
                options='-c statement_timeout=30000'
            )
            return conn
        except Exception as e:
            logger.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        """تنفيذ استعلام مع معالجة الأخطاء"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute(query, params)
            
            if fetch:
                result = cursor.fetchall()
                return result
            else:
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ خطأ في الاستعلام: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    # ==================== أنواع المعاملات ====================
    
    def get_transaction_types(self, level: int = None, parent_id: int = None, 
                              include_inactive: bool = False) -> List[Dict]:
        """جلب أنواع المعاملات مع التفريعات"""
        query = """
            SELECT t1.*, 
                   t2.name as parent_name,
                   t2.icon as parent_icon,
                   (SELECT COUNT(*) FROM transactions WHERE transaction_type_id = t1.id AND is_active = true) as transactions_count
            FROM transaction_types t1
            LEFT JOIN transaction_types t2 ON t1.parent_id = t2.id
            WHERE 1=1
        """
        
        params = []
        
        if not include_inactive:
            query += " AND t1.is_active = true"
        
        if level:
            query += " AND t1.level = %s"
            params.append(level)
        
        if parent_id is not None:
            query += " AND t1.parent_id = %s"
            params.append(parent_id)
        
        query += " ORDER BY t1.level, t1.id"
        
        return self.execute_query(query, tuple(params))
    
    def get_main_types(self) -> List[Dict]:
        """جلب الأنواع الرئيسية فقط (Level 1)"""
        return self.get_transaction_types(level=1)
    
    def get_subtypes(self, parent_id: int) -> List[Dict]:
        """جلب التفريعات لنوع معين"""
        return self.get_transaction_types(parent_id=parent_id)
    
    def add_transaction_type(self, name: str, icon: str, parent_id: int = None, 
                            description: str = None) -> int:
        """إضافة نوع معاملة جديد"""
        level = 1 if not parent_id else 2
        
        query = """
            INSERT INTO transaction_types (name, icon, parent_id, level, description)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, (name, icon, parent_id, level, description))
            type_id = cursor.fetchone()[0]
            conn.commit()
            logger.info(f"✅ تم إضافة نوع جديد: {name} (ID: {type_id})")
            return type_id
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ فشل إضافة النوع: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    # ==================== المستخدمين والصلاحيات ====================
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """جلب معلومات مستخدم"""
        query = """
            SELECT u.*,
                   (SELECT COUNT(*) FROM transactions WHERE user_id = u.user_id AND is_active = true) as total_transactions,
                   (SELECT COUNT(*) FROM transactions WHERE user_id = u.user_id AND is_active = true AND DATE(end_date) - CURRENT_DATE <= 3) as critical_count
            FROM users u
            WHERE u.user_id = %s
        """
        
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def get_all_users(self, role: str = None, department: str = None, 
                     active_only: bool = True) -> List[Dict]:
        """جلب جميع المستخدمين مع فلترة"""
        query = "SELECT * FROM users WHERE 1=1"
        params = []
        
        if active_only:
            query += " AND is_active = true"
        
        if role:
            query += " AND role = %s"
            params.append(role)
        
        if department:
            query += " AND department = %s"
            params.append(department)
        
        query += " ORDER BY full_name"
        
        return self.execute_query(query, tuple(params))
    
    def get_managers(self) -> List[Dict]:
        """جلب المدراء والإداريين"""
        query = """
            SELECT * FROM users 
            WHERE (role = 'manager' OR role = 'admin') AND is_active = true
            ORDER BY role DESC, full_name
        """
        return self.execute_query(query)
    
    def add_user(self, user_id: int, phone_number: str, full_name: str,
                 role: str = 'user', department: str = None, email: str = None,
                 telegram_username: str = None) -> bool:
        """إضافة أو تحديث مستخدم"""
        query = """
            INSERT INTO users (user_id, phone_number, full_name, role, department, email, telegram_username)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                phone_number = EXCLUDED.phone_number,
                full_name = EXCLUDED.full_name,
                role = EXCLUDED.role,
                department = EXCLUDED.department,
                email = EXCLUDED.email,
                telegram_username = EXCLUDED.telegram_username,
                last_active = CURRENT_TIMESTAMP
        """
        
        try:
            self.execute_query(query, (user_id, phone_number, full_name, role, 
                                      department, email, telegram_username), fetch=False)
            logger.info(f"✅ تم حفظ المستخدم: {full_name}")
            return True
        except Exception as e:
            logger.error(f"❌ فشل حفظ المستخدم: {e}")
            return False
    
    # ==================== المعاملات ====================
    
    def add_transaction(self, transaction_type_id: int, user_id: int, title: str,
                       end_date: str, responsible_person_id: int = None,
                       reminder_recipients: List[int] = None, description: str = None,
                       data: dict = None, start_date: str = None, 
                       priority: str = 'normal') -> Optional[int]:
        """إضافة معاملة جديدة مع جميع التفاصيل"""
        
        # التحقق من الصلاحيات
        user = self.get_user(user_id)
        if not user or not user['is_active']:
            logger.error(f"❌ مستخدم غير مفعّل: {user_id}")
            return None
        
        # إعداد البيانات
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
            self._create_auto_notifications(transaction_id, end_date, recipients)
            
            logger.info(f"✅ تم إنشاء المعاملة #{transaction_id}: {title}")
            return transaction_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ فشل إنشاء المعاملة: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def _create_auto_notifications(self, transaction_id: int, end_date: str, recipients: List[int]):
        """إنشاء تنبيهات تلقائية"""
        if not recipients:
            return
        
        days_before_list = [30, 15, 7, 3, 0]
        
        query = """
            INSERT INTO notifications (transaction_id, days_before, recipients, notification_type)
            VALUES (%s, %s, %s, 'scheduled')
        """
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for days in days_before_list:
                cursor.execute(query, (transaction_id, days, recipients))
            conn.commit()
            logger.info(f"✅ تم إنشاء {len(days_before_list)} تنبيه للمعاملة #{transaction_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ فشل إنشاء التنبيهات: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def get_transactions_by_role(self, user_id: int, filters: dict = None) -> List[Dict]:
        """جلب المعاملات حسب صلاحية المستخدم"""
        user = self.get_user(user_id)
        if not user:
            return []
        
        base_query = """
            SELECT t.*,
                   tt.name as type_name,
                   tt.icon as type_icon,
                   tt.parent_id as type_parent_id,
                   pt.name as parent_type_name,
                   u.full_name as user_name,
                   u.department as user_department,
                   r.full_name as responsible_person_name,
                   DATE(t.end_date) - CURRENT_DATE as days_left
            FROM transactions t
            JOIN transaction_types tt ON t.transaction_type_id = tt.id
            LEFT JOIN transaction_types pt ON tt.parent_id = pt.id
            JOIN users u ON t.user_id = u.user_id
            LEFT JOIN users r ON t.responsible_person_id = r.user_id
            WHERE t.is_active = true
        """
        
        params = []
        
        # تطبيق الصلاحيات
        if user['role'] == 'admin':
            pass
        elif user['role'] == 'manager':
            base_query += """
                AND (
                    t.user_id = %s
                    OR t.responsible_person_id = %s
                    OR %s = ANY(t.reminder_recipients)
                    OR u.department = %s
                )
            """
            params.extend([user_id, user_id, user_id, user['department']])
        else:
            base_query += """
                AND (
                    t.user_id = %s
                    OR %s = ANY(t.reminder_recipients)
                )
            """
            params.extend([user_id, user_id])
        
        base_query += " ORDER BY t.end_date ASC, t.priority DESC"
        
        result = self.execute_query(base_query, tuple(params))
        
        # تحويل JSONB و arrays
        for trans in result:
            if trans.get('data'):
                trans['data'] = dict(trans['data'])
            if trans.get('reminder_recipients'):
                trans['reminder_recipients'] = list(trans['reminder_recipients'])
        
        return result
    
    def get_active_transactions(self) -> List[Dict]:
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
        
        for trans in result:
            if trans.get('data'):
                trans['data'] = dict(trans['data'])
            if trans.get('reminder_recipients'):
                trans['reminder_recipients'] = list(trans['reminder_recipients'])
        
        return result
    
    def get_transaction(self, transaction_id: int) -> Optional[Dict]:
        """جلب معاملة واحدة"""
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
    
    # ==================== التنبيهات ====================
    
    def get_pending_notifications(self) -> List[Dict]:
        """جلب التنبيهات المعلقة"""
        query = """
            SELECT n.*, t.title, t.end_date, t.priority,
                   tt.name as type_name, tt.icon as type_icon,
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
        
        for notif in result:
            if notif.get('recipients'):
                notif['recipients'] = list(notif['recipients'])
        
        return result
    
    def mark_notification_sent(self, notification_id: int) -> bool:
        """تعليم تنبيه كمُرسل"""
        query = "UPDATE notifications SET sent = true, sent_at = CURRENT_TIMESTAMP WHERE notification_id = %s"
        try:
            rows = self.execute_query(query, (notification_id,), fetch=False)
            return rows > 0
        except:
            return False
    
    def send_immediate_notification(self, transaction_id: int, recipients: List[int],
                                   message: str, sent_by: int) -> Optional[int]:
        """إرسال تنبيه فوري"""
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
            logger.info(f"✅ تم إرسال تنبيه فوري للمعاملة #{transaction_id}")
            return notification_id
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ فشل إرسال التنبيه الفوري: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    # ==================== الإحصائيات ====================
    
    def get_stats(self, user_id: int = None) -> Dict:
        """جلب إحصائيات شاملة"""
        
        base_filters = "WHERE is_active = true"
        params = []
        
        if user_id:
            user = self.get_user(user_id)
            if user and user['role'] != 'admin':
                if user['role'] == 'manager':
                    base_filters += " AND (user_id = %s OR %s = ANY(reminder_recipients))"
                    params = [user_id, user_id]
                else:
                    base_filters += " AND (user_id = %s OR %s = ANY(reminder_recipients))"
                    params = [user_id, user_id]
        
        # إجمالي المعاملات
        query = f"SELECT COUNT(*) as total FROM transactions {base_filters}"
        total = self.execute_query(query, tuple(params))[0]['total']
        
        # حسب الأولوية
        query = f"""
            SELECT 
                COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE <= 3 THEN 1 END) as critical,
                COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE BETWEEN 4 AND 7 THEN 1 END) as warning,
                COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE BETWEEN 8 AND 30 THEN 1 END) as upcoming,
                COUNT(CASE WHEN DATE(end_date) - CURRENT_DATE > 30 THEN 1 END) as safe
            FROM transactions {base_filters}
        """
        priority_stats = self.execute_query(query, tuple(params))[0]
        
        return {
            'total': total,
            'critical': priority_stats['critical'],
            'warning': priority_stats['warning'],
            'upcoming': priority_stats['upcoming'],
            'safe': priority_stats['safe']
        }
    
    # ==================== Audit Log ====================
    
    def _log_audit(self, table_name: str, action: str, record_id: int, 
                   user_id: int, changes: dict):
        """تسجيل في audit log"""
        query = """
            INSERT INTO audit_log (table_name, action, record_id, user_id, new_values)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        try:
            self.execute_query(query, (
                table_name, action, record_id, user_id, json.dumps(changes)
            ), fetch=False)
        except Exception as e:
            logger.error(f"❌ فشل تسجيل audit log: {e}")
