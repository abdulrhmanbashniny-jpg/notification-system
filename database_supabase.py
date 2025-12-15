import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.conn = None
    
    def connect(self):
        """إنشاء اتصال بقاعدة البيانات"""
        try:
            if not self.conn or self.conn.closed:
                self.conn = psycopg2.connect(self.connection_string)
            return self.conn
        except Exception as e:
            logger.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
            raise
    
    def check_connection(self):
        """التحقق من الاتصال بقاعدة البيانات"""
        try:
            conn = self.connect()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"فشل الاتصال بقاعدة البيانات: {e}")
            return False
    
    def execute_query(self, query, params=None, fetch=True):
        """تنفيذ استعلام SQL"""
        try:
            conn = self.connect()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    result = cur.fetchall()
                    return result
                else:
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"خطأ في تنفيذ الاستعلام: {e}")
            if self.conn:
                self.conn.rollback()
            return None if fetch else False
    
    # ==================== المستخدمون ====================
    
    def get_user(self, user_id):
        """جلب معلومات مستخدم"""
        query = "SELECT * FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def add_user(self, user_id, full_name, telegram_username=None, phone_number=None, 
                 email=None, role='user', department=None):
        """إضافة مستخدم جديد"""
        query = """
            INSERT INTO users (user_id, full_name, telegram_username, phone_number, 
                             email, role, department, is_active, created_at, last_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, true, NOW(), NOW())
            ON CONFLICT (user_id) DO UPDATE 
            SET last_active = NOW()
            RETURNING user_id
        """
        result = self.execute_query(
            query, 
            (user_id, full_name, telegram_username, phone_number, email, role, department),
            fetch=True
        )
        return result[0]['user_id'] if result else None
    
    def update_user_activity(self, user_id):
        """تحديث آخر نشاط للمستخدم"""
        query = "UPDATE users SET last_active = NOW() WHERE user_id = %s"
        return self.execute_query(query, (user_id,), fetch=False)
    
    # ==================== أنواع المعاملات ====================
    
    def get_transaction_types(self, level=None, parent_id=None):
        """جلب أنواع المعاملات"""
        if parent_id is not None:
            query = """
                SELECT * FROM transaction_types 
                WHERE parent_id = %s AND is_active = true
                ORDER BY name
            """
            params = (parent_id,)
        elif level is not None:
            query = """
                SELECT * FROM transaction_types 
                WHERE level = %s AND is_active = true
                ORDER BY name
            """
            params = (level,)
        else:
            query = """
                SELECT * FROM transaction_types 
                WHERE is_active = true
                ORDER BY level, name
            """
            params = None
        
        return self.execute_query(query, params) or []
    
    def get_transaction_type_name(self, type_id):
        """جلب اسم نوع المعاملة"""
        query = "SELECT name FROM transaction_types WHERE id = %s"
        result = self.execute_query(query, (type_id,))
        return result[0]['name'] if result else 'غير معروف'
    
    # ==================== المعاملات ====================
    
    def add_transaction(self, transaction_type_id, user_id, title, description='',
                       start_date=None, end_date=None, priority='normal', 
                       responsible_person_id=None, data=None):
        """إضافة معاملة جديدة"""
        if start_date is None:
            start_date = datetime.now().date()
        
        query = """
            INSERT INTO transactions (
                transaction_type_id, user_id, responsible_person_id, title, 
                description, data, start_date, end_date, priority, 
                status, is_active, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', true, NOW(), NOW())
            RETURNING transaction_id
        """
        
        result = self.execute_query(
            query,
            (transaction_type_id, user_id, responsible_person_id or user_id, 
             title, description, data, start_date, end_date, priority),
            fetch=True
        )
        
        if result:
            transaction_id = result[0]['transaction_id']
            # إنشاء التنبيهات التلقائية
            self.create_notifications_for_transaction(transaction_id, end_date, [user_id])
            return transaction_id
        return None
    
    def get_transaction(self, transaction_id):
        """جلب معلومات معاملة"""
        query = """
            SELECT t.*, tt.name as type_name, tt.icon,
                   u.full_name as user_name,
                   r.full_name as responsible_name
            FROM transactions t
            LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
            LEFT JOIN users u ON t.user_id = u.user_id
            LEFT JOIN users r ON t.responsible_person_id = r.user_id
            WHERE t.transaction_id = %s
        """
        result = self.execute_query(query, (transaction_id,))
        return result[0] if result else None
    
    def get_user_transactions(self, user_id, status=None, transaction_type_id=None, 
                             priority=None, limit=None):
        """جلب معاملات المستخدم"""
        query = """
            SELECT t.*, tt.name as type_name, tt.icon
            FROM transactions t
            LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
            WHERE t.user_id = %s AND t.is_active = true
        """
        params = [user_id]
        
        if status:
            query += " AND t.status = %s"
            params.append(status)
        
        if transaction_type_id:
            query += " AND t.transaction_type_id = %s"
            params.append(transaction_type_id)
        
        if priority:
            query += " AND t.priority = %s"
            params.append(priority)
        
        query += " ORDER BY t.end_date ASC, t.created_at DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query, tuple(params)) or []
    
    def get_recent_transactions(self, limit=10):
        """جلب أحدث المعاملات"""
        query = """
            SELECT t.*, tt.name as type_name, tt.icon, u.full_name as user_name
            FROM transactions t
            LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
            LEFT JOIN users u ON t.user_id = u.user_id
            WHERE t.is_active = true
            ORDER BY t.created_at DESC
            LIMIT %s
        """
        return self.execute_query(query, (limit,)) or []
    
    def update_transaction(self, transaction_id, updates):
        """تحديث معاملة"""
        # بناء جملة UPDATE ديناميكياً
        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        query = f"""
            UPDATE transactions 
            SET {set_clause}, updated_at = NOW()
            WHERE transaction_id = %s
        """
        params = list(updates.values()) + [transaction_id]
        return self.execute_query(query, tuple(params), fetch=False)
    
    def delete_transaction(self, transaction_id):
        """حذف معاملة (soft delete)"""
        query = """
            UPDATE transactions 
            SET is_active = false, updated_at = NOW()
            WHERE transaction_id = %s
        """
        return self.execute_query(query, (transaction_id,), fetch=False)
    
    def search_transactions(self, user_id, search_term):
        """البحث في المعاملات"""
        query = """
            SELECT t.*, tt.name as type_name, tt.icon
            FROM transactions t
            LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
            WHERE t.user_id = %s 
            AND t.is_active = true
            AND (t.title ILIKE %s OR t.description ILIKE %s)
            ORDER BY t.end_date ASC
        """
        search_pattern = f"%{search_term}%"
        return self.execute_query(query, (user_id, search_pattern, search_pattern)) or []
    
    def get_transactions_due_soon(self, user_id, days=7):
        """جلب المعاملات التي تنتهي قريباً"""
        query = """
            SELECT t.*, tt.name as type_name, tt.icon
            FROM transactions t
            LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
            WHERE t.user_id = %s 
            AND t.status = 'active'
            AND t.is_active = true
            AND t.end_date <= %s
            ORDER BY t.end_date ASC
        """
        due_date = datetime.now().date() + timedelta(days=days)
        return self.execute_query(query, (user_id, due_date)) or []
    
    # ==================== التنبيهات ====================
    
    def create_notifications_for_transaction(self, transaction_id, end_date, recipients):
        """إنشاء التنبيهات التلقائية لمعاملة"""
        days_before_list = [30, 15, 7, 3, 0]
        
        for days_before in days_before_list:
            notification_date = end_date - timedelta(days=days_before)
            
            # تخطي التنبيهات في الماضي
            if notification_date < datetime.now().date():
                continue
            
            query = """
                INSERT INTO notifications (
                    transaction_id, days_before, recipients, 
                    notification_type, message, sent, created_at
                )
                VALUES (%s, %s, %s, 'scheduled', %s, false, NOW())
            """
            
            # إنشاء رسالة التنبيه
            if days_before == 0:
                message = f"⏰ تنتهي المعاملة اليوم!"
            else:
                message = f"⚠️ تنبيه: المعاملة ستنتهي بعد {days_before} يوم"
            
            self.execute_query(
                query,
                (transaction_id, days_before, recipients, message),
                fetch=False
            )
    
    def get_pending_notifications(self):
        """جلب التنبيهات المعلقة (التي يجب إرسالها اليوم)"""
        query = """
            SELECT n.*, t.title, t.end_date, t.priority, tt.name as type_name
            FROM notifications n
            JOIN transactions t ON n.transaction_id = t.transaction_id
            JOIN transaction_types tt ON t.transaction_type_id = tt.id
            WHERE n.sent = false
            AND t.is_active = true
            AND t.status = 'active'
            AND (t.end_date - n.days_before) = CURRENT_DATE
            ORDER BY n.created_at ASC
        """
        results = self.execute_query(query) or []
        
        # تحديث رسالة التنبيه بالتفاصيل
        for notif in results:
            priority_emoji = {'normal': '🟢', 'high': '🟡', 'critical': '🔴'}
            days = notif['days_before']
            
            if days == 0:
                time_text = "**اليوم**"
            else:
                time_text = f"بعد **{days}** يوم"
            
            notif['message'] = f"""
🔔 **تنبيه معاملة**

📋 **{notif['title']}**
📂 النوع: {notif['type_name']}
{priority_emoji.get(notif['priority'], '')} الأولوية: {notif['priority']}

⏰ تنتهي {time_text}
📅 تاريخ الانتهاء: {notif['end_date']}

🆔 رقم المعاملة: #{notif['transaction_id']}
            """
        
        return results
    
    def mark_notification_sent(self, notification_id):
        """تحديث حالة التنبيه كمُرسَل"""
        query = """
            UPDATE notifications 
            SET sent = true, sent_at = NOW()
            WHERE notification_id = %s
        """
        return self.execute_query(query, (notification_id,), fetch=False)
    
    # ==================== الإحصائيات ====================
    
    def get_statistics(self):
        """جلب الإحصائيات العامة"""
        stats = {}
        
        # إجمالي المعاملات
        query = "SELECT COUNT(*) as count FROM transactions WHERE is_active = true"
        result = self.execute_query(query)
        stats['total_transactions'] = result[0]['count'] if result else 0
        
        # المعاملات النشطة
        query = "SELECT COUNT(*) as count FROM transactions WHERE status = 'active' AND is_active = true"
        result = self.execute_query(query)
        stats['active_transactions'] = result[0]['count'] if result else 0
        
        # عدد المستخدمين
        query = "SELECT COUNT(*) as count FROM users WHERE is_active = true"
        result = self.execute_query(query)
        stats['total_users'] = result[0]['count'] if result else 0
        
        # التنبيهات المعلقة
        query = "SELECT COUNT(*) as count FROM notifications WHERE sent = false"
        result = self.execute_query(query)
        stats['pending_notifications'] = result[0]['count'] if result else 0
        
        return stats
    
    def get_user_statistics(self, user_id):
        """جلب إحصائيات مستخدم محدد"""
        stats = {}
        
        # إجمالي المعاملات
        query = "SELECT COUNT(*) as count FROM transactions WHERE user_id = %s AND is_active = true"
        result = self.execute_query(query, (user_id,))
        stats['total_transactions'] = result[0]['count'] if result else 0
        
        # المعاملات حسب الحالة
        for status in ['active', 'completed', 'cancelled']:
            query = """
                SELECT COUNT(*) as count FROM transactions 
                WHERE user_id = %s AND status = %s AND is_active = true
            """
            result = self.execute_query(query, (user_id, status))
            stats[f'{status}_transactions'] = result[0]['count'] if result else 0
        
        # المعاملات حسب الأولوية
        for priority in ['normal', 'high', 'critical']:
            query = """
                SELECT COUNT(*) as count FROM transactions 
                WHERE user_id = %s AND priority = %s AND status = 'active' AND is_active = true
            """
            result = self.execute_query(query, (user_id, priority))
            key = 'normal_transactions' if priority == 'normal' else f'{priority}_priority_transactions'
            stats[key] = result[0]['count'] if result else 0
        
        # المعاملات التي تنتهي قريباً (7 أيام)
        query = """
            SELECT COUNT(*) as count FROM transactions 
            WHERE user_id = %s AND status = 'active' 
            AND is_active = true
            AND end_date <= %s
        """
        due_date = datetime.now().date() + timedelta(days=7)
        result = self.execute_query(query, (user_id, due_date))
        stats['due_soon'] = result[0]['count'] if result else 0
        
        # التنبيهات المعلقة
        query = """
            SELECT COUNT(*) as count FROM notifications n
            JOIN transactions t ON n.transaction_id = t.transaction_id
            WHERE t.user_id = %s AND n.sent = false
        """
        result = self.execute_query(query, (user_id,))
        stats['pending_notifications'] = result[0]['count'] if result else 0
        
        return stats
    
    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("تم إغلاق الاتصال بقاعدة البيانات")
