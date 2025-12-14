"""
MCP Server لتمكين التكامل مع أدوات AI الخارجية
مثل Claude Desktop, ChatGPT, وغيرها
"""

from flask import Flask, jsonify, request
from database_supabase import Database
from ai_agent import AIAgent
import json

mcp_app = Flask(__name__)
db = Database()
ai = AIAgent()

@mcp_app.route('/mcp/tools', methods=['GET'])
def list_tools():
    """قائمة الأدوات المتاحة"""
    return jsonify({
        'tools': [
            {
                'name': 'get_transactions',
                'description': 'احصل على قائمة المعاملات',
                'parameters': {
                    'user_id': {'type': 'integer', 'optional': True}
                }
            },
            {
                'name': 'add_transaction',
                'description': 'أضف معاملة جديدة',
                'parameters': {
                    'title': {'type': 'string'},
                    'end_date': {'type': 'string'},
                    'type_id': {'type': 'integer'}
                }
            },
            {
                'name': 'analyze_transactions',
                'description': 'حلل المعاملات بواسطة AI',
                'parameters': {}
            }
        ]
    })

@mcp_app.route('/mcp/execute', methods=['POST'])
def execute_tool():
    """تنفيذ أداة"""
    data = request.json
    tool_name = data.get('tool')
    params = data.get('parameters', {})
    
    if tool_name == 'get_transactions':
        transactions = db.get_active_transactions(user_id=params.get('user_id'))
        return jsonify({'success': True, 'result': transactions})
    
    elif tool_name == 'add_transaction':
        trans_id = db.add_transaction(
            transaction_type_id=params['type_id'],
            user_id=params.get('user_id', 1),
            title=params['title'],
            data={},
            end_date=params['end_date']
        )
        return jsonify({'success': True, 'transaction_id': trans_id})
    
    elif tool_name == 'analyze_transactions':
        analysis = ai.analyze_transactions()
        return jsonify({'success': True, 'result': analysis})
    
    return jsonify({'success': False, 'error': 'Unknown tool'}), 400

if __name__ == '__main__':
    mcp_app.run(host='0.0.0.0', port=5002)
