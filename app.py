import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)

# Configure SQLite database file stored in instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dashboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize ORM extension
db = SQLAlchemy(app)


# Define Database Model
class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(100), nullable=True, default='server')
    category = db.Column(db.String(50), nullable=False, default='General')
    is_online = db.Column(db.Boolean, default=True)

    def to_dict(self):
        """Convert database record to a dictionary for API JSON responses."""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'icon': self.icon,
            'category': self.category,
            'is_online': self.is_online
        }


# Quick test route
@app.route('/')
def home():
    return {"message": "Homelab Dashboard API is running"}


if __name__ == '__main__':
    # Automatically create database tables inside app context if they don't exist
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

    app.run(debug=True, port=5000)