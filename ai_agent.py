import logging

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self, db):
        self.db = db
    
    def analyze_all_transactions(self, user_id=None):
        try:
            if user_id:
                transactions = self.db.get_transactions_by_role(user_id)
            else:
                transactions = self.db.get_active_transactions()
            
            critical = [t for t in transactions if t.get('days_left', 999) <= 3]
            warning = [t for t in transactions if 4 <= t.get('days_left', 999) <= 7]
            
            recommendations = []
            if critical:
                recommendations.append({
                    'icon': '🔴',
                    'title': f'{len(critical)} معاملة عاجلة تحتاج متابعة فورية',
                    'priority': 'critical'
                })
            if warning:
                recommendations.append({
                    'icon': '🟡',
                    'title': f'{len(warning)} معاملة تحتاج متابعة خلال أسبوع',
                    'priority': 'warning'
                })
            
            return {
                'total_transactions': len(transactions),
                'critical': critical,
                'warning': warning,
                'recommendations': recommendations
            }
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {
                'total_transactions': 0,
                'critical': [],
                'warning': [],
                'recommendations': []
            }
