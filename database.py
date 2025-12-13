import sqlite3
import os
from datetime import datetime, timedelta
import json

class Database:
    def __init__(self, db_path='data/notifications.db'):
        self.db_path = db_path
        self._ensure_directory()
        self._create_tables()
    
    def _ensure_directory(self):
        """إنشاء مجلد data إذا لم يكن موجوداً"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _get_connection(self):
        """إنشاء اتصال بقاعدة البيانات"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                phone_number TEXT UNIQUE,
                full_name TEXT,
                is_admin INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول أنواع المعاملات (قابل للتوسع)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_types (
                type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT UNIQUE NOT NULL,
                fields_config TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول المعاملات الرئيسي
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_id INTEGER,
                created_by INTEGER,
                title TEXT NOT NULL,
                data TEXT,
                end_date TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (type_id) REFERENCES transaction_types(type_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        ''')
        
        # جدول التنبيهات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                days_before INTEGER,
                is_enabled INTEGER DEFAULT 1,
                last_sent TEXT,
                FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
            )
        ''')
        
        # جدول المستلمين للتنبيهات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_recipients (
                recipient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id INTEGER,
                user_id INTEGER,
                FOREIGN KEY (notification_id) REFERENCES notifications(notification_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # جدول الجلسات القضائية (علاقة واحد لكثير)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS court_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                session_date TEXT,
                session_link TEXT,
                session_notes TEXT,
                is_completed INTEGER DEFAULT 0,
                FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
            )
        ''')
        
        # جدول تواريخ السيارة (تأمين، استمارة، ترخيص)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicle_dates (
                vehicle_date_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                date_type TEXT,
                expiry_date TEXT,
                FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
            )
        ''')
        
        # جدول الأرشيف
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS archived_transactions (
                archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                archived_at TEXT DEFAULT CURRENT_TIMESTAMP,
                archived_by INTEGER,
                final_notes TEXT,
                FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
                FOREIGN KEY (archived_by) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # إدراج أنواع المعاملات الافتراضية
        self._insert_default_transaction_types()
    
    def _insert_default_transaction_types(self):
        """إدراج أنواع المعاملات الافتراضية"""
        default_types = [
            {
                'type_name': 'عقد_عمل',
                'fields': ['اسم_الموظف', 'رقم_العقد', 'تاريخ_البداية', 'تاريخ_الانتهاء', 'الراتب', 'المسمى_الوظيفي', 'ملاحظات']
            },
            {
                'type_name': 'إجازة_موظف',
                'fields': ['اسم_الموظف', 'الوظيفة', 'الموظف_البديل', 'تاريخ_البداية', 'تاريخ_النهاية']
            },
            {
                'type_name': 'استمارة_سيارة',
                'fields': ['رقم_اللوحة', 'الرقم_التسلسلي']
            },
            {
                'type_name': 'ترخيص',
                'fields': ['نوع_الترخيص', 'تاريخ_البداية', 'تاريخ_الانتهاء', 'المنصة']
            },
            {
                'type_name': 'جلسة_قضائية',
                'fields': ['رقم_القضية', 'بيان_القضية', 'رابط_الجلسة']
            },
            {
                'type_name': 'أخرى',
                'fields': ['العنوان', 'الوصف', 'تاريخ_الانتهاء']
            }
        ]
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for trans_type in default_types:
            cursor.execute('''
                INSERT OR IGNORE INTO transaction_types (type_name, fields_config)
                VALUES (?, ?)
            ''', (trans_type['type_name'], json.dumps(trans_type['fields'])))
        
        conn.commit()
        conn.close()
    
    # وظائف المستخدمين
    def add_user(self, user_id, phone_number, full_name, is_admin=0):
        """إضافة مستخدم جديد"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (user_id, phone_number, full_name, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (user_id, phone_number, full_name, is_admin))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_user(self, user_id):
        """الحصول على معلومات مستخدم"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    def is_admin(self, user_id):
        """التحقق من صلاحيات المسؤول"""
        user = self.get_user(user_id)
        return user and user['is_admin'] == 1
    
    def get_all_users(self):
        """الحصول على جميع المستخدمين"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_active = 1')
        users = cursor.fetchall()
        conn.close()
        return [dict(user) for user in users]
    
    # وظائف المعاملات
    def add_transaction(self, type_id, created_by, title, data, end_date=None):
        """إضافة معاملة جديدة"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (type_id, created_by, title, data, end_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (type_id, created_by, title, json.dumps(data), end_date))
        transaction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return transaction_id
    
    def get_transaction(self, transaction_id):
        """الحصول على معاملة محددة"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.*, tt.type_name, u.full_name as creator_name
            FROM transactions t
            JOIN transaction_types tt ON t.type_id = tt.type_id
            JOIN users u ON t.created_by = u.user_id
            WHERE t.transaction_id = ?
        ''', (transaction_id,))
        transaction = cursor.fetchone()
        conn.close()
        if transaction:
            trans_dict = dict(transaction)
            trans_dict['data'] = json.loads(trans_dict['data']) if trans_dict['data'] else {}
            return trans_dict
        return None
    
    def get_active_transactions(self, user_id=None, type_id=None):
        """الحصول على المعاملات النشطة"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT t.*, tt.type_name, u.full_name as creator_name
            FROM transactions t
            JOIN transaction_types tt ON t.type_id = tt.type_id
            JOIN users u ON t.created_by = u.user_id
            WHERE t.status = 'active'
        '''
        params = []
        
        if user_id:
            query += ' AND t.created_by = ?'
            params.append(user_id)
        
        if type_id:
            query += ' AND t.type_id = ?'
            params.append(type_id)
        
        query += ' ORDER BY t.end_date ASC'
        
        cursor.execute(query, params)
        transactions = cursor.fetchall()
        conn.close()
        
        result = []
        for trans in transactions:
            trans_dict = dict(trans)
            trans_dict['data'] = json.loads(trans_dict['data']) if trans_dict['data'] else {}
            result.append(trans_dict)
        return result
    
    def update_transaction(self, transaction_id, data=None, end_date=None):
        """تحديث معاملة"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if data:
            cursor.execute('''
                UPDATE transactions
                SET data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE transaction_id = ?
            ''', (json.dumps(data), transaction_id))
        
        if end_date:
            cursor.execute('''
                UPDATE transactions
                SET end_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE transaction_id = ?
            ''', (end_date, transaction_id))
        
        conn.commit()
        conn.close()
    
    def archive_transaction(self, transaction_id, archived_by, final_notes=''):
        """أرشفة معاملة"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE transactions
            SET status = 'archived'
            WHERE transaction_id = ?
        ''', (transaction_id,))
        
        cursor.execute('''
            INSERT INTO archived_transactions (transaction_id, archived_by, final_notes)
            VALUES (?, ?, ?)
        ''', (transaction_id, archived_by, final_notes))
        
        conn.commit()
        conn.close()
    
    def delete_transaction(self, transaction_id):
        """حذف معاملة"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM transactions WHERE transaction_id = ?', (transaction_id,))
        conn.commit()
        conn.close()
    
    # وظائف التنبيهات
    def add_notification(self, transaction_id, days_before, recipient_ids):
        """إضافة تنبيه مع المستلمين"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (transaction_id, days_before)
            VALUES (?, ?)
        ''', (transaction_id, days_before))
        
        notification_id = cursor.lastrowid
        
        for user_id in recipient_ids:
            cursor.execute('''
                INSERT INTO notification_recipients (notification_id, user_id)
                VALUES (?, ?)
            ''', (notification_id, user_id))
        
        conn.commit()
        conn.close()
        return notification_id
    
    def get_notifications_for_transaction(self, transaction_id):
        """الحصول على تنبيهات معاملة"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM notifications
            WHERE transaction_id = ? AND is_enabled = 1
        ''', (transaction_id,))
        notifications = cursor.fetchall()
        conn.close()
        return [dict(notif) for notif in notifications]
    
    def get_due_notifications(self):
        """الحصول على التنبيهات المستحقة للإرسال"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        cursor.execute('''
            SELECT n.*, t.title, t.end_date, t.data, tt.type_name
            FROM notifications n
            JOIN transactions t ON n.transaction_id = t.transaction_id
            JOIN transaction_types tt ON t.type_id = tt.type_id
            WHERE n.is_enabled = 1 
            AND t.status = 'active'
            AND t.end_date IS NOT NULL
        ''')
        
        all_notifications = cursor.fetchall()
        conn.close()
        
        due_notifications = []
        for notif in all_notifications:
            notif_dict = dict(notif)
            end_date = datetime.strptime(notif_dict['end_date'], '%Y-%m-%d').date()
            days_until_end = (end_date - today).days
            
            # إرسال التنبيه فقط إذا تطابق عدد الأيام
            if days_until_end == notif_dict['days_before']:
                # التحقق من عدم إرسال التنبيه اليوم
                last_sent = notif_dict.get('last_sent')
                if not last_sent or last_sent != str(today):
                    notif_dict['data'] = json.loads(notif_dict['data']) if notif_dict['data'] else {}
                    due_notifications.append(notif_dict)
        
        return due_notifications
    
    def mark_notification_sent(self, notification_id):
        """تسجيل إرسال التنبيه"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE notifications
            SET last_sent = DATE('now')
            WHERE notification_id = ?
        ''', (notification_id,))
        conn.commit()
        conn.close()
    
    def toggle_notification(self, notification_id, enabled):
        """تفعيل/إيقاف تنبيه"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE notifications
            SET is_enabled = ?
            WHERE notification_id = ?
        ''', (1 if enabled else 0, notification_id))
        conn.commit()
        conn.close()
    
    def get_notification_recipients(self, notification_id):
        """الحصول على مستلمي التنبيه"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.user_id, u.full_name, u.phone_number
            FROM notification_recipients nr
            JOIN users u ON nr.user_id = u.user_id
            WHERE nr.notification_id = ?
        ''', (notification_id,))
        recipients = cursor.fetchall()
        conn.close()
        return [dict(rec) for rec in recipients]
    
    # وظائف السيارات
    def add_vehicle_dates(self, transaction_id, insurance_date, license_date, registration_date):
        """إضافة تواريخ السيارة الثلاثة"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        dates = [
            ('تأمين', insurance_date),
            ('استمارة', registration_date),
            ('ترخيص', license_date)
        ]
        
        for date_type, date_value in dates:
            if date_value:
                cursor.execute('''
                    INSERT INTO vehicle_dates (transaction_id, date_type, expiry_date)
                    VALUES (?, ?, ?)
                ''', (transaction_id, date_type, date_value))
        
        conn.commit()
        conn.close()
    
    def get_vehicle_dates(self, transaction_id):
        """الحصول على تواريخ السيارة"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM vehicle_dates WHERE transaction_id = ?
        ''', (transaction_id,))
        dates = cursor.fetchall()
        conn.close()
        return [dict(d) for d in dates]
    
    # وظائف الجلسات القضائية
    def add_court_session(self, transaction_id, session_date, session_link='', session_notes=''):
        """إضافة جلسة قضائية"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO court_sessions (transaction_id, session_date, session_link, session_notes)
            VALUES (?, ?, ?, ?)
        ''', (transaction_id, session_date, session_link, session_notes))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def get_court_sessions(self, transaction_id):
        """الحصول على جلسات قضية"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM court_sessions
            WHERE transaction_id = ?
            ORDER BY session_date ASC
        ''', (transaction_id,))
        sessions = cursor.fetchall()
        conn.close()
        return [dict(s) for s in sessions]
    
    def complete_court_session(self, session_id):
        """تسجيل انتهاء جلسة"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE court_sessions
            SET is_completed = 1
            WHERE session_id = ?
        ''', (session_id,))
        conn.commit()
        conn.close()
    
    # وظائف أنواع المعاملات
    def get_transaction_types(self):
        """الحصول على جميع أنواع المعاملات"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM transaction_types WHERE is_active = 1')
        types = cursor.fetchall()
        conn.close()
        
        result = []
        for t in types:
            t_dict = dict(t)
            t_dict['fields_config'] = json.loads(t_dict['fields_config']) if t_dict['fields_config'] else []
            result.append(t_dict)
        return result
    
    def add_transaction_type(self, type_name, fields):
        """إضافة نوع معاملة جديد"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO transaction_types (type_name, fields_config)
                VALUES (?, ?)
            ''', (type_name, json.dumps(fields)))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
