import os, json
from flask import Flask, request, jsonify, render_template, Response, send_from_directory
from flask_sqlalchemy import SQLAlchemy

# Tell Flask to find HTML templates in the 'templates' folder
app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dashboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(100), nullable=True, default='server')
    category = db.Column(db.String(50), nullable=False, default='General')
    is_online = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'icon': self.icon,
            'category': self.category,
            'is_online': self.is_online
        }

class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {'key': self.key, 'value': self.value}

# Wrap create_all in a try block to handle Gunicorn worker race conditions safely
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        # Ignore race condition error if another Gunicorn worker created the tables simultaneously
        pass
    
# --- FRONTEND ROUTE ---
@app.route('/')
def index():
    return render_template('index.html')

# --- SETTINGS PAGE ROUTE ---
@app.route('/settings')
def settings_page():
    return render_template('settings.html')

# --- EXPORT API ROUTE ---
@app.route('/api/export', methods=['GET'])
def export_data():
    services = Service.query.all()
    settings = Setting.query.all()

    # Structure data payload
    backup_data = {
        "version": "1.0",
        "services": [s.to_dict() for s in services],
        "settings": {s.key: s.value for s in settings}
    }

    # Convert to formatted JSON string
    json_output = json.dumps(backup_data, indent=2)

    # Return as downloadable attachment header
    return Response(
        json_output,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment;filename=dashboard_backup.json'}
    )

# --- REST API ROUTES ---
@app.route('/api/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([service.to_dict() for service in services]), 200


@app.route('/api/services/<int:service_id>', methods=['GET'])
def get_service(service_id):
    service = Service.query.get_or_404(service_id, description="Service not found")
    return jsonify(service.to_dict()), 200


@app.route('/api/services', methods=['POST'])
def create_service():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('url'):
        return jsonify({'error': 'Missing required fields'}), 400

    new_service = Service(
        name=data['name'],
        url=data['url'],
        icon=data.get('icon', 'server'),
        category=data.get('category', 'General'),
        is_online=data.get('is_online', True)
    )

    db.session.add(new_service)
    db.session.commit()
    return jsonify(new_service.to_dict()), 201


@app.route('/api/services/<int:service_id>', methods=['PUT'])
def update_service(service_id):
    service = Service.query.get_or_404(service_id)
    data = request.get_json() or {}

    service.name = data.get('name', service.name)
    service.url = data.get('url', service.url)
    service.icon = data.get('icon', service.icon)
    service.category = data.get('category', service.category)
    service.is_online = data.get('is_online', service.is_online)

    db.session.commit()
    return jsonify(service.to_dict()), 200


@app.route('/api/services/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': f'Service {service_id} deleted successfully'}), 200

# Route to auto-list all local icons inside /static/icons/
@app.route('/api/icons', methods=['GET'])
def get_local_icons():
    icons_dir = os.path.join(app.root_path, 'static', 'icons')
    
    # Create directory if it does not exist yet
    if not os.path.exists(icons_dir):
        os.makedirs(icons_dir, exist_ok=True)
        return jsonify([]), 200

    # Retrieve all PNG, SVG, JPG, and WEBP filenames
    valid_extensions = ('.png', '.svg', '.jpg', '.jpeg', '.webp')
    icon_files = [
        f for f in os.listdir(icons_dir)
        if f.lower().endswith(valid_extensions)
    ]
    
    return jsonify(sorted(icon_files)), 200

if __name__ == '__main__':
    # Explicitly bind to 0.0.0.0 so Docker can route traffic into the container
    app.run(host='0.0.0.0', port=5000, debug=False)