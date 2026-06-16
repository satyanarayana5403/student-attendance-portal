from flask import Blueprint, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from models import SupportTicket
from extensions import db

support_bp = Blueprint('support', __name__)

@support_bp.route('/', methods=['GET'])
@login_required
def support_tickets():
    if current_user.role == 'admin':
        return redirect(url_for('admin.management_page') + '#support')
    
    # Render support page (returns JSON for JS modals in the dashboard)
    tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(SupportTicket.created_at.desc()).all()
    return jsonify([
        {
            'id': t.id,
            'subject': t.subject,
            'message': t.message,
            'status': t.status,
            'admin_reply': t.admin_reply,
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
        } for t in tickets
    ])

@support_bp.route('/new', methods=['POST'])
@login_required
def new_support_ticket():
    data = request.get_json()
    if not data or not data.get('subject') or not data.get('message'):
        return jsonify({'success': False, 'message': 'Subject and message are required'}), 400
        
    ticket = SupportTicket(
        user_id=current_user.id,
        subject=data['subject'],
        message=data['message']
    )
    db.session.add(ticket)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Support ticket submitted successfully'})
