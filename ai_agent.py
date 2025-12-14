"""
🤖 AI Agent - المساعد الذكي المحلي
نظام تحليل ذكي بدون استهلاك APIs خارجية
مع Roadmap كامل للتحديثات المستقبلية
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import logging

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 📋 ROADMAP للتطوير المستقبلي ====================
"""
VERSION 1.0.0 (Current) ✅
- تحليل محلي ذكي بدون AI خارجي
- جدولة ذكية حسب الأولوية
- توقع التأخيرات بناءً على الإحصائيات
- توصيات ذكية

VERSION 1.1.0 (Next Release) 🔜
- [ ] تحليل الأنماط التاريخية (Pattern Analysis)
- [ ] اقتراحات تحسين الأداء
- [ ] تنبيهات استباقية (Proactive Alerts)
- [ ] تقارير أسبوعية تلقائية

VERSION 1.2.0 (Future) 🔮
- [ ] Machine Learning للتنبؤ بالتأخيرات
- [ ] تكامل مع DeepSeek (اختياري)
- [ ] تحليل النصوص بـ NLP
- [ ] توليد تقارير تلقائية بـ AI

VERSION 2.0.0 (Advanced) 🚀
- [ ] Multi-Agent System
- [ ] Real-time Monitoring
- [ ] Predictive Analytics
- [ ] Auto-remediation
"""

class AIAgent:
    """
    المساعد الذكي - يعمل بذكاء محلي بدون الحاجة لـ APIs خارجية
    """
    
    # ==================== الإعدادات ====================
    ROADMAP_VERSION = "1.0.0"
    
    # حدود التنبيهات
    CRITICAL_DAYS = 3
    WARNING_DAYS = 7
    UPCOMING_DAYS = 30
    
    # أوزان الأولوية
    PRIORITY_WEIGHTS = {
        'critical': 4,
        'high': 3,
        'normal': 2,
        'low': 1
    }
    
    def __init__(self, database):
        """
        تهيئة المساعد الذكي
        
        Args:
            database: كائن قاعدة البيانات
        """
        self.db = database
        self.deepseek_enabled = False  # معطّل افتراضياً
        self.deepseek_key = os.environ.get('DEEPSEEK_API_KEY')
        
        logger.info(f"✅ تم تهيئة AI Agent v{self.ROADMAP_VERSION}")
        logger.info(f"🔌 DeepSeek: {'مفعّل' if self.deepseek_key else 'معطّل'}")
    
    # ==================== التحليل الذكي ====================
    
    def analyze_all_transactions(self, user_id: int = None) -> Dict:
        """
        تحليل شامل لجميع المعاملات
        
        Returns:
            dict: تحليل شامل يحتوي على:
                - الإحصائيات العامة
                - المعاملات الحرجة
                - التوصيات الذكية
                - توزيع الأولويات
        """
        logger.info(f"🔍 بدء التحليل الشامل...")
        
        # جلب المعاملات
        transactions = self.db.get_transactions_by_role(user_id) if user_id else self.db.get_active_transactions()
        today = datetime.now().date()
        
        analysis = {
            'version': self.ROADMAP_VERSION,
            'analyzed_at': datetime.now().isoformat(),
            'total_transactions': len(transactions),
            'critical': [],
            'warning': [],
            'upcoming': [],
            'safe': [],
            'by_type': {},
            'by_department': {},
            'by_priority': {'critical': 0, 'high': 0, 'normal': 0, 'low': 0},
            'overdue': [],
            'today_ending': [],
            'recommendations': [],
            'statistics': {}
        }
        
        # تحليل كل معاملة
        for trans in transactions:
            try:
                days_left = trans['days_left']
                
                # تصنيف حسب الأيام المتبقية
                if days_left < 0:
                    analysis['overdue'].append(trans)
                elif days_left == 0:
                    analysis['today_ending'].append(trans)
                    analysis['critical'].append(trans)
                elif days_left <= self.CRITICAL_DAYS:
                    analysis['critical'].append(trans)
                elif days_left <= self.WARNING_DAYS:
                    analysis['warning'].append(trans)
                elif days_left <= self.UPCOMING_DAYS:
                    analysis['upcoming'].append(trans)
                else:
                    analysis['safe'].append(trans)
                
                # تصنيف حسب النوع
                type_name = trans.get('parent_type_name') or trans['type_name']
                if type_name not in analysis['by_type']:
                    analysis['by_type'][type_name] = {
                        'count': 0,
                        'critical': 0,
                        'icon': trans.get('type_icon', '📋')
                    }
                analysis['by_type'][type_name]['count'] += 1
                if days_left <= self.CRITICAL_DAYS:
                    analysis['by_type'][type_name]['critical'] += 1
                
                # تصنيف حسب القسم
                department = trans.get('user_department', 'غير محدد')
                if department not in analysis['by_department']:
                    analysis['by_department'][department] = 0
                analysis['by_department'][department] += 1
                
                # تصنيف حسب الأولوية
                priority = trans.get('priority', 'normal')
                analysis['by_priority'][priority] += 1
                
            except Exception as e:
                logger.error(f"❌ خطأ في تحليل المعاملة {trans.get('transaction_id')}: {e}")
                continue
        
        # توليد التوصيات الذكية
        analysis['recommendations'] = self._generate_recommendations(analysis)
        
        # حساب الإحصائيات
        analysis['statistics'] = self._calculate_statistics(analysis, transactions)
        
        logger.info(f"✅ اكتمل التحليل: {len(transactions)} معاملة")
        return analysis
    
    def _generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """
        توليد توصيات ذكية بناءً على التحليل
        """
        recommendations = []
        
        # توصيات للمعاملات المنتهية
        if len(analysis['overdue']) > 0:
            recommendations.append({
                'type': 'urgent',
                'priority': 'critical',
                'icon': '🚨',
                'title': 'معاملات منتهية!',
                'message': f"لديك {len(analysis['overdue'])} معاملة منتهية. يجب التعامل معها فوراً!",
                'action': 'review_overdue',
                'count': len(analysis['overdue'])
            })
        
        # توصيات للمعاملات الحرجة
        critical_count = len(analysis['critical'])
        if critical_count > 5:
            recommendations.append({
                'type': 'urgent',
                'priority': 'high',
                'icon': '⚠️',
                'title': 'حمل عمل مرتفع',
                'message': f"لديك {critical_count} معاملة عاجلة. يُنصح بإعادة تنظيم الأولويات",
                'action': 'reorganize_priorities',
                'count': critical_count
            })
        elif critical_count > 0:
            recommendations.append({
                'type': 'info',
                'priority': 'normal',
                'icon': '📌',
                'title': 'معاملات عاجلة',
                'message': f"لديك {critical_count} معاملة تتطلب انتباهك قريباً",
                'action': 'review_critical',
                'count': critical_count
            })
        
        # توصيات للتخطيط
        warning_count = len(analysis['warning'])
        if warning_count > 10:
            recommendations.append({
                'type': 'planning',
                'priority': 'normal',
                'icon': '📅',
                'title': 'خطط مسبقاً',
                'message': f"{warning_count} معاملة خلال الأسبوع القادم. ابدأ بالتحضير",
                'action': 'plan_week',
                'count': warning_count
            })
        
        # توصيات حسب القسم
        for type_name, data in analysis['by_type'].items():
            if data['critical'] > 3:
                recommendations.append({
                    'type': 'department',
                    'priority': 'normal',
                    'icon': data['icon'],
                    'title': f'تركيز على {type_name}',
                    'message': f"{data['critical']} معاملة عاجلة في قسم {type_name}",
                    'action': f'focus_type_{type_name}',
                    'count': data['critical']
                })
        
        # توصيات إيجابية
        if critical_count == 0 and len(analysis['overdue']) == 0:
            recommendations.append({
                'type': 'positive',
                'priority': 'info',
                'icon': '🎉',
                'title': 'عمل ممتاز!',
                'message': 'لا توجد معاملات عاجلة. استمر بهذا الأداء الرائع!',
                'action': 'keep_going',
                'count': 0
            })
        
        # ترتيب حسب الأولوية
        priority_order = {'critical': 0, 'high': 1, 'normal': 2, 'info': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 999))
        
        return recommendations
    
    def _calculate_statistics(self, analysis: Dict, transactions: List[Dict]) -> Dict:
        """
        حساب إحصائيات متقدمة
        """
        stats = {
            'completion_rate': 0,
            'average_days_left': 0,
            'busiest_department': None,
            'busiest_type': None,
            'response_time': {
                'excellent': 0,  # > 30 days
                'good': 0,       # 7-30 days
                'acceptable': 0, # 3-7 days
                'critical': 0    # < 3 days
            }
        }
        
        if not transactions:
            return stats
        
        # متوسط الأيام المتبقية
        days_list = [t['days_left'] for t in transactions if t.get('days_left') is not None]
        if days_list:
            stats['average_days_left'] = round(sum(days_list) / len(days_list), 1)
        
        # القسم الأكثر انشغالاً
        if analysis['by_department']:
            busiest_dept = max(analysis['by_department'].items(), key=lambda x: x[1])
            stats['busiest_department'] = {
                'name': busiest_dept[0],
                'count': busiest_dept[1]
            }
        
        # النوع الأكثر انشغالاً
        if analysis['by_type']:
            busiest_type = max(analysis['by_type'].items(), key=lambda x: x[1]['count'])
            stats['busiest_type'] = {
                'name': busiest_type[0],
                'count': busiest_type[1]['count'],
                'icon': busiest_type[1]['icon']
            }
        
        # تصنيف وقت الاستجابة
        for trans in transactions:
            days = trans.get('days_left', 0)
            if days > 30:
                stats['response_time']['excellent'] += 1
            elif days >= 7:
                stats['response_time']['good'] += 1
            elif days >= 3:
                stats['response_time']['acceptable'] += 1
            else:
                stats['response_time']['critical'] += 1
        
        return stats
    
    # ==================== الجدولة الذكية ====================
    
    def smart_scheduling(self, user_id: int = None) -> Dict:
        """
        جدولة ذكية للمعاملات حسب الأولوية
        
        Returns:
            dict: جدول منظم للمعاملات
        """
        logger.info("📅 إنشاء جدول ذكي...")
        
        transactions = self.db.get_transactions_by_role(user_id) if user_id else self.db.get_active_transactions()
        
        schedule = {
            'today': [],
            'this_week': [],
            'next_week': [],
            'this_month': [],
            'later': []
        }
        
        today = datetime.now().date()
        week_end = today + timedelta(days=7)
        next_week_end = today + timedelta(days=14)
        month_end = today + timedelta(days=30)
        
        # تصنيف حسب الوقت
        for trans in transactions:
            try:
                end_date = datetime.strptime(trans['end_date'], '%Y-%m-%d').date()
                days_left = (end_date - today).days
                
                # إضافة نقاط الأولوية
                priority_weight = self.PRIORITY_WEIGHTS.get(trans.get('priority', 'normal'), 2)
                trans['calculated_priority'] = priority_weight * (1 / max(days_left, 1))
                
                if end_date <= today:
                    schedule['today'].append(trans)
                elif end_date <= week_end:
                    schedule['this_week'].append(trans)
                elif end_date <= next_week_end:
                    schedule['next_week'].append(trans)
                elif end_date <= month_end:
                    schedule['this_month'].append(trans)
                else:
                    schedule['later'].append(trans)
            except:
                continue
        
        # ترتيب كل فئة حسب الأولوية المحسوبة
        for key in schedule:
            schedule[key].sort(key=lambda x: x.get('calculated_priority', 0), reverse=True)
        
        logger.info(f"✅ تم إنشاء الجدول: {sum(len(v) for v in schedule.values())} معاملة")
        return schedule
    
    # ==================== التنبؤ بالتأخيرات ====================
    
    def predict_delays(self, transaction_id: int) -> Dict:
        """
        التنبؤ باحتمالية تأخر معاملة
        
        Args:
            transaction_id: رقم المعاملة
            
        Returns:
            dict: احتمالية التأخر والعوامل المؤثرة
        """
        transaction = self.db.get_transaction(transaction_id)
        if not transaction:
            return {'error': 'المعاملة غير موجودة'}
        
        # عوامل التنبؤ
        factors = []
        risk_score = 0.0
        
        days_left = transaction['days_left']
        
        # عامل الوقت المتبقي
        if days_left <= 1:
            risk_score += 0.8
            factors.append({'factor': 'وقت قليل جداً', 'impact': 'high', 'score': 0.8})
        elif days_left <= 3:
            risk_score += 0.5
            factors.append({'factor': 'وقت محدود', 'impact': 'medium', 'score': 0.5})
        elif days_left <= 7:
            risk_score += 0.2
            factors.append({'factor': 'وقت مقبول', 'impact': 'low', 'score': 0.2})
        
        # عامل الأولوية
        priority = transaction.get('priority', 'normal')
        if priority == 'critical':
            risk_score += 0.3
            factors.append({'factor': 'أولوية حرجة', 'impact': 'high', 'score': 0.3})
        
        # عامل التنبيهات المرسلة
        notifications_sent = transaction.get('notifications_sent_count', 0)
        if notifications_sent > 3:
            risk_score += 0.2
            factors.append({'factor': 'تنبيهات متعددة مُرسلة', 'impact': 'medium', 'score': 0.2})
        
        # تحديد مستوى الخطر
        if risk_score >= 0.7:
            risk_level = 'critical'
            risk_label = 'خطر عالي جداً'
            recommendation = 'يجب التعامل معها فوراً!'
        elif risk_score >= 0.5:
            risk_level = 'high'
            risk_label = 'خطر عالي'
            recommendation = 'يُنصح بالمتابعة العاجلة'
        elif risk_score >= 0.3:
            risk_level = 'medium'
            risk_label = 'خطر متوسط'
            recommendation = 'راقب عن كثب'
        else:
            risk_level = 'low'
            risk_label = 'خطر منخفض'
            recommendation = 'استمر بالمتابعة العادية'
        
        return {
            'transaction_id': transaction_id,
            'title': transaction['title'],
            'days_left': days_left,
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'risk_label': risk_label,
            'probability': f"{round(risk_score * 100)}%",
            'factors': factors,
            'recommendation': recommendation,
            'analyzed_at': datetime.now().isoformat()
        }
    
    # ==================== البحث الذكي ====================
    
    def smart_search(self, query: str, user_id: int = None) -> Dict:
        """
        بحث ذكي في المعاملات
        
        Args:
            query: نص البحث
            user_id: معرف المستخدم (اختياري)
            
        Returns:
            dict: نتائج البحث مع التحليل
        """
        logger.info(f"🔍 بحث ذكي عن: {query}")
        
        # كلمات مفتاحية
        urgent_keywords = ['عاجل', 'مهم', 'فوري', 'critical', 'urgent']
        type_keywords = {
            'عقد': 1, 'عقود': 1,
            'إجازة': 2, 'إجازات': 2,
            'سيارة': 3, 'سيارات': 3,
            'ترخيص': 4, 'تراخيص': 4,
            'قضية': 5, 'قضايا': 5
        }
        
        filters = {}
        
        # تحليل الاستعلام
        query_lower = query.lower()
        
        # البحث عن النوع
        for keyword, type_id in type_keywords.items():
            if keyword in query_lower:
                filters['type_id'] = type_id
                break
        
        # البحث عن الأولوية
        for keyword in urgent_keywords:
            if keyword in query_lower:
                filters['days_range'] = 'critical'
                break
        
        # البحث النصي
        filters['search'] = query
        
        # جلب النتائج
        results = self.db.get_transactions_by_role(user_id, filters)
        
        return {
            'query': query,
            'filters_applied': filters,
            'results_count': len(results),
            'results': results[:20],  # أول 20 نتيجة
            'searched_at': datetime.now().isoformat()
        }
    
    # ==================== التكامل مع DeepSeek (اختياري) ====================
    
    def ask_deepseek(self, question: str, context: Dict = None) -> str:
        """
        استخدام DeepSeek للأسئلة المعقدة (اختياري)
        
        Args:
            question: السؤال
            context: سياق إضافي
            
        Returns:
            str: الإجابة
        """
        if not self.deepseek_enabled or not self.deepseek_key:
            return "❌ DeepSeek غير مفعّل. يعمل النظام بالتحليل المحلي فقط."
        
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=self.deepseek_key,
                base_url="https://api.deepseek.com"
            )
            
            # بناء الرسالة
            system_prompt = """أنت مساعد ذكي لإدارة المعاملات. 
مهمتك مساعدة المستخدمين بتحليل معاملاتهم وإعطاء توصيات مفيدة.
كن مختصراً ومباشراً في إجاباتك."""
            
            user_message = question
            if context:
                user_message += f"\n\nالسياق:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            logger.info(f"✅ DeepSeek: استجابة ناجحة")
            return answer
            
        except Exception as e:
            logger.error(f"❌ DeepSeek: {e}")
            return f"❌ فشل الاتصال بـ DeepSeek: {str(e)}"
    
    # ==================== التقارير ====================
    
    def generate_report(self, user_id: int = None, report_type: str = 'summary') -> Dict:
        """
        توليد تقرير شامل
        
        Args:
            user_id: معرف المستخدم
            report_type: نوع التقرير (summary, detailed, weekly)
            
        Returns:
            dict: التقرير
        """
        logger.info(f"📊 توليد تقرير: {report_type}")
        
        analysis = self.analyze_all_transactions(user_id)
        schedule = self.smart_scheduling(user_id)
        
        report = {
            'type': report_type,
            'generated_at': datetime.now().isoformat(),
            'user_id': user_id,
            'summary': {
                'total': analysis['total_transactions'],
                'critical': len(analysis['critical']),
                'warning': len(analysis['warning']),
                'overdue': len(analysis['overdue'])
            },
            'analysis': analysis,
            'schedule': schedule,
            'roadmap_version': self.ROADMAP_VERSION
        }
        
        logger.info(f"✅ تم توليد التقرير")
        return report

# ==================== Helper Functions ====================

def get_ai_insights(db, user_id: int = None) -> str:
    """
    الحصول على رؤى ذكية نصية
    
    Args:
        db: قاعدة البيانات
        user_id: معرف المستخدم
        
    Returns:
        str: رؤى نصية
    """
    agent = AIAgent(db)
    analysis = agent.analyze_all_transactions(user_id)
    
    insights = f"""
📊 **التحليل الذكي**

📈 الإحصائيات:
- إجمالي المعاملات: {analysis['total_transactions']}
- عاجلة: {len(analysis['critical'])} 🔴
- تحذير: {len(analysis['warning'])} 🟡
- منتهية: {len(analysis['overdue'])} ⚫

🎯 التوصيات الرئيسية:
"""
    
    for i, rec in enumerate(analysis['recommendations'][:3], 1):
        insights += f"\n{i}. {rec['icon']} {rec['title']}: {rec['message']}"
    
    return insights

# ==================== انتهى الملف ====================
