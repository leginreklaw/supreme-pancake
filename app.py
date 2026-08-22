import os
from flask import Flask, request, jsonify, render_template
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


# --- FRONTEND ROUTE ---
@app.route('/')
def index():
    return render_template('index.html')


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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Explicitly bind to 0.0.0.0 so Docker can route traffic into the container
    app.run(host='0.0.0.0', port=5000, debug=False)