import os
import uuid
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from recommendation_engine import RecommendationEngine, load_products, get_product_by_id, update_product_stock

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'se-lab-ai-shopping-system-secret-key-2026')

engine = RecommendationEngine()

# In-memory store for orders during server session (matching lab requirement: no database)
ORDERS_STORE = []

@app.before_request
def init_cart():
    if 'cart' not in session:
        session['cart'] = {} # {str(product_id): quantity}

@app.context_processor
def inject_cart_count():
    cart = session.get('cart', {})
    total_qty = sum(cart.values())
    return dict(cart_count=total_qty)

@app.route('/')
def index():
    products = load_products()
    # Select a few diverse featured products
    featured = [p for p in products if p['id'] in [1, 4, 11, 15, 23, 28, 31, 39, 42, 47]]
    categories = [
        {'name': 'Headphones and Earbuds', 'icon': '🎧'},
        {'name': 'Smartphones', 'icon': '📱'},
        {'name': 'Laptops', 'icon': '💻'},
        {'name': 'Smartwatches', 'icon': '⌚'},
        {'name': 'Speakers', 'icon': '🔊'},
        {'name': 'Keyboards and Mice', 'icon': '⌨️'},
        {'name': 'Monitors', 'icon': '🖥️'}
    ]
    return render_template('index.html', featured=featured, categories=categories)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('index'))

    data = engine.recommend(query)
    return render_template('recommendations.html',
                           query=data['query'],
                           constraints=data['constraints'],
                           results=data['results'],
                           total_matches=data['total_matches'])

@app.route('/category/<cat_name>')
def category_view(cat_name):
    products = load_products()
    matched = [p for p in products if p['category'].lower() == cat_name.lower()]
    return render_template('recommendations.html',
                           query=f"Category: {cat_name}",
                           constraints={'category': cat_name, 'max_price': None, 'preferences': {}},
                           results=matched,
                           total_matches=len(matched))

@app.route('/compare')
def compare():
    ids_param = request.args.get('ids', '')
    product_ids = [int(i) for i in ids_param.split(',') if i.strip().isdigit()]
    products = [get_product_by_id(pid) for pid in product_ids]
    products = [p for p in products if p is not None]

    # Collect all unique specification keys across selected products
    all_spec_keys = []
    for p in products:
        for k in p.get('specifications', {}).keys():
            if k not in all_spec_keys:
                all_spec_keys.append(k)

    return render_template('compare.html', products=products, spec_keys=all_spec_keys)

@app.route('/cart')
def cart():
    cart_dict = session.get('cart', {})
    cart_items = []
    subtotal = 0

    for pid_str, qty in cart_dict.items():
        p = get_product_by_id(int(pid_str))
        if p:
            item_total = p['price'] * qty
            subtotal += item_total
            cart_items.append({
                'product': p,
                'quantity': qty,
                'item_total': item_total,
                'max_stock': p.get('stock', 0)
            })

    return render_template('cart.html', items=cart_items, subtotal=subtotal)

@app.route('/cart/add/<int:product_id>', methods=['POST', 'GET'])
def add_to_cart(product_id):
    p = get_product_by_id(product_id)
    if not p:
        flash("Product not found.", "error")
        return redirect(url_for('index'))

    cart = session.get('cart', {})
    pid_str = str(product_id)
    current_qty = cart.get(pid_str, 0)
    stock = p.get('stock', 0)

    if current_qty + 1 > stock:
        flash(f"Cannot add more units. Only {stock} available in stock.", "warning")
    else:
        cart[pid_str] = current_qty + 1
        session['cart'] = cart
        session.modified = True
        flash(f"Added {p['name']} to cart!", "success")

    # If ajax request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok', 'cart_count': sum(session['cart'].values())})

    return redirect(request.referrer or url_for('cart'))

@app.route('/cart/update', methods=['POST'])
def update_cart():
    product_id = request.form.get('product_id')
    try:
        qty = int(request.form.get('quantity', 1))
    except ValueError:
        qty = 1

    p = get_product_by_id(product_id)
    if p:
        cart = session.get('cart', {})
        pid_str = str(product_id)
        if qty <= 0:
            cart.pop(pid_str, None)
        else:
            stock = p.get('stock', 0)
            cart[pid_str] = min(qty, stock)
        session['cart'] = cart
        session.modified = True

    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    session.modified = True
    flash("Item removed from cart.", "info")
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_dict = session.get('cart', {})
    if not cart_dict:
        flash("Your cart is empty.", "info")
        return redirect(url_for('index'))

    cart_items = []
    total_amount = 0
    for pid_str, qty in cart_dict.items():
        p = get_product_by_id(int(pid_str))
        if p:
            cost = p['price'] * qty
            total_amount += cost
            cart_items.append({'product': p, 'quantity': qty, 'item_total': cost})

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        payment_method = request.form.get('payment_method', 'UPI')

        if not name or not email or not address:
            flash("Please fill in all required customer details.", "error")
            return render_template('checkout.html', items=cart_items, total=total_amount)

        # Generate unique Order ID
        order_id = "ORD-" + uuid.uuid4().hex[:8].upper()
        order_date = datetime.datetime.now().strftime("%d-%b-%Y, %I:%M %p")

        order_record = {
            'order_id': order_id,
            'date': order_date,
            'customer': {'name': name, 'email': email, 'address': address},
            'items': cart_items,
            'total_amount': total_amount,
            'payment_method': payment_method,
            'status': 'Confirmed' # Initial state from state chart
        }

        # Deduct stock in memory
        for item in cart_items:
            update_product_stock(item['product']['id'], item['quantity'])

        # Store order
        ORDERS_STORE.insert(0, order_record)

        # Clear cart
        session['cart'] = {}
        session.modified = True

        return redirect(url_for('confirmation', order_id=order_id))

    return render_template('checkout.html', items=cart_items, total=total_amount)

@app.route('/confirmation/<order_id>')
def confirmation(order_id):
    order = next((o for o in ORDERS_STORE if o['order_id'] == order_id), None)
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for('index'))
    return render_template('confirmation.html', order=order)

@app.route('/orders')
def orders():
    return render_template('orders.html', orders=ORDERS_STORE)

if __name__ == '__main__':
    print("Starting AI Shopping System on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=True)

