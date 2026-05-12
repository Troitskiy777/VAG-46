from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== МОДЕЛИ БАЗЫ ДАННЫХ ====================
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(10), default='🔧')
    is_active = db.Column(db.Boolean, default=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    car = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(20), default=datetime.now().strftime('%Y-%m-%d'))
    is_active = db.Column(db.Boolean, default=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# ==================== СОЗДАНИЕ БАЗЫ ДАННЫХ И ТЕСТОВЫХ ДАННЫХ ====================
with app.app_context():
    db.create_all()
    
    if not User.query.filter_by(username='admin').first():
        admin = User(username='VAG boss', password='Volkkoda')
        db.session.add(admin)
        db.session.commit()
        print("✅ Создан администратор: VAG boss / Volkkoda")
    
    if Service.query.count() == 0:
        services = [
            Service(title='Компьютерная диагностика', description='Полная диагностика всех систем автомобиля', price='от 2000 ₽', icon='🔍', is_active=True),
            Service(title='Техническое обслуживание', description='Замена масла, фильтров и расходных материалов', price='от 5000 ₽', icon='🔧', is_active=True),
            Service(title='Ремонт двигателя', description='Капитальный и текущий ремонт двигателей', price='от 15000 ₽', icon='⚙️', is_active=True),
            Service(title='Ремонт подвески', description='Замена амортизаторов, пружин, сайлентблоков', price='от 8000 ₽', icon='🔨', is_active=True),
            Service(title='Ремонт АКПП', description='Диагностика и ремонт автоматических коробок передач', price='от 12000 ₽', icon='🔄', is_active=True),
            Service(title='Ремонт электроники', description='Диагностика и ремонт электронных блоков', price='от 3000 ₽', icon='💡', is_active=True)
        ]
        db.session.add_all(services)
        db.session.commit()
        print("✅ Добавлены тестовые услуги")
    
    if Review.query.count() == 0:
        reviews = [
            Review(name='Иван Петров', car='Volkswagen Passat', rating=5, text='Отличный сервис! Быстро и качественно', is_active=True),
            Review(name='Сергей Иванов', car='Audi A6', rating=5, text='Профессиональный подход, рекомендую!', is_active=True),
            Review(name='Дмитрий Сидоров', car='Skoda Octavia', rating=4, text='Хороший сервис, сделали быстро', is_active=True)
        ]
        db.session.add_all(reviews)
        db.session.commit()
        print("✅ Добавлены тестовые отзывы")

# ==================== ДЕКОРАТОР ДЛЯ АДМИНКИ ====================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ==================== ГЛАВНАЯ СТРАНИЦА ====================
@app.route('/')
def index():
    services = Service.query.filter_by(is_active=True).all()
    reviews = Review.query.filter_by(is_active=True).all()
    return render_template('index.html', services=services, reviews=reviews)

# ==================== АДМИН-ПАНЕЛЬ (ВХОД И ВЫХОД) ====================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['admin_logged_in'] = True
            session['admin_user'] = username
            flash('Добро пожаловать в админ-панель!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверный логин или пароль', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_user', None)
    flash('Вы вышли из админ-панели', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    services_count = Service.query.count()
    reviews_count = Review.query.count()
    return render_template('admin/dashboard.html', 
                         services_count=services_count,
                         reviews_count=reviews_count)

# ==================== УПРАВЛЕНИЕ УСЛУГАМИ ====================
@app.route('/admin/services')
@login_required
def admin_services():
    services = Service.query.all()
    return render_template('admin/services.html', services=services)

@app.route('/admin/services/add', methods=['GET', 'POST'])
@login_required
def admin_service_add():
    if request.method == 'POST':
        service = Service(
            title=request.form['title'],
            description=request.form['description'],
            price=request.form['price'],
            icon=request.form['icon'],
            is_active='is_active' in request.form
        )
        db.session.add(service)
        db.session.commit()
        flash('Услуга успешно добавлена', 'success')
        return redirect(url_for('admin_services'))
    return render_template('admin/service_form.html', service=None)

@app.route('/admin/services/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_service_edit(id):
    service = Service.query.get_or_404(id)
    if request.method == 'POST':
        service.title = request.form['title']
        service.description = request.form['description']
        service.price = request.form['price']
        service.icon = request.form['icon']
        service.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Услуга успешно обновлена', 'success')
        return redirect(url_for('admin_services'))
    return render_template('admin/service_form.html', service=service)

@app.route('/admin/services/delete/<int:id>')
@login_required
def admin_service_delete(id):
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    flash('Услуга удалена', 'success')
    return redirect(url_for('admin_services'))

@app.route('/admin/services/toggle/<int:id>')
@login_required
def admin_service_toggle(id):
    service = Service.query.get_or_404(id)
    service.is_active = not service.is_active
    db.session.commit()
    status = 'активна' if service.is_active else 'неактивна'
    flash(f'Услуга теперь {status}', 'success')
    return redirect(url_for('admin_services'))

# ==================== УПРАВЛЕНИЕ ОТЗЫВАМИ ====================
@app.route('/admin/reviews')
@login_required
def admin_reviews():
    reviews = Review.query.all()
    return render_template('admin/reviews.html', reviews=reviews)

@app.route('/admin/reviews/add', methods=['GET', 'POST'])
@login_required
def admin_review_add():
    if request.method == 'POST':
        review = Review(
            name=request.form['name'],
            car=request.form['car'],
            rating=int(request.form['rating']),
            text=request.form['text'],
            is_active='is_active' in request.form
        )
        db.session.add(review)
        db.session.commit()
        flash('Отзыв успешно добавлен', 'success')
        return redirect(url_for('admin_reviews'))
    return render_template('admin/review_form.html', review=None)

@app.route('/admin/reviews/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_review_edit(id):
    review = Review.query.get_or_404(id)
    if request.method == 'POST':
        review.name = request.form['name']
        review.car = request.form['car']
        review.rating = int(request.form['rating'])
        review.text = request.form['text']
        review.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Отзыв успешно обновлен', 'success')
        return redirect(url_for('admin_reviews'))
    return render_template('admin/review_form.html', review=review)

@app.route('/admin/reviews/delete/<int:id>')
@login_required
def admin_review_delete(id):
    review = Review.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()
    flash('Отзыв удален', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/toggle/<int:id>')
@login_required
def admin_review_toggle(id):
    review = Review.query.get_or_404(id)
    review.is_active = not review.is_active
    db.session.commit()
    status = 'активен' if review.is_active else 'неактивен'
    flash(f'Отзыв теперь {status}', 'success')
    return redirect(url_for('admin_reviews'))

# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    app.run(debug=True)