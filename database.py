import sqlite3
import hashlib

def init_db():
    conn = sqlite3.connect('velora_travel.db')
    cursor = conn.cursor()

    # Dynamic Lookup Tables
    cursor.execute('CREATE TABLE IF NOT EXISTS currencies (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS supplier_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS service_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS expense_categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS payment_statuses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS profile_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS commission_types (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)')
    
    # RBAC Tables

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL,
            module_name TEXT NOT NULL,
            can_view INTEGER DEFAULT 0,
            can_add INTEGER DEFAULT 0,
            can_edit INTEGER DEFAULT 0,
            can_delete INTEGER DEFAULT 0,
            UNIQUE(role_name, module_name)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role_name TEXT NOT NULL
        )
    ''')
    
    for col, col_type in [('password', 'TEXT NOT NULL DEFAULT ""'), ('role_name', 'TEXT NOT NULL DEFAULT "Administrator"')]:
        try:
            cursor.execute(f'ALTER TABLE users ADD COLUMN {col} {col_type}')
        except sqlite3.OperationalError:
            pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            profile_type TEXT NOT NULL,
            credit_limit_iqd REAL NOT NULL,
            preferred_currency TEXT,
            preferred_currency_amount REAL DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            supplier_type TEXT NOT NULL,
            amount_payable_iqd REAL DEFAULT 0,
            credit_limit_iqd REAL DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            service_type TEXT NOT NULL,
            pnr TEXT,
            ticket_number TEXT,
            passenger_name TEXT,
            selling_price_iqd REAL NOT NULL,
            selling_price_secondary REAL NOT NULL,
            secondary_currency TEXT DEFAULT 'USD',
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticketing_pnrs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pnr TEXT UNIQUE NOT NULL,
            airline_name TEXT NOT NULL,
            route TEXT NOT NULL,
            passenger_name TEXT NOT NULL,
            cost_iqd REAL NOT NULL,
            refund_iqd REAL DEFAULT 0,
            penalty_iqd REAL DEFAULT 0,
            status TEXT DEFAULT 'Active',
            created_date TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            invoice_number TEXT,
            issue_date TEXT,
            due_date TEXT,
            amount REAL DEFAULT 0,
            currency TEXT DEFAULT 'IQD',
            status TEXT DEFAULT 'Unpaid',
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            description TEXT,
            amount_iqd REAL NOT NULL,
            amount_secondary REAL DEFAULT 0,
            currency TEXT DEFAULT 'USD',
            expense_date TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commission_type TEXT NOT NULL,
            reference_no TEXT NOT NULL,
            beneficiary_name TEXT NOT NULL,
            amount_iqd REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            amount_secondary REAL DEFAULT 0,
            commission_date TEXT NOT NULL
        )
    ''')

    # Seed Lookups
    cursor.executemany('INSERT OR IGNORE INTO profile_types (name) VALUES (?)', [('Individual',), ('Corporate',)])
    cursor.executemany('INSERT OR IGNORE INTO service_types (name) VALUES (?)', [('Air Ticket',), ('Hotel Booking',), ('Visa Service',), ('Tour Package',), ('Transport',)])
    cursor.executemany('INSERT OR IGNORE INTO expense_categories (name) VALUES (?)', [('Office Rent',), ('Staff Salaries',), ('Utilities',), ('Internet & Telecom',), ('Marketing',), ('Transportation',), ('Office Supplies',), ('Other',)])
    cursor.executemany('INSERT OR IGNORE INTO payment_statuses (name) VALUES (?)', [('Pending',), ('Paid',), ('Overdue',), ('Partially Paid',), ('Cancelled',)])
    cursor.executemany('INSERT OR IGNORE INTO commission_types (name) VALUES (?)', [('Airline Commission',), ('Hotel Commission',), ('DMC Commission',), ('Supplier Commission',), ('Salesperson Commission',), ('Agent Commission',)])

    admin_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    cursor.execute('INSERT OR IGNORE INTO users (username, password, role_name) VALUES (?, ?, ?)', ('admin', admin_hash, 'Administrator'))

    modules = ['Dashboard', 'Bookings', 'Ticketing', 'Invoices', 'Customers', 'Suppliers', 'Expenses', 'Commissions', 'Settings']
    for m in modules:
        cursor.execute('INSERT OR IGNORE INTO permissions (role_name, module_name, can_view, can_add, can_edit, can_delete) VALUES (?, ?, 1, 1, 1, 1)', ('Administrator', m))

    conn.commit()
    conn.close()
    print("Database updated successfully!")

if __name__ == '__main__':
    init_db()