-- =====================================================
-- THEOPHILE POS - COMPLETE DATABASE SCHEMA
-- Version: 3.0
-- Description: Point of Sale System with Multi-Branch, 
--              Inventory, HR, Payroll, and Permissions
-- =====================================================

-- Drop database if exists (CAUTION: This will delete all data)
-- DROP DATABASE IF EXISTS theophile_pos;

-- Create database
CREATE DATABASE IF NOT EXISTS theophile_pos
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE theophile_pos;

-- =====================================================
-- 1. CORE TABLES
-- =====================================================

-- Users table (system access)
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    role ENUM('admin', 'cashier') DEFAULT 'cashier',
    branch_id INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_role (role),
    INDEX idx_users_branch (branch_id),
    INDEX idx_users_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Branches table
CREATE TABLE branches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    branch_code VARCHAR(20) UNIQUE NOT NULL,
    branch_name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(100),
    manager VARCHAR(100),
    address TEXT,
    tax_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_branches_code (branch_code),
    INDEX idx_branches_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Categories table
CREATE TABLE categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_categories_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Products table
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    category_id INT,
    buying_price DECIMAL(10,2) DEFAULT 0,
    selling_price DECIMAL(10,2) DEFAULT 0,
    tax_rate DECIMAL(5,2) DEFAULT 18.00,
    profit_margin DECIMAL(5,2) DEFAULT 0,
    quantity INT DEFAULT 0,
    expiry_date DATE,
    branch_id INT DEFAULT 1,
    reorder_level INT DEFAULT 5,
    sku VARCHAR(50) UNIQUE,
    barcode VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL,
    INDEX idx_products_name (name),
    INDEX idx_products_branch (branch_id),
    INDEX idx_products_expiry (expiry_date),
    INDEX idx_products_quantity (quantity),
    INDEX idx_products_sku (sku)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 2. SALES AND TRANSACTIONS
-- =====================================================

-- Sales table
CREATE TABLE sales (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT,
    cashier_id INT,
    branch_id INT DEFAULT 1,
    session_id INT,
    quantity INT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    payment_method ENUM('cash', 'card', 'mobile', 'mixed') DEFAULT 'cash',
    sale_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    FOREIGN KEY (cashier_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL,
    INDEX idx_sales_date (sale_date),
    INDEX idx_sales_branch (branch_id),
    INDEX idx_sales_cashier (cashier_id),
    INDEX idx_sales_payment (payment_method)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tax transactions table (18% on profit)
CREATE TABLE tax_transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    cost_price DECIMAL(10,2) DEFAULT 0,
    selling_price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL,
    profit DECIMAL(10,2) DEFAULT 0,
    subtotal DECIMAL(10,2) NOT NULL,
    tax_rate DECIMAL(5,2) NOT NULL DEFAULT 18.00,
    tax_amount DECIMAL(10,2) NOT NULL,
    total_with_tax DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_tax_sale (sale_id),
    INDEX idx_tax_date (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tax settings table
CREATE TABLE tax_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tax_name VARCHAR(100) NOT NULL,
    tax_rate DECIMAL(5,2) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    applies_to ENUM('all', 'profit', 'sales') DEFAULT 'profit',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 3. CASH MANAGEMENT
-- =====================================================

-- Cash sessions table
CREATE TABLE cash_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    branch_id INT,
    opening_date DATE NOT NULL,
    opening_time TIME NOT NULL,
    opening_balance DECIMAL(10,2) DEFAULT 0,
    closing_date DATE,
    closing_time TIME,
    closing_balance DECIMAL(10,2),
    expected_balance DECIMAL(10,2),
    difference DECIMAL(10,2),
    status ENUM('open', 'closed') DEFAULT 'open',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    INDEX idx_cash_user (user_id),
    INDEX idx_cash_status (status),
    INDEX idx_cash_date (opening_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Cash transactions table
CREATE TABLE cash_transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    transaction_type ENUM('sale', 'payment', 'expense', 'withdrawal', 'deposit', 'refund') NOT NULL,
    reference_id INT,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('cash', 'card', 'mobile') DEFAULT 'cash',
    description TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES cash_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_cash_trans_session (session_id),
    INDEX idx_cash_trans_type (transaction_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Expenses table
CREATE TABLE expenses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    expense_number VARCHAR(50) UNIQUE NOT NULL,
    expense_date DATE NOT NULL,
    category VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('cash', 'bank', 'mobile') DEFAULT 'cash',
    description TEXT,
    receipt_number VARCHAR(100),
    paid_to VARCHAR(200),
    approved_by INT,
    created_by INT,
    branch_id INT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'approved',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    INDEX idx_expenses_date (expense_date),
    INDEX idx_expenses_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Expense categories table
CREATE TABLE expense_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 4. SUPPLIER MANAGEMENT
-- =====================================================

-- Suppliers table
CREATE TABLE suppliers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    tax_id VARCHAR(50),
    payment_terms VARCHAR(100),
    lead_time_days INT DEFAULT 7,
    rating DECIMAL(3,2) DEFAULT 5.0,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_suppliers_code (supplier_code),
    INDEX idx_suppliers_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Purchase orders table
CREATE TABLE purchase_orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_id INT,
    branch_id INT,
    order_date DATE,
    expected_date DATE,
    status ENUM('draft', 'sent', 'received', 'cancelled', 'partial') DEFAULT 'draft',
    subtotal DECIMAL(10,2),
    tax_amount DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    payment_status ENUM('pending', 'partial', 'paid') DEFAULT 'pending',
    notes TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_po_number (po_number),
    INDEX idx_po_status (status),
    INDEX idx_po_date (order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Purchase order items table
CREATE TABLE po_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    po_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    received_quantity INT DEFAULT 0,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    INDEX idx_po_items_po (po_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 5. STOCK TRANSFERS
-- =====================================================

-- Stock transfers table
CREATE TABLE stock_transfers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    transfer_number VARCHAR(50) UNIQUE NOT NULL,
    from_branch_id INT,
    to_branch_id INT,
    transfer_date DATE,
    status ENUM('pending', 'approved', 'shipped', 'received', 'cancelled') DEFAULT 'pending',
    requested_by INT,
    approved_by INT,
    received_by INT,
    shipping_tracking VARCHAR(100),
    shipping_carrier VARCHAR(50),
    shipping_date DATE,
    estimated_arrival DATE,
    notes TEXT,
    total_value DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_branch_id) REFERENCES branches(id),
    FOREIGN KEY (to_branch_id) REFERENCES branches(id),
    FOREIGN KEY (requested_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (received_by) REFERENCES users(id),
    INDEX idx_transfer_number (transfer_number),
    INDEX idx_transfer_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Transfer items table
CREATE TABLE transfer_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    transfer_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10,2),
    total_value DECIMAL(10,2),
    received_quantity INT DEFAULT 0,
    status ENUM('pending', 'partial', 'complete') DEFAULT 'pending',
    FOREIGN KEY (transfer_id) REFERENCES stock_transfers(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Transfer history table
CREATE TABLE transfer_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    transfer_id INT,
    action VARCHAR(50),
    user_id INT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transfer_id) REFERENCES stock_transfers(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 6. HR MANAGEMENT
-- =====================================================

-- Employees table
CREATE TABLE employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    position VARCHAR(100),
    department VARCHAR(100),
    hire_date DATE,
    base_salary DECIMAL(10,2),
    hourly_rate DECIMAL(10,2),
    bank_name VARCHAR(100),
    bank_account VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    branch_id INT DEFAULT 1,
    status ENUM('active', 'inactive', 'on_leave') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    INDEX idx_employees_id (employee_id),
    INDEX idx_employees_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Attendance table
CREATE TABLE attendance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id INT,
    branch_id INT DEFAULT 1,
    clock_in DATETIME,
    clock_out DATETIME,
    hours_worked DECIMAL(5,2),
    overtime_hours DECIMAL(5,2),
    status ENUM('present', 'absent', 'late', 'half_day') DEFAULT 'present',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    INDEX idx_attendance_date (clock_in),
    INDEX idx_attendance_employee (employee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Payroll table
CREATE TABLE payroll (
    id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id INT,
    pay_period_start DATE,
    pay_period_end DATE,
    regular_hours DECIMAL(5,2),
    overtime_hours DECIMAL(5,2),
    regular_pay DECIMAL(10,2),
    overtime_pay DECIMAL(10,2),
    bonus DECIMAL(10,2) DEFAULT 0,
    deductions DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    net_pay DECIMAL(10,2),
    payment_date DATE,
    status ENUM('pending', 'paid', 'cancelled') DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    INDEX idx_payroll_period (pay_period_start, pay_period_end),
    INDEX idx_payroll_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 7. PERMISSIONS SYSTEM
-- =====================================================

-- Permissions table
CREATE TABLE permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    permission_key VARCHAR(50) UNIQUE NOT NULL,
    permission_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_permissions_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- User permissions table
CREATE TABLE user_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    permission_id INT NOT NULL,
    granted_by INT,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at DATE NULL,
    revoked_by INT,
    revoked_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (revoked_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY unique_user_permission (user_id, permission_id),
    INDEX idx_user_permissions_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 8. COMPANY SETTINGS
-- =====================================================

-- Company settings table
CREATE TABLE company_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'text',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by INT,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_settings_key (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 9. AUDIT LOGS
-- =====================================================

-- Audit logs table
CREATE TABLE audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(255),
    details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_date (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- 10. DEFAULT DATA INSERTION
-- =====================================================

-- Insert default branches
INSERT INTO branches (branch_code, branch_name, location, phone, email, manager) VALUES
('HQ', 'Headquarters', 'Kigali', '+250 788 123 456', 'hq@theophile.com', 'General Manager'),
('KGL01', 'Kigali City Branch', 'Downtown Kigali', '+250 788 123 457', 'kigali@theophile.com', 'Branch Manager'),
('HYE01', 'Huye Branch', 'Butare', '+250 788 123 458', 'huye@theophile.com', 'Branch Manager'),
('MSZ01', 'Musanze Branch', 'Ruhengeri', '+250 788 123 459', 'musanze@theophile.com', 'Branch Manager');

-- Insert default users (passwords: admin123, cashier123)
INSERT INTO users (username, password, full_name, email, phone, role, branch_id) VALUES
('admin', MD5('admin123'), 'System Administrator', 'admin@theophile.com', '+250 788 000 001', 'admin', 1),
('cashier1', MD5('cashier123'), 'John Doe', 'john.doe@theophile.com', '+250 788 000 002', 'cashier', 2),
('cashier2', MD5('cashier123'), 'Jane Smith', 'jane.smith@theophile.com', '+250 788 000 003', 'cashier', 3);

-- Insert default categories
INSERT INTO categories (name, description) VALUES
('Beverages', 'Soft drinks, juices, water, etc.'),
('Food Products', 'Packaged food items'),
('Dairy', 'Milk, yogurt, cheese, etc.'),
('Bakery', 'Bread, cakes, pastries'),
('Snacks', 'Chips, cookies, candies'),
('Household', 'Cleaning supplies, etc.'),
('Electronics', 'Small electronics and accessories');

-- Insert default tax settings (18% on profit)
INSERT INTO tax_settings (tax_name, tax_rate, is_default, applies_to) VALUES
('VAT Standard', 18.00, TRUE, 'profit'),
('VAT Zero Rated', 0.00, FALSE, 'all'),
('Service Charge', 10.00, FALSE, 'sales');

-- Insert default expense categories
INSERT INTO expense_categories (name, description) VALUES
('Utilities', 'Electricity, water, internet bills'),
('Rent', 'Branch/office rent'),
('Salaries', 'Employee salaries and wages'),
('Supplies', 'Office and operational supplies'),
('Maintenance', 'Equipment and building maintenance'),
('Transport', 'Fuel, delivery, transport costs'),
('Marketing', 'Advertising and promotions'),
('Taxes', 'Tax payments'),
('Miscellaneous', 'Other expenses');

-- Insert default permissions
INSERT INTO permissions (permission_key, permission_name, category, description) VALUES
-- Products
('products.view', 'View Products', 'Products', 'Can view product list'),
('products.create', 'Create Products', 'Products', 'Can add new products'),
('products.edit', 'Edit Products', 'Products', 'Can edit existing products'),
('products.delete', 'Delete Products', 'Products', 'Can delete products'),
('products.manage_stock', 'Manage Stock', 'Products', 'Can adjust stock levels'),

-- Sales
('sales.view', 'View Sales', 'Sales', 'Can view sales'),
('sales.create', 'Create Sales', 'Sales', 'Can process new sales'),
('sales.edit', 'Edit Sales', 'Sales', 'Can edit existing sales'),
('sales.delete', 'Delete Sales', 'Sales', 'Can delete sales'),
('sales.refund', 'Process Refunds', 'Sales', 'Can process refunds'),

-- Cash
('cash.view', 'View Cash', 'Cash', 'Can view cash transactions'),
('cash.open_session', 'Open Session', 'Cash', 'Can open cash session'),
('cash.close_session', 'Close Session', 'Cash', 'Can close cash session'),
('cash.add_expense', 'Add Expenses', 'Cash', 'Can record expenses'),
('cash.view_report', 'View Cash Report', 'Cash', 'Can view cash reports'),

-- Reports
('reports.view_sales', 'View Sales Reports', 'Reports', 'Can view sales reports'),
('reports.view_tax', 'View Tax Reports', 'Reports', 'Can view tax reports'),
('reports.view_profit', 'View Profit Reports', 'Reports', 'Can view profit reports'),
('reports.export', 'Export Reports', 'Reports', 'Can export reports'),

-- Employees
('employees.view', 'View Employees', 'Employees', 'Can view employees'),
('employees.create', 'Create Employees', 'Employees', 'Can add employees'),
('employees.edit', 'Edit Employees', 'Employees', 'Can edit employees'),

-- Transfers
('transfers.view', 'View Transfers', 'Transfers', 'Can view transfers'),
('transfers.create', 'Create Transfers', 'Transfers', 'Can create transfers'),
('transfers.approve', 'Approve Transfers', 'Transfers', 'Can approve transfers'),
('transfers.receive', 'Receive Transfers', 'Transfers', 'Can receive transfers'),

-- Admin
('admin.access', 'Admin Access', 'Admin', 'Full system access'),
('admin.manage_users', 'Manage Users', 'Admin', 'Can manage users'),
('admin.manage_permissions', 'Manage Permissions', 'Admin', 'Can manage permissions'),

-- Branches
('branches.view', 'View Branches', 'Branches', 'Can view branches'),
('branches.manage', 'Manage Branches', 'Branches', 'Can manage branches'),

-- Suppliers
('suppliers.view', 'View Suppliers', 'Suppliers', 'Can view suppliers'),
('suppliers.manage', 'Manage Suppliers', 'Suppliers', 'Can manage suppliers'),

-- Purchase Orders
('purchase_orders.view', 'View Purchase Orders', 'Purchase Orders', 'Can view purchase orders'),
('purchase_orders.create', 'Create Purchase Orders', 'Purchase Orders', 'Can create purchase orders'),
('purchase_orders.receive', 'Receive Purchase Orders', 'Purchase Orders', 'Can receive purchase orders'),

-- Attendance
('attendance.view', 'View Attendance', 'Attendance', 'Can view attendance records'),
('attendance.manage', 'Manage Attendance', 'Attendance', 'Can manage attendance'),

-- Payroll
('payroll.view', 'View Payroll', 'Payroll', 'Can view payroll'),
('payroll.manage', 'Manage Payroll', 'Payroll', 'Can manage payroll');

-- Grant all permissions to admin (user_id = 1)
INSERT INTO user_permissions (user_id, permission_id, granted_by)
SELECT 1, id, 1 FROM permissions
ON DUPLICATE KEY UPDATE is_active = 1;

-- Insert default company settings
INSERT INTO company_settings (setting_key, setting_value, setting_type) VALUES
('company_name', 'Theophile POS', 'text'),
('tagline', 'Complete Point of Sale Solution', 'text'),
('address', 'KG 123 St, Kigali, Rwanda', 'text'),
('phone', '+250 788 123 456', 'text'),
('email', 'info@theophile.com', 'text'),
('website', 'www.theophile.com', 'text'),
('tax_number', 'TAX123456789', 'text'),
('footer_text', 'Thank you for your business!', 'text'),
('logo', '', 'image'),
('favicon', '', 'image');

-- Insert sample products
INSERT INTO products (name, category_id, buying_price, selling_price, quantity, expiry_date, branch_id, tax_rate) VALUES
('Sugar', 2, 800, 1000, 50, DATE_ADD(CURDATE(), INTERVAL 180 DAY), 1, 18.00),
('Milk', 3, 600, 800, 30, DATE_ADD(CURDATE(), INTERVAL 5 DAY), 1, 18.00),
('Yogurt', 3, 700, 900, 25, DATE_ADD(CURDATE(), INTERVAL 5 DAY), 1, 18.00),
('Biscuits', 5, 400, 600, 100, DATE_ADD(CURDATE(), INTERVAL 90 DAY), 1, 18.00),
('Bread', 4, 500, 700, 20, DATE_ADD(CURDATE(), INTERVAL 3 DAY), 1, 18.00),
('Juice', 1, 800, 1000, 40, DATE_ADD(CURDATE(), INTERVAL 60 DAY), 1, 18.00),
('Soda', 1, 400, 600, 200, DATE_ADD(CURDATE(), INTERVAL 90 DAY), 1, 18.00),
('Rice', 2, 1500, 2000, 80, DATE_ADD(CURDATE(), INTERVAL 365 DAY), 1, 18.00),
('Cooking Oil', 2, 2000, 2500, 60, DATE_ADD(CURDATE(), INTERVAL 180 DAY), 1, 18.00),
('Flour', 2, 700, 1000, 45, DATE_ADD(CURDATE(), INTERVAL 120 DAY), 1, 18.00);

-- Insert sample suppliers
INSERT INTO suppliers (supplier_code, company_name, contact_person, phone, email, payment_terms, lead_time_days) VALUES
('SUP001', 'Rwanda Wholesalers Ltd', 'Jean Paul', '+250 788 234 567', 'info@rwandawholesale.rw', 'Net 30', 5),
('SUP002', 'East African Distributors', 'Sarah Johnson', '+250 788 345 678', 'sales@eastafricadist.com', 'Net 15', 3),
('SUP003', 'Global Foods Inc', 'Michael Chen', '+250 788 456 789', 'orders@globalfoods.com', 'Net 45', 10),
('SUP004', 'Local Farmers Cooperative', 'Marie Claire', '+250 788 567 890', 'farmers@coop.rw', 'Cash on Delivery', 2);

-- Insert sample employees
INSERT INTO employees (user_id, employee_id, full_name, position, department, base_salary, hire_date, phone, email, branch_id) VALUES
(1, 'EMP001', 'System Administrator', 'Manager', 'Management', 500000, '2023-01-01', '0788000001', 'admin@theophile.com', 1),
(2, 'EMP002', 'John Doe', 'Cashier', 'Sales', 250000, '2023-02-01', '0788000002', 'john@theophile.com', 2),
(3, 'EMP003', 'Jane Smith', 'Senior Cashier', 'Sales', 300000, '2023-03-01', '0788000003', 'jane@theophile.com', 3);

-- Generate sample sales for the last 30 days
INSERT INTO sales (product_id, cashier_id, branch_id, quantity, total_price, payment_method, sale_date)
SELECT 
    p.id,
    FLOOR(1 + RAND() * 3) as cashier_id,
    FLOOR(1 + RAND() * 4) as branch_id,
    FLOOR(1 + RAND() * 5) as quantity,
    p.selling_price * FLOOR(1 + RAND() * 5) as total_price,
    ELT(FLOOR(1 + RAND() * 3), 'cash', 'card', 'mobile') as payment_method,
    DATE_SUB(CURDATE(), INTERVAL FLOOR(RAND() * 30) DAY) as sale_date
FROM products p
CROSS JOIN (
    SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
) nums
LIMIT 100;

-- Generate tax transactions for the sample sales
INSERT INTO tax_transactions (sale_id, product_id, cost_price, selling_price, quantity, profit, subtotal, tax_rate, tax_amount, total_with_tax)
SELECT 
    s.id,
    s.product_id,
    p.buying_price,
    p.selling_price,
    s.quantity,
    (p.selling_price - p.buying_price) * s.quantity as profit,
    p.selling_price * s.quantity as subtotal,
    18.00 as tax_rate,
    ((p.selling_price - p.buying_price) * s.quantity) * 0.18 as tax_amount,
    (p.selling_price * s.quantity) + (((p.selling_price - p.buying_price) * s.quantity) * 0.18) as total_with_tax
FROM sales s
JOIN products p ON s.product_id = p.id
WHERE s.id NOT IN (SELECT sale_id FROM tax_transactions);

-- =====================================================
-- 11. CREATE VIEWS FOR COMMON REPORTS
-- =====================================================

-- Daily sales summary view
CREATE VIEW vw_daily_sales AS
SELECT 
    sale_date,
    COUNT(*) as transactions,
    SUM(quantity) as items_sold,
    SUM(total_price) as total_sales,
    AVG(total_price) as avg_sale,
    SUM(CASE WHEN payment_method = 'cash' THEN total_price ELSE 0 END) as cash_sales,
    SUM(CASE WHEN payment_method = 'card' THEN total_price ELSE 0 END) as card_sales,
    SUM(CASE WHEN payment_method = 'mobile' THEN total_price ELSE 0 END) as mobile_sales
FROM sales
GROUP BY sale_date
ORDER BY sale_date DESC;

-- Product performance view
CREATE VIEW vw_product_performance AS
SELECT 
    p.id,
    p.name,
    c.name as category,
    p.selling_price,
    p.buying_price,
    p.quantity as current_stock,
    COALESCE(SUM(s.quantity), 0) as total_sold,
    COALESCE(SUM(s.total_price), 0) as revenue,
    COALESCE(SUM((p.selling_price - p.buying_price) * s.quantity), 0) as profit
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN sales s ON p.id = s.product_id
GROUP BY p.id
ORDER BY revenue DESC;

-- Cashier performance view
CREATE VIEW vw_cashier_performance AS
SELECT 
    u.id,
    u.full_name,
    u.role,
    COUNT(s.id) as transactions,
    COALESCE(SUM(s.total_price), 0) as total_sales,
    COALESCE(AVG(s.total_price), 0) as avg_sale,
    MAX(s.sale_date) as last_sale
FROM users u
LEFT JOIN sales s ON u.id = s.cashier_id
WHERE u.role IN ('admin', 'cashier')
GROUP BY u.id
ORDER BY total_sales DESC;

-- Branch performance view
CREATE VIEW vw_branch_performance AS
SELECT 
    b.id,
    b.branch_name,
    b.location,
    b.manager,
    COUNT(DISTINCT p.id) as products,
    COUNT(DISTINCT e.id) as employees,
    COUNT(DISTINCT s.id) as transactions,
    COALESCE(SUM(s.total_price), 0) as total_sales,
    COALESCE(AVG(s.total_price), 0) as avg_sale
FROM branches b
LEFT JOIN products p ON b.id = p.branch_id
LEFT JOIN employees e ON b.id = e.branch_id
LEFT JOIN sales s ON b.id = s.branch_id
GROUP BY b.id;

-- Tax summary view
CREATE VIEW vw_tax_summary AS
SELECT 
    DATE(s.sale_date) as date,
    COUNT(*) as transactions,
    COALESCE(SUM(tt.profit), 0) as total_profit,
    COALESCE(SUM(tt.tax_amount), 0) as tax_collected,
    COALESCE(AVG(tt.tax_rate), 0) as avg_tax_rate
FROM tax_transactions tt
JOIN sales s ON tt.sale_id = s.id
GROUP BY DATE(s.sale_date)
ORDER BY date DESC;

-- =====================================================
-- 12. CREATE INDEXES FOR PERFORMANCE
-- =====================================================

-- Additional indexes for better query performance
CREATE INDEX idx_sales_product ON sales(product_id);
CREATE INDEX idx_sales_cashier_date ON sales(cashier_id, sale_date);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_branch_stock ON products(branch_id, quantity);
CREATE INDEX idx_attendance_employee_date ON attendance(employee_id, clock_in);
CREATE INDEX idx_payroll_employee_period ON payroll(employee_id, pay_period_start);
CREATE INDEX idx_transfer_from_to ON stock_transfers(from_branch_id, to_branch_id);
CREATE INDEX idx_transfer_status_date ON stock_transfers(status, transfer_date);
CREATE INDEX idx_user_permissions_user ON user_permissions(user_id, is_active);

-- =====================================================
-- 13. STORED PROCEDURES
-- =====================================================

DELIMITER //

-- Get monthly sales report
CREATE PROCEDURE GetMonthlyReport(IN month_num INT, IN year_num INT)
BEGIN
    SELECT 
        DATE_FORMAT(sale_date, '%Y-%m-%d') as date,
        COUNT(DISTINCT s.id) as transactions,
        COUNT(DISTINCT s.cashier_id) as active_cashiers,
        SUM(s.quantity) as items_sold,
        SUM(s.total_price) as total_sales,
        SUM((p.selling_price - p.buying_price) * s.quantity) as total_profit,
        SUM(tt.tax_amount) as total_tax
    FROM sales s
    JOIN products p ON s.product_id = p.id
    LEFT JOIN tax_transactions tt ON s.id = tt.sale_id
    WHERE MONTH(s.sale_date) = month_num 
      AND YEAR(s.sale_date) = year_num
    GROUP BY DATE(s.sale_date)
    ORDER BY s.sale_date;
END //

-- Get branch summary
CREATE PROCEDURE GetBranchSummary(IN branch_id_param INT)
BEGIN
    SELECT 
        b.*,
        COUNT(DISTINCT p.id) as total_products,
        COUNT(DISTINCT e.id) as total_employees,
        COUNT(DISTINCT s.id) as today_transactions,
        COALESCE(SUM(s.total_price), 0) as today_sales,
        (SELECT COUNT(*) FROM stock_transfers WHERE from_branch_id = branch_id_param AND status = 'pending') as pending_outgoing,
        (SELECT COUNT(*) FROM stock_transfers WHERE to_branch_id = branch_id_param AND status = 'pending') as pending_incoming
    FROM branches b
    LEFT JOIN products p ON b.id = p.branch_id
    LEFT JOIN employees e ON b.id = e.branch_id
    LEFT JOIN sales s ON b.id = s.branch_id AND DATE(s.sale_date) = CURDATE()
    WHERE b.id = branch_id_param
    GROUP BY b.id;
END //

-- Calculate payroll for a period
CREATE PROCEDURE CalculatePayroll(IN period_start DATE, IN period_end DATE)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE emp_id INT;
    DECLARE emp_salary DECIMAL(10,2);
    DECLARE emp_hourly DECIMAL(10,2);
    DECLARE total_hours DECIMAL(5,2);
    DECLARE total_ot DECIMAL(5,2);
    
    DECLARE emp_cursor CURSOR FOR 
        SELECT id, base_salary, hourly_rate FROM employees WHERE status = 'active';
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    OPEN emp_cursor;
    
    read_loop: LOOP
        FETCH emp_cursor INTO emp_id, emp_salary, emp_hourly;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- Get attendance hours
        SELECT 
            COALESCE(SUM(hours_worked), 0),
            COALESCE(SUM(overtime_hours), 0)
        INTO total_hours, total_ot
        FROM attendance
        WHERE employee_id = emp_id 
          AND DATE(clock_in) BETWEEN period_start AND period_end;
        
        -- Insert into payroll table
        INSERT INTO payroll 
            (employee_id, pay_period_start, pay_period_end, regular_hours, 
             overtime_hours, regular_pay, overtime_pay, net_pay, status)
        VALUES (
            emp_id, period_start, period_end, total_hours, total_ot,
            total_hours * COALESCE(emp_hourly, emp_salary/160, 1000),
            total_ot * COALESCE(emp_hourly, emp_salary/160, 1000) * 1.5,
            (total_hours * COALESCE(emp_hourly, emp_salary/160, 1000)) + 
            (total_ot * COALESCE(emp_hourly, emp_salary/160, 1000) * 1.5),
            'pending'
        );
    END LOOP;
    
    CLOSE emp_cursor;
END //

DELIMITER ;

-- =====================================================
-- 14. TRIGGERS
-- =====================================================

-- Update product profit margin after insert/update
DELIMITER //
CREATE TRIGGER update_product_profit_margin
BEFORE INSERT ON products
FOR EACH ROW
BEGIN
    IF NEW.buying_price > 0 THEN
        SET NEW.profit_margin = ((NEW.selling_price - NEW.buying_price) / NEW.buying_price) * 100;
    ELSE
        SET NEW.profit_margin = 0;
    END IF;
END //

CREATE TRIGGER update_product_profit_margin_on_update
BEFORE UPDATE ON products
FOR EACH ROW
BEGIN
    IF NEW.buying_price > 0 THEN
        SET NEW.profit_margin = ((NEW.selling_price - NEW.buying_price) / NEW.buying_price) * 100;
    ELSE
        SET NEW.profit_margin = 0;
    END IF;
END //

-- Update product quantity after sale
CREATE TRIGGER update_stock_after_sale
AFTER INSERT ON sales
FOR EACH ROW
BEGIN
    UPDATE products 
    SET quantity = quantity - NEW.quantity 
    WHERE id = NEW.product_id;
END //

DELIMITER ;

-- =====================================================
-- 15. DATABASE MAINTENANCE
-- =====================================================

-- Analyze tables for optimal performance
ANALYZE TABLE users, products, sales, branches, employees;

-- Optimize tables
OPTIMIZE TABLE users, products, sales, tax_transactions, permissions;

-- =====================================================
-- END OF DATABASE SCHEMA
-- =====================================================

-- Display success message
SELECT 'Theophile POS Database successfully created!' as 'Status';
SELECT CONCAT('Total Tables: ', COUNT(*)) as 'Summary' FROM information_schema.tables WHERE table_schema = 'theophile_pos';