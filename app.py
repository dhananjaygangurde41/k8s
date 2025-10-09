from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import redis, json, os

app = Flask(__name__)

# SQLite DB inside pod
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Redis host comes from environment variable
redis_host = os.getenv('REDIS_HOST', 'redis-service')
r = redis.Redis(host=redis_host, port=6379, db=0)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/users')
def get_users():
    cache_key = "users_data"
    cached_data = r.get(cache_key)

    if cached_data:
        users = json.loads(cached_data)
        cache_status = "Cache Hit"
    else:
        users = [{"id": u.id, "name": u.name, "email": u.email} for u in User.query.all()]
        r.set(cache_key, json.dumps(users), ex=60)
        cache_status = "Cache Miss"

    return render_template('users.html', users=users, cache_status=cache_status)

@app.route('/add', methods=['POST'])
def add_user():
    name = request.form['name']
    email = request.form['email']
    new_user = User(name=name, email=email)
    db.session.add(new_user)
    db.session.commit()
    r.delete("users_data")
    return "User added! <a href='/users'>View Users</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
