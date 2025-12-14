import os
from flask import Flask, render_template_string, request, redirect, jsonify, session
from datetime import datetime, timedelta
from database_supabase import Database
from ai_agent import AIAgent
import secrets
import json


logger = logging.getLogger(__name__)

Base = declarative_base()

# ==================== النماذج ====================

class TransactionType(Base):
    __tablename__ = 'transaction_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(10))

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    is_admin = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = 'transactions'
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    data = Column(Text)
    end_date = Column(String(20), nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = 'notifications'
    
    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, nullable=False)
    days_before = Column(Integer, nullable=False)
    recipients = Column(Text, nullable=False)
    sent = Column(Integer, default=0)
    last_sent = Column(DateTime)

# ==================== Database Class ====================

class Database:
    def __init__(self):
        """إنشاء اتصال بقاعدة بيانات Supabase"""
        
        # جلب DATABASE_URL من متغيرات البيئة
        database_url = os.environ.get('SUPABASE_DATABASE_URL')
        
        if not database_url:
            raise Exception("❌ SUPABASE_DATABASE_URL غير موجود في متغيرات البيئة!")
        
        logger.info("🔗 الاتصال بقاعدة بيانات Supabase...")
        
        # إنشاء المحرك
        self.engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        
        # إنشاء الجداول
        Base.metadata.create_all(self.engine)
        logger.info("✅ تم إنشاء الجداول بنجاح")
        
        # إنشاء الجلسة
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # إضافة أنواع المعاملات الافتراضية
        self._init_transaction_types()
        logger.info("✅ قاعدة البيانات جاهزة!")
    
    def _init_transaction_types(self):
        """إضافة أنواع المعاملات الافتراضية"""
        types = [
            (1, 'عقد عمل', '📝'),
            (2, 'إجازة موظف', '🏖️'),
            (3, 'استمارة سيارة', '🚗'),
            (4, 'ترخيص', '📄'),
            (5, 'جلسة قضائية', '⚖️')
        ]
        
        for type_id, name, icon in types:
            try:
                exists = self.session.query(TransactionType).filter_by(id=type_id).first()
                if not exists:
                    trans_type = TransactionType(id=type_id, name=name, icon=icon)
                    self.session.add(trans_type)
            except:
                pass
        
        try:
            self.session.commit()
        except:
            self.session.rollback()
    
    def add_user(self, user_id, phone_number, full_name, is_admin=0):
        """إضافة أو تحديث مستخدم"""
        try:
            user = self.session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.phone_number = phone_number
                user.full_name = full_name
                user.is_admin = is_admin
            else:
                user = User(user_id=user_id, phone_number=phone_number, 
                           full_name=full_name, is_admin=is_admin)
                self.session.add(user)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"خطأ في إضافة المستخدم: {e}")
            return False
    
    def get_user(self, user_id):
        """جلب مستخدم"""
        try:
            user = self.session.query(User).filter_by(user_id=user_id).first()
            if user:
                return {
                    'user_id': user.user_id,
                    'phone_number': user.phone_number,
                    'full_name': user.full_name,
                    'is_admin': user.is_admin,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
            return None
        except Exception as e:
            logger.error(f"خطأ في جلب المستخدم: {e}")
            return None
    
    def get_all_users(self):
        """جلب جميع المستخدمين"""
        try:
            users = self.session.query(User).order_by(User.full_name).all()
            return [{
                'user_id': u.user_id,
                'phone_number': u.phone_number,
                'full_name': u.full_name,
                'is_admin': u.is_admin,
                'created_at': u.created_at.isoformat() if u.created_at else None
            } for u in users]
        except:
            return []
    
    def delete_user(self, user_id):
        """حذف مستخدم"""
        try:
            user = self.session.query(User).filter_by(user_id=user_id).first()
            if user:
                self.session.delete(user)
                self.session.commit()
                return True
            return False
        except:
            self.session.rollback()
            return False
    
    def add_transaction(self, transaction_type_id, user_id, title, data, end_date):
        """إضافة معاملة"""
        try:
            data_json = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else '{}'
            trans = Transaction(
                transaction_type_id=transaction_type_id,
                user_id=user_id,
                title=title,
                data=data_json,
                end_date=end_date,
                is_active=1
            )
            self.session.add(trans)
            self.session.commit()
            return trans.transaction_id
        except Exception as e:
            self.session.rollback()
            logger.error(f"خطأ في إضافة المعاملة: {e}")
            return None
    
    def update_transaction(self, transaction_id, title, end_date, data=None):
        """تحديث معاملة"""
        try:
            trans = self.session.query(Transaction).filter_by(transaction_id=transaction_id).first()
            if trans:
                trans.title = title
                trans.end_date = end_date
                if data:
                    trans.data = json.dumps(data, ensure_ascii=False)
                self.session.commit()
                return True
            return False
        except:
            self.session.rollback()
            return False
    
    def get_transaction(self, transaction_id):
        """جلب معاملة"""
        try:
            trans = self.session.query(Transaction).filter_by(transaction_id=transaction_id).first()
            if trans:
                return {
                    'transaction_id': trans.transaction_id,
                    'transaction_type_id': trans.transaction_type_id,
                    'user_id': trans.user_id,
                    'title': trans.title,
                    'data': json.loads(trans.data) if trans.data else {},
                    'end_date': trans.end_date,
                    'is_active': trans.is_active,
                    'created_at': trans.created_at.isoformat() if trans.created_at else None
                }
            return None
        except:
            return None
    
    def get_active_transactions(self, user_id=None):
        """جلب المعاملات النشطة"""
        try:
            query = self.session.query(Transaction).filter_by(is_active=1)
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            transactions = query.order_by(Transaction.end_date).all()
            return [{
                'transaction_id': t.transaction_id,
                'transaction_type_id': t.transaction_type_id,
                'user_id': t.user_id,
                'title': t.title,
                'data': json.loads(t.data) if t.data else {},
                'end_date': t.end_date,
                'is_active': t.is_active,
                'created_at': t.created_at.isoformat() if t.created_at else None
            } for t in transactions]
        except Exception as e:
            logger.error(f"خطأ في جلب المعاملات: {e}")
            return []
    
    def delete_transaction(self, transaction_id):
        """حذف معاملة"""
        try:
            trans = self.session.query(Transaction).filter_by(transaction_id=transaction_id).first()
            if trans:
                self.session.delete(trans)
                self.session.query(Notification).filter_by(transaction_id=transaction_id).delete()
                self.session.commit()
                return True
            return False
        except:
            self.session.rollback()
            return False
    
    def add_notification(self, transaction_id, days_before, recipients):
        """إضافة تنبيه"""
        try:
            recipients_json = json.dumps(recipients)
            notif = Notification(
                transaction_id=transaction_id,
                days_before=days_before,
                recipients=recipients_json
            )
            self.session.add(notif)
            self.session.commit()
            return True
        except:
            self.session.rollback()
            return False
    
    def get_transaction_types(self):
        """جلب أنواع المعاملات"""
        try:
            types = self.session.query(TransactionType).all()
            return [{
                'id': t.id,
                'name': t.name,
                'icon': t.icon
            } for t in types]
        except:
            return []
    
    def close(self):
        """إغلاق الجلسة"""
        self.session.close()
