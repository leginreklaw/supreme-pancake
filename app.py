import os
import json
from flask import Flask, request, jsonify, render_template, Response
from flask_sqlalchemy import SQLAlchemy

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


with app.app_context():
    try:
        db.create_all()
    except Exception:
        pass


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/settings')
def settings_page():
    return render_template('settings.html')


@app.route('/api/export', methods=['GET'])
def export_data():
    services = Service.query.all()
    settings = Setting.query.all()

    backup_data = {
        "version": "1.0",
        "services": [s.to_dict() for s in services],
        "settings": {s.key: s.value for s in settings}
    }

    json_output = json.dumps(backup_data, indent=2)
    return Response(
        json_output,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment;filename=dashboard_backup.json'}
    )


@app.route('/api/import', methods=['POST'])
def import_data():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    try:
        data = json.load(file)
        if 'services' in data:
            Service.query.delete()
            for s in data['services']:
                db.session.add(Service(
                    name=s['name'],
                    url=s['url'],
                    icon=s.get('icon', 'server'),
                    category=s.get('category', 'General'),
                    is_online=s.get('is_online', True)
                ))
            db.session.commit()
        return jsonify({'message': 'Import successfully completed'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([service.to_dict() for service in services]), 200


@app.route('/api/services/<int:service_id>', methods=['GET'])
def get_service(service_id):
    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({'error': 'Service not found'}), 404
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
    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({'error': 'Service not found'}), 404
        
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
    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({'error': 'Service not found'}), 404
        
    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': f'Service {service_id} deleted successfully'}), 200


@app.route('/api/icons', methods=['GET'])
def get_local_icons():
    icons_dir = os.path.join(app.root_path, 'static', 'icons')
    if not os.path.exists(icons_dir):
        os.makedirs(icons_dir, exist_ok=True)
        return jsonify([]), 200

    valid_extensions = ('.png', '.svg', '.jpg', '.jpeg', '.webp')
    icon_files = [f for f in os.listdir(icons_dir) if f.lower().endswith(valid_extensions)]
    return jsonify(sorted(icon_files)), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)