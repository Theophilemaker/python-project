import os
from datetime import datetime, date, timedelta
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Permission, Branch, Category, Product, Sale, TaxTransaction
from models import CashSession, CashTransaction, Expense, Supplier, PurchaseOrder, POItem
from models import StockTransfer, TransferItem, TransferHistory, Employee, Attendance, Payroll
from models import CompanySetting, AuditLog
from forms import *
from decorators import admin_required, permission_required
from utils import *

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# =====================================================
# USER LOADER
# =====================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =====================================================
# CONTEXT PROCESSORS
# =====================================================

@app.context_processor
def inject_company_settings():
    """Inject company settings into all templates"""
    settings = {}
    company_settings = CompanySetting.query.all()
    for setting in company_settings:
        settings[setting.setting_key] = setting.setting_value
    
    defaults = {
        'company_name': Config.COMPANY_NAME,
        'company_tagline': Config.COMPANY_TAGLINE,
        'company_address': Config.COMPANY_ADDRESS,
        'company_phone': Config.COMPANY_PHONE,
        'company_email': Config.COMPANY_EMAIL,
        'company_website': Config.COMPANY_WEBSITE
    }
    
    for key, value in defaults.items():
        if key not in settings:
            settings[key] = value
    
    return {'company': settings}

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def get_branch_filter():
    """Get branch filter for queries based on user role"""
    if current_user.role == 'admin':
        return None
    return current_user.branch_id

def log_action(action, details=''):
    """Log user action"""
    if current_user.is_authenticated:
        log_audit(db, current_user.id, action, details)

# =====================================================
# AUTHENTICATION ROUTES
# =====================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=True)
            user.last_login = datetime.now()
            db.session.commit()
            
            log_action('login', f'User {user.username} logged in')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    log_action('logout', f'User {current_user.username} logged out')
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

# =====================================================
# DASHBOARD
# =====================================================

@app.route('/')
@app.route('/index')
@login_required
def index():
    branch_filter = get_branch_filter()
    
    # Statistics
    query = Product.query
    if branch_filter:
        query = query.filter_by(branch_id=branch_filter)
    
    total_products = query.count()
    low_stock = query.filter(Product.quantity < 5).count()
    expiring = query.filter(Product.expiry_date <= date.today() + timedelta(days=7)).count()
    
    # Today's sales
    sales_query = Sale.query.filter_by(sale_date=date.today())
    if branch_filter:
        sales_query = sales_query.filter_by(branch_id=branch_filter)
    if current_user.role == 'cashier':
        sales_query = sales_query.filter_by(cashier_id=current_user.id)
    
    today_sales = sales_query.with_entities(db.func.sum(Sale.total_price)).scalar() or 0
    
    # Low stock items
    low_stock_items = Product.query.filter(Product.quantity < 5).limit(5).all()
    
    # Expiring items
    expiring_items = Product.query.filter(
        Product.expiry_date <= date.today() + timedelta(days=7)
    ).limit(5).all()
    
    # Recent sales
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()
    
    # Products for dropdown
    products = Product.query.filter(Product.quantity > 0).all()
    
    return render_template('index.html',
                         total_products=total_products,
                         low_stock=low_stock,
                         expiring=expiring,
                         today_sales=today_sales,
                         low_stock_items=low_stock_items,
                         expiring_items=expiring_items,
                         recent_sales=recent_sales,
                         products=products)

# =====================================================
# PRODUCT MANAGEMENT
# =====================================================

@app.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    form = ProductForm()
    
    # Populate category choices
    categories = Category.query.filter_by(is_active=True).all()
    form.category_id.choices = [(0, 'Select Category')] + [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit() and current_user.role == 'admin':
        product = Product(
            name=form.name.data,
            category_id=form.category_id.data,
            buying_price=form.buying_price.data,
            selling_price=form.selling_price.data,
            quantity=form.quantity.data,
            expiry_date=form.expiry_date.data,
            tax_rate=form.tax_rate.data,
            reorder_level=form.reorder_level.data,
            sku=form.sku.data or generate_sku(),
            barcode=form.barcode.data,
            branch_id=current_user.branch_id or 1
        )
        db.session.add(product)
        db.session.commit()
        log_action('create_product', f'Created product: {product.name}')
        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))
    
    # Handle edit
    edit_id = request.args.get('edit', type=int)
    edit_product = None
    if edit_id and current_user.role == 'admin':
        edit_product = Product.query.get_or_404(edit_id)
        if request.method == 'GET':
            form.name.data = edit_product.name
            form.category_id.data = edit_product.category_id
            form.buying_price.data = edit_product.buying_price
            form.selling_price.data = edit_product.selling_price
            form.quantity.data = edit_product.quantity
            form.expiry_date.data = edit_product.expiry_date
            form.tax_rate.data = edit_product.tax_rate
            form.reorder_level.data = edit_product.reorder_level
            form.sku.data = edit_product.sku
            form.barcode.data = edit_product.barcode
    
    # Handle delete
    delete_id = request.args.get('delete', type=int)
    if delete_id and current_user.role == 'admin':
        product = Product.query.get_or_404(delete_id)
        # Check if product has sales
        if product.sales.count() > 0:
            flash('Cannot delete product with sales history!', 'error')
        else:
            db.session.delete(product)
            db.session.commit()
            log_action('delete_product', f'Deleted product: {product.name}')
            flash('Product deleted successfully!', 'success')
        return redirect(url_for('products'))
    
    # Get all products
    branch_filter = get_branch_filter()
    query = Product.query
    if branch_filter:
        query = query.filter_by(branch_id=branch_filter)
    products = query.order_by(Product.created_at.desc()).all()
    
    return render_template('products.html',
                         form=form,
                         products=products,
                         edit_product=edit_product,
                         categories=categories)

@app.route('/process_sale', methods=['POST'])
@login_required
def process_sale():
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int)
    
    product = Product.query.get_or_404(product_id)
    
    if product.quantity < quantity:
        flash(f'Insufficient stock! Only {product.quantity} available.', 'error')
        return redirect(url_for('index'))
    
    # Calculate profit and tax
    cost_price = product.buying_price
    selling_price = product.selling_price
    subtotal = selling_price * quantity
    profit_per_unit = selling_price - cost_price
    total_profit = profit_per_unit * quantity
    
    # Tax is 18% of profit
    tax_rate = 18.00
    tax_amount = total_profit * (tax_rate / 100)
    total_with_tax = subtotal + tax_amount
    
    # Start transaction
    try:
        # Create sale
        sale = Sale(
            product_id=product.id,
            cashier_id=current_user.id,
            branch_id=current_user.branch_id or 1,
            quantity=quantity,
            total_price=total_with_tax,
            sale_date=date.today()
        )
        db.session.add(sale)
        db.session.flush()
        
        # Create tax transaction
        tax_trans = TaxTransaction(
            sale_id=sale.id,
            product_id=product.id,
            cost_price=cost_price,
            selling_price=selling_price,
            quantity=quantity,
            profit=total_profit,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_with_tax=total_with_tax
        )
        db.session.add(tax_trans)
        
        # Update stock
        product.quantity -= quantity
        
        db.session.commit()
        
        flash(f'Sale completed! Total: {format_currency(total_with_tax)} (Tax: {format_currency(tax_amount)})', 'success')
        log_action('sale', f'Sold {quantity} x {product.name}')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing sale: {str(e)}', 'error')
    
    return redirect(url_for('index'))

# =====================================================
# BRANCH MANAGEMENT
# =====================================================

@app.route('/branches', methods=['GET', 'POST'])
@login_required
@admin_required
def branches():
    form = BranchForm()
    
    if form.validate_on_submit():
        if 'add_branch' in request.form:
            branch = Branch(
                branch_code=form.branch_code.data.upper(),
                branch_name=form.branch_name.data,
                location=form.location.data,
                phone=form.phone.data,
                email=form.email.data,
                manager=form.manager.data,
                address=form.address.data,
                tax_id=form.tax_id.data,
                is_active=form.is_active.data
            )
            db.session.add(branch)
            db.session.commit()
            log_action('create_branch', f'Created branch: {branch.branch_name}')
            flash('Branch added successfully!', 'success')
        elif 'edit_branch' in request.form:
            branch_id = request.form.get('branch_id', type=int)
            branch = Branch.query.get_or_404(branch_id)
            branch.branch_name = form.branch_name.data
            branch.location = form.location.data
            branch.phone = form.phone.data
            branch.email = form.email.data
            branch.manager = form.manager.data
            branch.address = form.address.data
            branch.tax_id = form.tax_id.data
            branch.is_active = form.is_active.data
            db.session.commit()
            log_action('update_branch', f'Updated branch: {branch.branch_name}')
            flash('Branch updated successfully!', 'success')
        
        return redirect(url_for('branches'))
    
    # Handle delete
    delete_id = request.args.get('delete', type=int)
    if delete_id:
        branch = Branch.query.get_or_404(delete_id)
        # Check if branch has products
        if branch.products.count() > 0:
            flash('Cannot delete branch with products!', 'error')
        else:
            db.session.delete(branch)
            db.session.commit()
            log_action('delete_branch', f'Deleted branch: {branch.branch_name}')
            flash('Branch deleted successfully!', 'success')
        return redirect(url_for('branches'))
    
    # Get edit branch
    edit_id = request.args.get('edit', type=int)
    edit_branch = None
    if edit_id:
        edit_branch = Branch.query.get_or_404(edit_id)
        if request.method == 'GET':
            form.branch_code.data = edit_branch.branch_code
            form.branch_name.data = edit_branch.branch_name
            form.location.data = edit_branch.location
            form.phone.data = edit_branch.phone
            form.email.data = edit_branch.email
            form.manager.data = edit_branch.manager
            form.address.data = edit_branch.address
            form.tax_id.data = edit_branch.tax_id
            form.is_active.data = edit_branch.is_active
    
    # Get all branches
    branches = Branch.query.order_by(Branch.id).all()
    
    return render_template('branches.html',
                         form=form,
                         branches=branches,
                         edit_branch=edit_branch)

# =====================================================
# SUPPLIER MANAGEMENT
# =====================================================

@app.route('/suppliers', methods=['GET', 'POST'])
@login_required
@admin_required
def suppliers():
    form = SupplierForm()
    
    if form.validate_on_submit() and 'add_supplier' in request.form:
        supplier_code = 'SUP' + str(random.randint(1000, 9999))
        supplier = Supplier(
            supplier_code=supplier_code,
            company_name=form.company_name.data,
            contact_person=form.contact_person.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            tax_id=form.tax_id.data,
            payment_terms=form.payment_terms.data,
            lead_time_days=form.lead_time_days.data
        )
        db.session.add(supplier)
        db.session.commit()
        log_action('create_supplier', f'Created supplier: {supplier.company_name}')
        flash('Supplier added successfully!', 'success')
        return redirect(url_for('suppliers'))
    
    # Get all suppliers
    suppliers = Supplier.query.order_by(Supplier.company_name).all()
    
    return render_template('suppliers.html', form=form, suppliers=suppliers)

# =====================================================
# CASH MANAGEMENT
# =====================================================

@app.route('/cash_dashboard', methods=['GET', 'POST'])
@login_required
def cash_dashboard():
    # Check for open session
    open_session = CashSession.query.filter_by(
        user_id=current_user.id,
        status='open'
    ).first()
    
    # Get today's sales and expenses
    today_sales = Sale.query.filter_by(
        cashier_id=current_user.id,
        sale_date=date.today()
    ).with_entities(db.func.sum(Sale.total_price)).scalar() or 0
    
    today_expenses = Expense.query.filter_by(
        created_by=current_user.id,
        expense_date=date.today()
    ).with_entities(db.func.sum(Expense.amount)).scalar() or 0
    
    # Handle open session
    if request.method == 'POST' and 'open_session' in request.form:
        if open_session:
            flash('You already have an open session!', 'error')
        else:
            session = CashSession(
                user_id=current_user.id,
                branch_id=current_user.branch_id or 1,
                opening_balance=float(request.form['opening_balance']),
                status='open'
            )
            db.session.add(session)
            db.session.commit()
            log_action('open_session', f'Opened cash session')
            flash(f'Session opened with balance {format_currency(session.opening_balance)}', 'success')
        return redirect(url_for('cash_dashboard'))
    
    # Handle close session
    if request.method == 'POST' and 'close_session' in request.form and open_session:
        closing_balance = float(request.form['closing_balance'])
        expected = float(open_session.opening_balance) + today_sales - today_expenses
        difference = closing_balance - expected
        
        open_session.closing_balance = closing_balance
        open_session.expected_balance = expected
        open_session.difference = difference
        open_session.closing_date = date.today()
        open_session.closing_time = datetime.now().time()
        open_session.status = 'closed'
        
        db.session.commit()
        log_action('close_session', f'Closed cash session, difference: {difference}')
        flash(f'Session closed. Difference: {format_currency(difference)}', 'success')
        return redirect(url_for('cash_dashboard'))
    
    # Handle expense
    if request.method == 'POST' and 'add_expense' in request.form:
        expense = Expense(
            expense_number=generate_expense_number(),
            expense_date=date.today(),
            category=request.form['category'],
            amount=float(request.form['amount']),
            description=request.form['description'],
            paid_to=request.form['paid_to'],
            created_by=current_user.id,
            branch_id=current_user.branch_id or 1
        )
        db.session.add(expense)
        db.session.commit()
        log_action('add_expense', f'Added expense: {format_currency(expense.amount)}')
        flash('Expense recorded successfully!', 'success')
        return redirect(url_for('cash_dashboard'))
    
    # Get recent sessions
    recent_sessions = CashSession.query.filter(
        (CashSession.user_id == current_user.id) | (CashSession.branch_id == current_user.branch_id)
    ).order_by(CashSession.created_at.desc()).limit(10).all()
    
    # Get expense categories
    expense_categories = [
        'Utilities', 'Rent', 'Salaries', 'Supplies', 
        'Maintenance', 'Transport', 'Marketing', 'Taxes', 'Miscellaneous'
    ]
    
    return render_template('cash_dashboard.html',
                         open_session=open_session,
                         today_sales=today_sales,
                         today_expenses=today_expenses,
                         recent_sessions=recent_sessions,
                         expense_categories=expense_categories)

# =====================================================
# REPORTS
# =====================================================

@app.route('/reports', methods=['GET'])
@login_required
@admin_required
def reports():
    start_date = request.args.get('start_date', (date.today().replace(day=1)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', date.today().strftime('%Y-%m-%d'))
    branch_id = request.args.get('branch_id', 'all')
    
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Build query
    query = Sale.query.filter(Sale.sale_date.between(start, end))
    
    if branch_id != 'all':
        query = query.filter_by(branch_id=int(branch_id))
    
    # Summary
    total_sales = query.with_entities(db.func.sum(Sale.total_price)).scalar() or 0
    total_transactions = query.count()
    avg_sale = total_sales / total_transactions if total_transactions > 0 else 0
    
    # Payment method breakdown
    cash_sales = query.filter_by(payment_method='cash').with_entities(db.func.sum(Sale.total_price)).scalar() or 0
    card_sales = query.filter_by(payment_method='card').with_entities(db.func.sum(Sale.total_price)).scalar() or 0
    mobile_sales = query.filter_by(payment_method='mobile').with_entities(db.func.sum(Sale.total_price)).scalar() or 0
    
    # Daily sales
    daily_sales = db.session.query(
        db.func.date(Sale.sale_date).label('date'),
        db.func.count(Sale.id).label('transactions'),
        db.func.sum(Sale.total_price).label('total')
    ).filter(Sale.sale_date.between(start, end)).group_by(db.func.date(Sale.sale_date)).order_by('date').all()
    
    # Top products
    top_products = db.session.query(
        Product.name,
        db.func.count(Sale.id).label('times_sold'),
        db.func.sum(Sale.quantity).label('total_quantity'),
        db.func.sum(Sale.total_price).label('revenue')
    ).join(Sale).filter(Sale.sale_date.between(start, end)).group_by(Product.id).order_by(db.desc('revenue')).limit(10).all()
    
    # Cashier performance
    cashiers = db.session.query(
        User.full_name,
        User.role,
        db.func.count(Sale.id).label('transactions'),
        db.func.sum(Sale.total_price).label('total_sales'),
        db.func.avg(Sale.total_price).label('avg_sale')
    ).join(Sale).filter(Sale.sale_date.between(start, end)).group_by(User.id).order_by(db.desc('total_sales')).all()
    
    # Sales details
    sales = Sale.query.filter(Sale.sale_date.between(start, end)).order_by(Sale.sale_date.desc()).limit(100).all()
    
    # Branches for filter
    branches = Branch.query.filter_by(is_active=True).all()
    
    summary = {
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'average_sale': avg_sale,
        'cash_sales': cash_sales,
        'card_sales': card_sales,
        'mobile_sales': mobile_sales,
        'active_cashiers': len(set(s.cashier_id for s in sales))
    }
    
    return render_template('reports.html',
                         summary=summary,
                         daily_sales=daily_sales,
                         top_products=top_products,
                         cashiers=cashiers,
                         sales=sales,
                         start_date=start,
                         end_date=end,
                         branch_id=branch_id,
                         branches=branches)

@app.route('/sales_report_pdf')
@login_required
@admin_required
def sales_report_pdf():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    branch_id = request.args.get('branch_id', 'all')
    
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get data
    query = Sale.query.filter(Sale.sale_date.between(start, end))
    if branch_id != 'all':
        query = query.filter_by(branch_id=int(branch_id))
    
    total_sales = query.with_entities(db.func.sum(Sale.total_price)).scalar() or 0
    total_transactions = query.count()
    avg_sale = total_sales / total_transactions if total_transactions > 0 else 0
    
    daily_sales = db.session.query(
        db.func.date(Sale.sale_date).label('date'),
        db.func.count(Sale.id).label('transactions'),
        db.func.sum(Sale.total_price).label('total')
    ).filter(Sale.sale_date.between(start, end)).group_by(db.func.date(Sale.sale_date)).order_by('date').all()
    
    data = {
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'average_sale': avg_sale,
        'active_cashiers': len(set(s.cashier_id for s in query.all())),
        'daily_sales': daily_sales
    }
    
    # Get company info
    company_info = {
        'name': CompanySetting.query.filter_by(setting_key='company_name').first().setting_value if CompanySetting.query.filter_by(setting_key='company_name').first() else Config.COMPANY_NAME
    }
    
    pdf_buffer = generate_sales_report_pdf(data, start, end, company_info)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f'sales_report_{start_date}_to_{end_date}.pdf',
        mimetype='application/pdf'
    )

# =====================================================
# TAX REPORTS
# =====================================================

@app.route('/tax_reports', methods=['GET'])
@login_required
@admin_required
def tax_reports():
    month = request.args.get('month', date.today().strftime('%Y-%m'))
    branch_id = request.args.get('branch_id', 'all')
    
    year, month_num = map(int, month.split('-'))
    
    # Build query
    query = TaxTransaction.query.join(Sale).filter(
        db.extract('year', Sale.sale_date) == year,
        db.extract('month', Sale.sale_date) == month_num
    )
    
    if branch_id != 'all':
        query = query.filter(Sale.branch_id == int(branch_id))
    
    # Summary
    total_subtotal = query.with_entities(db.func.sum(TaxTransaction.subtotal)).scalar() or 0
    total_tax = query.with_entities(db.func.sum(TaxTransaction.tax_amount)).scalar() or 0
    total_profit = query.with_entities(db.func.sum(TaxTransaction.profit)).scalar() or 0
    total_transactions = query.count()
    avg_rate = query.with_entities(db.func.avg(TaxTransaction.tax_rate)).scalar() or 0
    
    # Daily breakdown
    daily = db.session.query(
        db.func.date(Sale.sale_date).label('date'),
        db.func.count().label('transactions'),
        db.func.sum(TaxTransaction.subtotal).label('subtotal'),
        db.func.sum(TaxTransaction.tax_amount).label('tax')
    ).join(TaxTransaction).filter(
        db.extract('year', Sale.sale_date) == year,
        db.extract('month', Sale.sale_date) == month_num
    ).group_by(db.func.date(Sale.sale_date)).order_by('date').all()
    
    # Category breakdown
    categories = db.session.query(
        Category.name.label('category'),
        db.func.count().label('items'),
        db.func.sum(TaxTransaction.subtotal).label('subtotal'),
        db.func.sum(TaxTransaction.tax_amount).label('tax')
    ).join(Product).join(TaxTransaction).join(Sale).filter(
        db.extract('year', Sale.sale_date) == year,
        db.extract('month', Sale.sale_date) == month_num
    ).group_by(Category.id).order_by(db.desc('tax')).all()
    
    # Transaction details
    details = TaxTransaction.query.join(Sale).join(Product).filter(
        db.extract('year', Sale.sale_date) == year,
        db.extract('month', Sale.sale_date) == month_num
    ).order_by(Sale.sale_date.desc()).all()
    
    # Branches for filter
    branches = Branch.query.filter_by(is_active=True).all()
    
    summary = {
        'total_subtotal': total_subtotal,
        'total_tax': total_tax,
        'total_profit': total_profit,
        'total_transactions': total_transactions,
        'avg_rate': avg_rate
    }
    
    return render_template('tax_reports.html',
                         summary=summary,
                         daily=daily,
                         categories=categories,
                         details=details,
                         month=month,
                         branch_id=branch_id,
                         branches=branches)

# =====================================================
# PROFILE & COMPANY SETTINGS
# =====================================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    password_form = ChangePasswordForm()
    
    if form.validate_on_submit() and 'update_profile' in request.form:
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        db.session.commit()
        log_action('update_profile', 'Updated profile information')
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    if password_form.validate_on_submit() and 'change_password' in request.form:
        if current_user.check_password(password_form.current_password.data):
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            log_action('change_password', 'Changed password')
            flash('Password changed successfully!', 'success')
        else:
            flash('Current password is incorrect!', 'error')
        return redirect(url_for('profile'))
    
    # Get recent activity
    recent_activity = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.created_at.desc()).limit(10).all()
    
    return render_template('profile.html',
                         form=form,
                         password_form=password_form,
                         recent_activity=recent_activity)

@app.route('/company_settings', methods=['GET', 'POST'])
@login_required
@admin_required
def company_settings():
    form = CompanySettingsForm()
    
    # Load current settings
    settings = {}
    company_settings = CompanySetting.query.all()
    for setting in company_settings:
        settings[setting.setting_key] = setting.setting_value
    
    if form.validate_on_submit() and 'save_settings' in request.form:
        # Handle logo upload
        if form.logo.data:
            file = form.logo.data
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"logo_{int(datetime.now().timestamp())}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'logos', new_filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            
            setting = CompanySetting.query.filter_by(setting_key='logo').first()
            if setting:
                setting.setting_value = filepath
                setting.updated_by = current_user.id
            else:
                setting = CompanySetting(
                    setting_key='logo',
                    setting_value=filepath,
                    setting_type='image',
                    updated_by=current_user.id
                )
                db.session.add(setting)
        
        # Handle favicon upload
        if form.favicon.data:
            file = form.favicon.data
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"favicon_{int(datetime.now().timestamp())}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'logos', new_filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            
            setting = CompanySetting.query.filter_by(setting_key='favicon').first()
            if setting:
                setting.setting_value = filepath
                setting.updated_by = current_user.id
            else:
                setting = CompanySetting(
                    setting_key='favicon',
                    setting_value=filepath,
                    setting_type='image',
                    updated_by=current_user.id
                )
                db.session.add(setting)
        
        # Save text settings
        text_settings = {
            'company_name': form.company_name.data,
            'tagline': form.tagline.data,
            'address': form.address.data,
            'phone': form.phone.data,
            'email': form.email.data,
            'website': form.website.data,
            'tax_number': form.tax_number.data,
            'footer_text': form.footer_text.data
        }
        
        for key, value in text_settings.items():
            setting = CompanySetting.query.filter_by(setting_key=key).first()
            if setting:
                setting.setting_value = value
                setting.updated_by = current_user.id
            else:
                setting = CompanySetting(
                    setting_key=key,
                    setting_value=value,
                    updated_by=current_user.id
                )
                db.session.add(setting)
        
        db.session.commit()
        log_action('update_company_settings', 'Updated company settings')
        flash('Company settings saved successfully!', 'success')
        return redirect(url_for('company_settings'))
    
    # Pre-populate form
    if request.method == 'GET':
        form.company_name.data = settings.get('company_name', Config.COMPANY_NAME)
        form.tagline.data = settings.get('tagline', Config.COMPANY_TAGLINE)
        form.address.data = settings.get('address', Config.COMPANY_ADDRESS)
        form.phone.data = settings.get('phone', Config.COMPANY_PHONE)
        form.email.data = settings.get('email', Config.COMPANY_EMAIL)
        form.website.data = settings.get('website', Config.COMPANY_WEBSITE)
        form.tax_number.data = settings.get('tax_number', Config.COMPANY_TAX_NUMBER)
        form.footer_text.data = settings.get('footer_text', 'Thank you for your business!')
    
    return render_template('company_settings.html',
                         form=form,
                         settings=settings)

# =====================================================
# PERMISSIONS MANAGEMENT
# =====================================================

@app.route('/permissions', methods=['GET', 'POST'])
@login_required
@admin_required
def permissions():
    if request.method == 'POST' and 'grant_permission' in request.form:
        user_id = request.form.get('user_id', type=int)
        permission_id = request.form.get('permission_id', type=int)
        expires_at = request.form.get('expires_at')
        
        user = User.query.get(user_id)
        permission = Permission.query.get(permission_id)
        
        if user and permission:
            # Check if already has permission
            if permission in user.permissions:
                flash('Permission already granted!', 'error')
            else:
                user.permissions.append(permission)
                # Set expiration if provided
                if expires_at:
                    # This would need a custom association object for full control
                    pass
                db.session.commit()
                log_action('grant_permission', f'Granted {permission.permission_key} to {user.username}')
                flash('Permission granted successfully!', 'success')
        
        return redirect(url_for('permissions'))
    
    if request.method == 'POST' and 'revoke_permission' in request.form:
        user_id = request.form.get('user_id', type=int)
        permission_id = request.form.get('permission_id', type=int)
        
        user = User.query.get(user_id)
        permission = Permission.query.get(permission_id)
        
        if user and permission:
            user.permissions.remove(permission)
            db.session.commit()
            log_action('revoke_permission', f'Revoked {permission.permission_key} from {user.username}')
            flash('Permission revoked successfully!', 'success')
        
        return redirect(url_for('permissions'))
    
    # Get all users and permissions
    users = User.query.order_by(User.role, User.full_name).all()
    permissions = Permission.query.order_by(Permission.category, Permission.permission_name).all()
    
    # Group permissions by category
    grouped_permissions = {}
    for perm in permissions:
        if perm.category not in grouped_permissions:
            grouped_permissions[perm.category] = []
        grouped_permissions[perm.category].append(perm)
    
    # Get user permissions with details
    user_permissions = []
    for user in users:
        for perm in user.permissions:
            user_permissions.append({
                'user': user,
                'permission': perm
            })
    
    # Statistics
    stats = {
        'active_permissions': len(user_permissions),
        'users_with_permissions': len([u for u in users if u.permissions]),
        'total_permissions': len(permissions)
    }
    
    return render_template('permissions.html',
                         users=users,
                         permissions=permissions,
                         grouped_permissions=grouped_permissions,
                         user_permissions=user_permissions,
                         stats=stats)

# =====================================================
# DATABASE INITIALIZATION
# =====================================================

@app.cli.command('init-db')
def init_db():
    """Initialize the database with tables and default data"""
    db.create_all()
    
    # Create default permissions
    default_permissions = [
        # Products
        ('products.view', 'View Products', 'Products', 'Can view product list'),
        ('products.create', 'Create Products', 'Products', 'Can add new products'),
        ('products.edit', 'Edit Products', 'Products', 'Can edit existing products'),
        ('products.delete', 'Delete Products', 'Products', 'Can delete products'),
        ('products.manage_stock', 'Manage Stock', 'Products', 'Can adjust stock levels'),
        
        # Sales
        ('sales.view', 'View Sales', 'Sales', 'Can view sales'),
        ('sales.create', 'Create Sales', 'Sales', 'Can process new sales'),
        ('sales.edit', 'Edit Sales', 'Sales', 'Can edit existing sales'),
        ('sales.delete', 'Delete Sales', 'Sales', 'Can delete sales'),
        ('sales.refund', 'Process Refunds', 'Sales', 'Can process refunds'),
        
        # Cash
        ('cash.view', 'View Cash', 'Cash', 'Can view cash transactions'),
        ('cash.open_session', 'Open Session', 'Cash', 'Can open cash session'),
        ('cash.close_session', 'Close Session', 'Cash', 'Can close cash session'),
        ('cash.add_expense', 'Add Expenses', 'Cash', 'Can record expenses'),
        ('cash.view_report', 'View Cash Report', 'Cash', 'Can view cash reports'),
        
        # Reports
        ('reports.view_sales', 'View Sales Reports', 'Reports', 'Can view sales reports'),
        ('reports.view_tax', 'View Tax Reports', 'Reports', 'Can view tax reports'),
        ('reports.view_profit', 'View Profit Reports', 'Reports', 'Can view profit reports'),
        ('reports.export', 'Export Reports', 'Reports', 'Can export reports'),
        
        # Employees
        ('employees.view', 'View Employees', 'Employees', 'Can view employees'),
        ('employees.create', 'Create Employees', 'Employees', 'Can add employees'),
        ('employees.edit', 'Edit Employees', 'Employees', 'Can edit employees'),
        
        # Transfers
        ('transfers.view', 'View Transfers', 'Transfers', 'Can view transfers'),
        ('transfers.create', 'Create Transfers', 'Transfers', 'Can create transfers'),
        ('transfers.approve', 'Approve Transfers', 'Transfers', 'Can approve transfers'),
        ('transfers.receive', 'Receive Transfers', 'Transfers', 'Can receive transfers'),
        
        # Admin
        ('admin.access', 'Admin Access', 'Admin', 'Full system access'),
        ('admin.manage_users', 'Manage Users', 'Admin', 'Can manage users'),
        ('admin.manage_permissions', 'Manage Permissions', 'Admin', 'Can manage permissions'),
    ]
    
    for key, name, category, desc in default_permissions:
        perm = Permission.query.filter_by(permission_key=key).first()
        if not perm:
            perm = Permission(
                permission_key=key,
                permission_name=name,
                category=category,
                description=desc
            )
            db.session.add(perm)
    
    # Create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            full_name='System Administrator',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Create cashier users
    cashier1 = User.query.filter_by(username='cashier1').first()
    if not cashier1:
        cashier1 = User(
            username='cashier1',
            full_name='John Doe',
            role='cashier'
        )
        cashier1.set_password('cashier123')
        db.session.add(cashier1)
    
    cashier2 = User.query.filter_by(username='cashier2').first()
    if not cashier2:
        cashier2 = User(
            username='cashier2',
            full_name='Jane Smith',
            role='cashier'
        )
        cashier2.set_password('cashier123')
        db.session.add(cashier2)
    
    # Create default branch
    branch = Branch.query.filter_by(branch_code='HQ').first()
    if not branch:
        branch = Branch(
            branch_code='HQ',
            branch_name='Headquarters',
            location='Kigali',
            phone='+250 788 123 456',
            email='hq@theophile.com',
            manager='General Manager',
            address='KG 123 St, Kigali, Rwanda'
        )
        db.session.add(branch)
    
    # Create default categories
    categories = ['Beverages', 'Food Products', 'Dairy', 'Bakery', 'Snacks']
    for cat_name in categories:
        cat = Category.query.filter_by(name=cat_name).first()
        if not cat:
            cat = Category(name=cat_name)
            db.session.add(cat)
    
    db.session.commit()
    
    # Grant admin all permissions
    admin = User.query.filter_by(username='admin').first()
    all_perms = Permission.query.all()
    for perm in all_perms:
        if perm not in admin.permissions:
            admin.permissions.append(perm)
    
    db.session.commit()
    
    print("Database initialized successfully!")

# =====================================================
# MAIN ENTRY POINT
# =====================================================

if __name__ == '__main__':
    # Create upload directories
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logos'), exist_ok=True)
    
    app.run(debug=True)