import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_name='transactions.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        
        # جدول أنواع المعاملات
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_types (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                icon TEXT
            )
        ''')
        
        # جدول المستخدمين
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                phone_number TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول المعاملات
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_type_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                data TEXT,
                end_date TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_type_id) REFERENCES transaction_types(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # جدول التنبيهات
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                days_before INTEGER NOT NULL,
                recipients TEXT NOT NULL,
                sent INTEGER DEFAULT 0,
                last_sent TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
            )
        ''')
        
        # إضافة أنواع المعاملات الافتراضية
        types = [
            (1, 'عقد عمل', '📝'),
            (2, 'إجازة موظف', '🏖️'),
            (3, 'استمارة سيارة', '🚗'),
            (4, 'ترخيص', '📄'),
            (5, 'جلسة قضائية', '⚖️')
        ]
        
        for type_id, name, icon in types:
            try:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO transaction_types (id, name, icon)
                    VALUES (?, ?, ?)
                ''', (type_id, name, icon))
            except:
                pass
        
        self.conn.commit()
    
    def add_user(self, user_id, phone_number, full_name, is_admin=0):
        """إضافة مستخدم جديد"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, phone_number, full_name, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (user_id, phone_number, full_name, is_admin))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"خطأ في إضافة المستخدم: {e}")
            return False
    
    def get_user(self, user_id):
        """جلب بيانات مستخدم"""
        try:
            row = self.cursor.execute('''
                SELECT * FROM users WHERE user_id = ?
            ''', (user_id,)).fetchone()
            
            if row:
                return dict(row)
            return None
        except:
            return None
    
    def get_all_users(self):
        """جلب جميع المستخدمين"""
        try:
            rows = self.cursor.execute('SELECT * FROM users ORDER BY full_name').fetchall()
            return [dict(row) for row in rows]
        except:
            return []
    
    def delete_user(self, user_id):
        """حذف مستخدم"""
        try:
            self.cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            self.conn.commit()
            return True
        except:
            return False
    
    def add_transaction(self, transaction_type_id, user_id, title, data, end_date):
        """إضافة معاملة جديدة"""
        try:
            data_json = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else json.dumps({})
            
            self.cursor.execute('''
                INSERT INTO transactions (transaction_type_id, user_id, title, data, end_date, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (transaction_type_id, user_id, title, data_json, end_date))
            
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"خطأ في إضافة المعاملة: {e}")
            self.conn.rollback()
            return None
    
    def update_transaction(self, transaction_id, title, end_date, data=None):
        """تحديث معاملة"""
        try:
            if data:
                data_json = json.dumps(data, ensure_ascii=False)
                self.cursor.execute('''
                    UPDATE transactions 
                    SET title = ?, end_date = ?, data = ?
                    WHERE transaction_id = ?
                ''', (title, end_date, data_json, transaction_id))
            else:
                self.cursor.execute('''
                    UPDATE transactions 
                    SET title = ?, end_date = ?
                    WHERE transaction_id = ?
                ''', (title, end_date, transaction_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"خطأ في تحديث المعاملة: {e}")
            return False
    
    def get_transaction(self, transaction_id):
        """جلب معاملة واحدة"""
        try:
            row = self.cursor.execute('''
                SELECT * FROM transactions WHERE transaction_id = ?
            ''', (transaction_id,)).fetchone()
            
            if row:
                trans = dict(row)
                if trans.get('data'):
                    try:
                        trans['data'] = json.loads(trans['data'])
                    except:
                        trans['data'] = {}
                return trans
            return None
        except:
            return None
    
    def get_active_transactions(self, user_id=None):
        """جلب المعاملات النشطة"""
        try:
            if user_id:
                rows = self.cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE is_active = 1 AND user_id = ?
                    ORDER BY end_date
                ''', (user_id,)).fetchall()
            else:
                rows = self.cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE is_active = 1
                    ORDER BY end_date
                ''').fetchall()
            
            transactions = []
            for row in rows:
                trans = dict(row)
                if trans.get('data'):
                    try:
                        trans['data'] = json.loads(trans['data'])
                    except:
                        trans['data'] = {}
                transactions.append(trans)
            
            return transactions
        except Exception as e:
            print(f"خطأ في جلب المعاملات: {e}")
            return []
    
    def delete_transaction(self, transaction_id):
        """حذف معاملة"""
        try:
            self.cursor.execute('DELETE FROM transactions WHERE transaction_id = ?', (transaction_id,))
            self.cursor.execute('DELETE FROM notifications WHERE transaction_id = ?', (transaction_id,))
            self.conn.commit()
            return True
        except:
            return False
    
    def add_notification(self, transaction_id, days_before, recipients):
        """إضافة تنبيه"""
        try:
            recipients_json = json.dumps(recipients)
            self.cursor.execute('''
                INSERT INTO notifications (transaction_id, days_before, recipients)
                VALUES (?, ?, ?)
            ''', (transaction_id, days_before, recipients_json))
            self.conn.commit()
            return True
        except:
            return False
    
    def get_pending_notifications(self):
        """جلب التنبيهات المعلقة"""
        try:
            rows = self.cursor.execute('''
                SELECT n.*, t.title, t.end_date, t.transaction_type_id
                FROM notifications n
                JOIN transactions t ON n.transaction_id = t.transaction_id
                WHERE t.is_active = 1 AND n.sent = 0
            ''').fetchall()
            
            notifications = []
            for row in rows:
                notif = dict(row)
                if notif.get('recipients'):
                    try:
                        notif['recipients'] = json.loads(notif['recipients'])
                    except:
                        notif['recipients'] = []
                notifications.append(notif)
            
            return notifications
        except:
            return []
    
    def mark_notification_sent(self, notification_id):
        """تعليم تنبيه كمُرسل"""
        try:
            self.cursor.execute('''
                UPDATE notifications 
                SET sent = 1, last_sent = ?
                WHERE notification_id = ?
            ''', (datetime.now().isoformat(), notification_id))
            self.conn.commit()
            return True
        except:
            return False
    
    def get_transaction_types(self):
        """جلب أنواع المعاملات"""
        try:
            rows = self.cursor.execute('SELECT * FROM transaction_types').fetchall()
            return [dict(row) for row in rows]
        except:
            return []
    
    def close(self):
        """إغلاق الاتصال"""
        self.conn.close()
