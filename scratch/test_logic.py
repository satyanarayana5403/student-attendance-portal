import json, urllib.request, time

req = urllib.request.Request('http://127.0.0.1:5000/api/absentees')
req.add_header('Cookie', 'session=eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIn0.xxx;') # we might not have a valid session cookie

# Let's just mock the logic to see python behaviour
results = {'sent': 0, 'failed': 0, 'skipped': 0, 'details': []}

class DummyStudent:
    def __init__(self, name, email):
        self.name = name
        self.email = email

absent_students = [
    {'name': 'S1', 'email': 'student1@example.com'},
    {'name': 'S2', 'email': 's2@example.com'}
]

def send_email(to, sub, body):
    return True

for student in absent_students:
    try:
        ok = send_email(student['email'], "sub", "body")
        if ok:
            results['sent'] += 1
            results['details'].append({'name': student['name'], 'status': 'sent'})
        else:
            results['failed'] += 1
            results['details'].append({'name': student['name'], 'status': 'failed'})
    except Exception as e:
        results['failed'] += 1
        results['details'].append({'name': student['name'], 'status': 'failed'})

print(json.dumps(results, indent=2))
