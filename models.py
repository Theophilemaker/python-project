from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

db = SQLAlchemy()

# =====================================================
# ASSOCIATION TABLES
# =====================================================

user_permissions = db.Table('user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True),
    db.Column('granted_by', db.Integer, db.ForeignKey('users.id')),
    db.Column('granted_at', db.DateTime, default=datetime.utcnow),
    db.Column('expires_at', db.Date, nullable=True),
    db.Column('is_active', db.Boolean, default=True)
)

# =====================================================
# USER MODEL
# =====================================================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum('admin', 'cashier'), default='cashier')
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), default=1)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    branch = db.relationship('Branch', backref='users')
    sales = db.relationship('Sale', backref='cashier', lazy='dynamic')
    cash_sessions = db.relationship('CashSession', backref='user', lazy='dynamic')
    expenses_created = db.relationship('Expense', foreign_keys='Expense.created_by', backref='creator')
    expenses_approved = db.relationship('Expense', foreign_keys='Expense.approved_by', backref='approver')
    
    permissions = db.relationship('Permission', secondary=user_permissions,
                                 lazy='subquery',
                                 backref=db.backref('users', lazy=True))
    
    def set_password(self, password):
        # Using MD5 for compatibility with existing PHP system
        self.password_hash = hashlib.md5(password.encode()).hexdigest()
    
    def check_password(self, password):
        return self.password_hash == hashlib.md5(password.encode()).hexdigest()
    
    def has_permission(self, permission_key):
        if self.role == 'admin':
            return True
        for perm in self.permissions:
            if perm.permission_key == permission_key:
                # Check if expired
                assoc = db.session.query(user_permissions).filter_by(
                    user_id=self.id, permission_id=perm.id).first()
                if assoc and assoc.is_active:
                    if assoc.expires_at and assoc.expires_at < date.today():
                        return False
                    return True
        return False
    
    def get_id(self):
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'

# =====================================================
# PERMISSION MODEL
# =====================================================

class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    permission_key = db.Column(db.String(50), unique=True, nullable=False)
    permission_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Permission {self.permission_key}>'

# =====================================================
# BRANCH MODEL
# =====================================================

class Branch(db.Model):
    __tablename__ = 'branches'
    
    id = db.Column(db.Integer, primary_key=True)
    branch_code = db.Column(db.String(20), unique=True, nullable=False)
    branch_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    manager = db.Column(db.String(100))
    address = db.Column(db.Text)
    tax_id = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='branch', lazy='dynamic')
    sales = db.relationship('Sale', backref='branch', lazy='dynamic')
    employees = db.relationship('Employee', backref='branch', lazy='dynamic')
    expenses = db.relationship('Expense', backref='branch', lazy='dynamic')
    
    def __repr__(self):
        return f'<Branch {self.branch_code}>'

# =====================================================
# CATEGORY MODEL
# =====================================================

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'

# =====================================================
# PRODUCT MODEL
# =====================================================

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    buying_price = db.Column(db.Numeric(10, 2), default=0)
    selling_price = db.Column(db.Numeric(10, 2), default=0)
    tax_rate = db.Column(db.Numeric(5, 2), default=18.00)
    profit_margin = db.Column(db.Numeric(5, 2), default=0)
    quantity = db.Column(db.Integer, default=0)
    expiry_date = db.Column(db.Date)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), default=1)
    reorder_level = db.Column(db.Integer, default=5)
    sku = db.Column(db.String(50), unique=True)
    barcode = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='product', lazy='dynamic')
    po_items = db.relationship('POItem', backref='product', lazy='dynamic')
    transfer_items = db.relationship('TransferItem', backref='product', lazy='dynamic')
    tax_transactions = db.relationship('TaxTransaction', backref='product', lazy='dynamic')
    
    @property
    def profit(self):
        return float(self.selling_price) - float(self.buying_price)
    
    @property
    def profit_percentage(self):
        if self.buying_price and float(self.buying_price) > 0:
            return (float(self.selling_price) - float(self.buying_price)) / float(self.buying_price) * 100
        return 0
    
    @property
    def stock_status(self):
        if self.quantity < 5:
            return 'Low Stock'
        elif self.expiry_date and (self.expiry_date - date.today()).days < 7:
            return 'Expiring Soon'
        return 'In Stock'
    
    def __repr__(self):
        return f'<Product {self.name}>'

# =====================================================
# SALE MODEL
# =====================================================

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    cashier_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), default=1)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id'))
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum('cash', 'card', 'mobile', 'mixed'), default='cash')
    sale_date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tax_transaction = db.relationship('TaxTransaction', backref='sale', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Sale #{self.id}>'

# =====================================================
# TAX TRANSACTION MODEL
# =====================================================

class TaxTransaction(db.Model):
    __tablename__ = 'tax_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), default=0)
    selling_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    profit = db.Column(db.Numeric(10, 2), default=0)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=18.00)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False)
    total_with_tax = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TaxTransaction #{self.id}>'

# =====================================================
# CASH SESSION MODEL
# =====================================================

class CashSession(db.Model):
    __tablename__ = 'cash_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))
    opening_date = db.Column(db.Date, nullable=False, default=date.today)
    opening_time = db.Column(db.Time, nullable=False, default=datetime.utcnow().time)
    opening_balance = db.Column(db.Numeric(10, 2), default=0)
    closing_date = db.Column(db.Date)
    closing_time = db.Column(db.Time)
    closing_balance = db.Column(db.Numeric(10, 2))
    expected_balance = db.Column(db.Numeric(10, 2))
    difference = db.Column(db.Numeric(10, 2))
    status = db.Column(db.Enum('open', 'closed'), default='open')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='session', lazy='dynamic')
    cash_transactions = db.relationship('CashTransaction', backref='session', lazy='dynamic')
    
    def __repr__(self):
        return f'<CashSession #{self.id}>'

# =====================================================
# CASH TRANSACTION MODEL
# =====================================================

class CashTransaction(db.Model):
    __tablename__ = 'cash_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_sessions.id'), nullable=False)
    transaction_type = db.Column(db.Enum('sale', 'payment', 'expense', 'withdrawal', 'deposit', 'refund'), nullable=False)
    reference_id = db.Column(db.Integer)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum('cash', 'card', 'mobile'), default='cash')
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CashTransaction #{self.id}>'

# =====================================================
# EXPENSE MODEL
# =====================================================

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    expense_number = db.Column(db.String(50), unique=True, nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=date.today)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum('cash', 'bank', 'mobile'), default='cash')
    description = db.Column(db.Text)
    receipt_number = db.Column(db.String(100))
    paid_to = db.Column(db.String(200))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))
    status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='approved')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.expense_number}>'

# =====================================================
# SUPPLIER MODEL
# =====================================================

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_code = db.Column(db.String(50), unique=True, nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    tax_id = db.Column(db.String(50))
    payment_terms = db.Column(db.String(100))
    lead_time_days = db.Column(db.Integer, default=7)
    rating = db.Column(db.Numeric(3, 2), default=5.0)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.supplier_code}>'

# =====================================================
# PURCHASE ORDER MODEL
# =====================================================

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))
    order_date = db.Column(db.Date, default=date.today)
    expected_date = db.Column(db.Date)
    status = db.Column(db.Enum('draft', 'sent', 'received', 'cancelled', 'partial'), default='draft')
    subtotal = db.Column(db.Numeric(10, 2))
    tax_amount = db.Column(db.Numeric(10, 2))
    total_amount = db.Column(db.Numeric(10, 2))
    payment_status = db.Column(db.Enum('pending', 'partial', 'paid'), default='pending')
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('POItem', backref='purchase_order', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PO {self.po_number}>'

# =====================================================
# PO ITEM MODEL
# =====================================================

class POItem(db.Model):
    __tablename__ = 'po_items'
    
    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Numeric(10, 2))
    total_price = db.Column(db.Numeric(10, 2))
    received_quantity = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<POItem #{self.id}>'

# =====================================================
# STOCK TRANSFER MODEL
# =====================================================

class StockTransfer(db.Model):
    __tablename__ = 'stock_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    transfer_number = db.Column(db.String(50), unique=True, nullable=False)
    from_branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))
    to_branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))
    transfer_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.Enum('pending', 'approved', 'shipped', 'received', 'cancelled'), default='pending')
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    received_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    shipping_tracking = db.Column(db.String(100))
    shipping_carrier = db.Column(db.String(50))
    shipping_date = db.Column(db.Date)
    estimated_arrival = db.Column(db.Date)
    notes = db.Column(db.Text)
    total_value = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('TransferItem', backref='transfer', lazy='dynamic', cascade='all, delete-orphan')
    history = db.relationship('TransferHistory', backref='transfer', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Transfer {self.transfer_number}>'

# =====================================================
# TRANSFER ITEM MODEL
# =====================================================

class TransferItem(db.Model):
    __tablename__ = 'transfer_items'
    
    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('stock_transfers.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Numeric(10, 2))
    total_value = db.Column(db.Numeric(10, 2))
    received_quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('pending', 'partial', 'complete'), default='pending')
    
    def __repr__(self):
        return f'<TransferItem #{self.id}>'

# =====================================================
# TRANSFER HISTORY MODEL
# =====================================================

class TransferHistory(db.Model):
    __tablename__ = 'transfer_history'
    
    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('stock_transfers.id'))
    action = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<TransferHistory {self.action}>'

# =====================================================
# EMPLOYEE MODEL
# =====================================================

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100))
    department = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    base_salary = db.Column(db.Numeric(10, 2))
    hourly_rate = db.Column(db.Numeric(10, 2))
    bank_name = db.Column(db.String(100))
    bank_account = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), default=1)
    status = db.Column(db.Enum('active', 'inactive', 'on_leave'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    attendance = db.relationship('Attendance', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    payroll = db.relationship('Payroll', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Employee {self.employee_id}>'

# =====================================================
# ATTENDANCE MODEL
# =====================================================

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), default=1)
    clock_in = db.Column(db.DateTime)
    clock_out = db.Column(db.DateTime)
    hours_worked = db.Column(db.Numeric(5, 2))
    overtime_hours = db.Column(db.Numeric(5, 2))
    status = db.Column(db.Enum('present', 'absent', 'late', 'half_day'), default='present')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Attendance #{self.id}>'

# =====================================================
# PAYROLL MODEL
# =====================================================

class Payroll(db.Model):
    __tablename__ = 'payroll'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    pay_period_start = db.Column(db.Date)
    pay_period_end = db.Column(db.Date)
    regular_hours = db.Column(db.Numeric(5, 2))
    overtime_hours = db.Column(db.Numeric(5, 2))
    regular_pay = db.Column(db.Numeric(10, 2))
    overtime_pay = db.Column(db.Numeric(10, 2))
    bonus = db.Column(db.Numeric(10, 2), default=0)
    deductions = db.Column(db.Numeric(10, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    net_pay = db.Column(db.Numeric(10, 2))
    payment_date = db.Column(db.Date)
    status = db.Column(db.Enum('pending', 'paid', 'cancelled'), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payroll #{self.id}>'

# =====================================================
# COMPANY SETTINGS MODEL
# =====================================================

class CompanySetting(db.Model):
    __tablename__ = 'company_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    setting_type = db.Column(db.String(50), default='text')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Setting {self.setting_key}>'

# =====================================================
# AUDIT LOG MODEL
# =====================================================

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(255))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<AuditLog {self.action}>'