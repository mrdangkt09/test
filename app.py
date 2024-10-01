from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from models import Product 
import os
import uuid
from models import Product 
from extensions import db  # Hoặc đường dẫn tương ứng đến mô hình Product



app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Khóa bí mật để sử dụng session
# Cấu hình SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy()
db.init_app(app)

# Tạo bảng nếu chưa tồn tại







# Định nghĩa mô hình của bạn
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200), nullable=True)



# Hàm kết nối cơ sở dữ liệu
def get_db_connection():
    conn = sqlite3.connect('store.db')
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    conn = get_db_connection()
    with conn:
        # Tạo bảng người dùng
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            uid TEXT NOT NULL UNIQUE  -- Thêm trường uid
        );''')

        conn.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            description TEXT,  -- Thêm trường mô tả sản phẩm
            FOREIGN KEY (user_id) REFERENCES users (id)
        );''')


        # Tạo bảng khách hàng
        conn.execute('''CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );''')

        # Tạo bảng hóa đơn
        conn.execute('''CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            total_price REAL NOT NULL,
            date TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );''')

        # Tạo bảng giỏ hàng
        conn.execute('''CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        );''')
    conn.close()

  




@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        uid = str(uuid.uuid4())  # Tạo UID ngẫu nhiên

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, uid) VALUES (?, ?, ?)', (username, password, uid))
            conn.commit()
            flash('Đăng ký thành công! Bạn có thể đăng nhập ngay.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Tên người dùng đã tồn tại! Vui lòng chọn tên khác.')
        finally:
            conn.close()
    
    return render_template('signup.html')

@app.route('/user_products/<uid>')
def user_products(uid):
    conn = get_db_connection()
    
    # Truy vấn thông tin người dùng
    user = conn.execute('SELECT * FROM users WHERE uid = ?', (uid,)).fetchone()
    
    if user is None:
        flash("Người dùng không tồn tại.")
        return redirect(url_for('index'))
    
    # Lấy user_id từ thông tin người dùng
    user_id = user['id']  # Hoặc user[0] nếu không sử dụng tên cột

    # Truy vấn sản phẩm của người dùng
    products = conn.execute('SELECT * FROM products WHERE user_id = ?', (user_id,)).fetchall()
    
    conn.close()

    return render_template('user_products.html', user=user, products=products)

@app.route('/user/<uid>/products', endpoint='user_products_view')
def user_products(uid):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE uid = ?', (uid,)).fetchone()
    products = conn.execute('SELECT * FROM products WHERE user_id = ?', (uid,)).fetchall()
    conn.close()
    
    return render_template('user_products.html', user=user, products=products)



@app.route('/search_user', methods=['GET'])
def search_user():
    query = request.args.get('query', '')
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users WHERE username LIKE ?', ('%' + query + '%',)).fetchall()
    conn.close()
    return render_template('user_search_results.html', users=users, query=query)


# Đăng nhập người dùng
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['username'] = user['username']
            session['user_id'] = user['id']  # Lưu user_id vào session
            flash('Đăng nhập thành công!')
            return redirect(url_for('index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!')

    return render_template('login.html')

# Đăng xuất
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)  # Xóa user_id khỏi session
    flash('Bạn đã đăng xuất thành công!')
    return redirect(url_for('index'))

# Trang chủ
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/products', methods=['GET', 'POST'])
def products():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem sản phẩm.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Nhận dữ liệu từ biểu mẫu
        product_name = request.form.get('name')
        product_category = request.form.get('category')
        product_price = request.form.get('price')
        product_quantity = request.form.get('quantity')

        # Kiểm tra các trường dữ liệu có được điền đầy đủ không
        if not product_name or not product_category or not product_price or not product_quantity:
            flash('Vui lòng điền đầy đủ thông tin sản phẩm.', 'warning')
            return redirect(url_for('products'))
        
        # Thêm sản phẩm vào cơ sở dữ liệu nếu thông tin hợp lệ
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO products (name, category, price, quantity, user_id) VALUES (?, ?, ?, ?, ?)',
                         (product_name, product_category, product_price, product_quantity, session['user_id']))
            conn.commit()
            flash('Sản phẩm đã được thêm thành công!', 'success')
        except Exception as e:
            flash(f'Có lỗi xảy ra khi thêm sản phẩm: {e}', 'danger')
        finally:
            conn.close()

    # Lấy danh sách sản phẩm từ cơ sở dữ liệu
    products = get_all_products()

    return render_template('products.html', products=products)  

    conn = get_db_connection()
    
    # Tìm kiếm sản phẩm
    search_query = request.args.get('search')
    if search_query:
        products = conn.execute('SELECT * FROM products WHERE name LIKE ? AND user_id = ?',
                                ('%' + search_query + '%', session['user_id'])).fetchall()
    else:
        products = conn.execute('SELECT * FROM products WHERE user_id = ?', (session['user_id'],)).fetchall()

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        quantity = request.form['quantity']
        conn.execute('INSERT INTO products (name, category, price, quantity, user_id) VALUES (?, ?, ?, ?, ?) ',
                     (name, category, price, quantity, session['user_id']))
        conn.commit()
        flash('Sản phẩm đã được thêm thành công!')
        return redirect(url_for('products'))

    conn.close()
    return render_template('products.html', products=products)

# Chỉnh sửa sản phẩm
@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để chỉnh sửa sản phẩm.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()

    if not product:
        flash('Sản phẩm không tồn tại hoặc không thuộc về bạn.')
        return redirect(url_for('products'))

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        quantity = request.form['quantity']
        
        # Kiểm tra các trường dữ liệu trước khi cập nhật
        if not name or not category or not price or not quantity:
            flash('Vui lòng điền đầy đủ thông tin sản phẩm.')
            return redirect(url_for('edit_product', id=id))

        conn.execute('UPDATE products SET name = ?, category = ?, price = ?, quantity = ? WHERE id = ?',
                     (name, category, price, quantity, id))
        conn.commit()
        flash('Sản phẩm đã được cập nhật thành công!')
        return redirect(url_for('products'))

    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xóa sản phẩm.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()
    
    if not product:
        flash('Không tìm thấy sản phẩm hoặc sản phẩm không thuộc về bạn.')
        return redirect(url_for('products'))

    conn.execute('DELETE FROM products WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    flash('Sản phẩm đã được xóa thành công!')
    return redirect(url_for('products'))



# Quản lý khách hàng (hiển thị và thêm khách hàng)
@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem khách hàng.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        conn.execute('INSERT INTO customers (name, phone, address, user_id) VALUES (?, ?, ?, ?)',
                     (name, phone, address, session['user_id']))
        conn.commit()
        flash('Khách hàng đã được thêm thành công!')
        return redirect(url_for('customers'))

    customers = conn.execute('SELECT * FROM customers WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('customers.html', customers=customers)

# Chỉnh sửa khách hàng
@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để chỉnh sửa khách hàng.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM customers WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()

    if not customer:
        flash('Khách hàng không tồn tại.')
        return redirect(url_for('customers'))

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        conn.execute('UPDATE customers SET name = ?, phone = ?, address = ? WHERE id = ?',
                     (name, phone, address, id))
        conn.commit()
        flash('Khách hàng đã được cập nhật thành công!')
        return redirect(url_for('customers'))

    conn.close()
    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/delete/<int:id>', methods=['POST'])
def delete_customer(id):
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xóa khách hàng.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM customers WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    flash('Khách hàng đã được xóa thành công!')
    return redirect(url_for('customers'))
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng.')
        return redirect(url_for('login'))

    quantity = request.form.get('quantity')
    if quantity is None or not quantity.isdigit() or int(quantity) <= 0:
        flash('Số lượng không hợp lệ! Vui lòng nhập số lượng lớn hơn 0.')
        return redirect(url_for('products'))

    quantity = int(quantity)
    cart = session.get('cart', {})
    
    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {'quantity': quantity}

    session['cart'] = cart
    flash('Sản phẩm đã được thêm vào giỏ hàng!')
    return redirect(url_for('products'))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', {})
    if not cart_items:
        return render_template('cart.html', cart_items=[], total_price=0)

    products = []
    total_price = 0

    for product_id, item in cart_items.items():
        try:
            product_id_int = int(product_id)  # Chuyển đổi về int
            product = Product.query.get(product_id_int)
            if product:
                quantity = item.get('quantity', 0)
                
                # Kiểm tra xem quantity có phải là int không
                if isinstance(quantity, int) and quantity >= 0:
                    products.append({
                        'name': product.name,
                        'price': product.price,
                        'quantity': quantity
                    })
                    total_price += product.price * quantity
                else:
                    print(f"Số lượng sản phẩm không hợp lệ cho ID {product_id}: {quantity}")
            else:
                print(f"Sản phẩm với ID {product_id} không tồn tại.")
        except ValueError:
            print(f"Lỗi chuyển đổi product_id: {product_id}")

    return render_template('cart.html', cart_items=products, total_price=total_price)

    session['some_value'] = some_integer_value  # should be an int
    session['another_value'] = some_string_value  # should be a str


@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    
    if product_id in cart:
        del cart[product_id]  # Xóa sản phẩm

    session['cart'] = cart
    flash('Sản phẩm đã được xóa khỏi giỏ hàng!')
    return redirect(url_for('cart'))

@app.route('/clear_session')
def clear_session():
    session.pop('cart', None)  # Xóa giỏ hàng
    flash('Giỏ hàng đã được xóa!')
    return redirect(url_for('products'))


# Xem hóa đơn
@app.route('/invoices')
def invoices():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem hóa đơn.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    invoices = conn.execute('SELECT * FROM invoices WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('invoices.html', invoices=invoices)

# Thêm hóa đơn
@app.route('/invoices/add', methods=['GET', 'POST'])
def add_invoice():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để thêm hóa đơn.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        customer_name = request.form['customer_name']
        total_price = request.form['total_price']
        date = request.form['date']
        conn = get_db_connection()
        conn.execute('INSERT INTO invoices (customer_name, total_price, date, user_id) VALUES (?, ?, ?, ?)',
                     (customer_name, total_price, date, session['user_id']))
        conn.commit()
        flash('Hóa đơn đã được thêm thành công!')
        return redirect(url_for('invoices'))

    return render_template('add_invoice.html')

# Xóa hóa đơn
@app.route('/invoices/delete/<int:id>')
def delete_invoice(id):
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xóa hóa đơn.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM invoices WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    flash('Hóa đơn đã được xóa thành công!')
    return redirect(url_for('invoices'))

# Hàm lấy tất cả sản phẩm từ cơ sở dữ liệu
def get_all_products():
    if 'user_id' not in session:
        return []  # Hoặc bạn có thể ném một lỗi hoặc redirect đến trang đăng nhập
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return products

@app.route('/store')
def store():
    products = get_all_products()  # Lấy danh sách sản phẩm từ cơ sở dữ liệu
    return render_template('store.html', products=products)

@app.route('/report')
def report():
    # Logic cho báo cáo
    return render_template('report.html')

@app.route('/upload_image/<int:id>', methods=['POST'])
def upload_image(id):
    product = Product.query.get(id)
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('Không có tệp hình ảnh nào được chọn!', 'danger')
            return redirect(url_for('product_management'))

        file = request.files['image']
        if file.filename == '':
            flash('Không có tệp nào được chọn!', 'danger')
            return redirect(url_for('product_management'))

        if file and allowed_file(file.filename):
            filename = f"{product.id}.jpg"  # Đặt tên tệp theo ID sản phẩm
            file.save(os.path.join(app.static_folder, 'images', filename))  # Lưu vào thư mục images
            flash('Hình ảnh đã được cập nhật!', 'success')
        else:
            flash('Định dạng tệp không hợp lệ! Chỉ cho phép hình ảnh JPEG.', 'danger')
    
    return redirect(url_for('product_management'))
    




@app.route('/search_store', methods=['GET'])
def search_store():
    query = request.args.get('query', '')
    print(f'Search query: {query}')  # In ra truy vấn để kiểm tra
    # Tìm kiếm trong cơ sở dữ liệu để lấy danh sách cửa hàng dựa trên truy vấn
    stores = Store.query.filter(Store.name.contains(query)).all()
    return render_template('store_search_results.html', stores=stores, query=query)


@app.route('/store_products/<int:store_id>', methods=['GET'])
def store_products(store_id):
    products = Product.query.filter(Product.store_id == store_id).all()  # Giả sử bạn có mô hình Product
    return render_template('store_products.html', products=products)








if __name__ == '__main__':
    if not os.path.exists('store.db'):
        with app.app_context():
            initialize_db() # Chỉ khởi tạo cơ sở dữ liệu nếu nó chưa tồn tại
            db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)