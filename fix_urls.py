import os
import re

mapping = {
    'login': 'auth.login', 
    'logout': 'auth.logout', 
    'change_password': 'auth.change_password', 
    'index': 'main.index', 
    'upload_profile': 'main.upload_profile', 
    'management_page': 'admin.management_page', 
    'register_user': 'admin.register_user', 
    'edit_user': 'admin.edit_user', 
    'delete_user': 'admin.delete_user', 
    'admin_mark_attendance': 'admin.admin_mark_attendance', 
    'export_data': 'admin.export_data', 
    'teacher_dashboard': 'teacher.teacher_dashboard', 
    'teacher_mark_self': 'teacher.teacher_mark_self', 
    'teacher_mark_student': 'teacher.teacher_mark_student', 
    'student_dashboard': 'student.student_dashboard', 
    'api_settings': 'api.api_settings', 
    'api_stats': 'api.api_stats', 
    'get_stats': 'main.get_stats', 
    'api_attendance_trend': 'api.api_attendance_trend', 
    'api_students_search': 'api.api_students_search', 
    'mark_attendance_api': 'main.mark_attendance_api',
    'support_tickets': 'support.support_tickets',
    'new_support_ticket': 'support.new_support_ticket'
}

templates_dir = 'templates'
for filename in os.listdir(templates_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(templates_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        def replacer(match):
            route = match.group(1)
            # Only replace if it's in our mapping (ignore static, etc.)
            new_route = mapping.get(route, route)
            return f"url_for('{new_route}'"
            
        new_content = re.sub(r"url_for\(['\"](.*?)['\"]", replacer, content)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filename}")
