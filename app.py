from flask import Flask, request, redirect, url_for, render_template_string, session
import sqlite3
import datetime
import hashlib

app = Flask(__name__)
app.secret_key = 'velora_travel_secure_secret_key'

def get_db_connection():
    conn = sqlite3.connect('velora_travel.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_db_connection():
    conn = sqlite3.connect('velora_travel.db')
    conn.row_factory = sqlite3.Row
    return conn

def log_activity(action, details):
    username = session.get('username', 'System')
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                 (username, action, details, timestamp))
    conn.commit()
    conn.close()

def check_permission(module_name, action='view'):
    if 'user_role' not in session:
        return False
    if session['user_role'] == 'Administrator':
        return True
    
    conn = get_db_connection()
    perm = conn.execute('SELECT * FROM permissions WHERE role_name = ? AND module_name = ?', (session['user_role'], module_name)).fetchone()
    conn.close()
    
    if not perm:
        return False
    if action == 'view': return perm['can_view'] == 1
    if action == 'add': return perm['can_add'] == 1
    if action == 'edit': return perm['can_edit'] == 1
    if action == 'delete': return perm['can_delete'] == 1
    return False

def render_layout(title, content):
    username = session.get('username', 'Guest')
    role = session.get('user_role', 'None')
    
    conn = get_db_connection()
    if role == 'Administrator':
        allowed_modules = ['Dashboard', 'Bookings', 'Ticketing', 'Invoices', 'Customers', 'Suppliers', 'Expenses', 'Commissions', 'Settings']
    else:
        perms = conn.execute('SELECT module_name FROM permissions WHERE role_name = ? AND can_view = 1', (role,)).fetchall()
        allowed_modules = [p['module_name'] for p in perms]
    conn.close()
    
    def can_see(mod):
        if role == 'Administrator': return True
        return mod in allowed_modules

    def nav_link(path, label, mod_name):
        if not can_see(mod_name):
            return ""
        return f'<a href="{path}" data-path="{path}" class="nav-link-item block px-4 py-2 rounded-lg transition font-medium text-xs text-slate-300 hover:bg-slate-800 hover:text-white">{label}</a>'

    nav_links = f"""
        {nav_link("/", "Dashboard & P&L", "Dashboard")}
        {nav_link("/bookings", "Sales & Bookings", "Bookings")}
        {nav_link("/ticketing", "Airline Ticketing & PNR", "Ticketing")}
        {nav_link("/invoices", "Invoices & AR", "Invoices")}
        {nav_link("/customers", "Customers", "Customers")}
        {nav_link("/suppliers", "Suppliers", "Suppliers")}
        {nav_link("/expenses", "Expenses", "Expenses")}
        {nav_link("/commissions", "Commissions", "Commissions")}
    """

    if can_see('Settings') or role == 'Administrator':
        nav_links += f"""
            <div class="pt-2 pb-1 px-4 text-[10px] font-bold uppercase tracking-wider text-slate-500">Dynamic Lookups</div>
            {nav_link("/profile-types", "Customer Profiles", "Settings")}
            {nav_link("/service-types", "Service Types", "Settings")}
            {nav_link("/expense-categories", "Expense Categories", "Settings")}
            {nav_link("/payment-statuses", "Payment Statuses", "Settings")}
            {nav_link("/commission-types", "Commission Types", "Settings")}
            {nav_link("/supplier-types", "Supplier Types", "Settings")}
            {nav_link("/currencies", "Currencies", "Settings")}
        """

    if role == 'Administrator':
        nav_links += f"""
            <div class="pt-2 pb-1 px-4 text-[10px] font-bold uppercase tracking-wider text-slate-500">Administration</div>
            {nav_link("/admin/users", "Users Management", "Dashboard")}
            {nav_link("/admin/permissions", "Permissions Matrix", "Dashboard")}
            {nav_link("/admin/logs", "Activity Logs", "Dashboard")}
        """

    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>{title} - Velora Travel</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <script>
                tailwind.config = {{ darkMode: 'class' }}
                // Apply dark theme instantly before page paints to prevent white flash
                if (localStorage.getItem('theme') === 'dark') {{
                    document.documentElement.classList.add('dark');
                }}
            </script>
            <style>
                .no-scrollbar::-webkit-scrollbar {{ display: none; }}
                .no-scrollbar {{ -ms-overflow-style: none; scrollbar-width: none; }}
                
                @media print {{
                    aside, header, .print\:hidden {{
                        display: none !important;
                    }}
                    body {{
                        background-color: #ffffff !important;
                        color: #1e293b !important;
                    }}
                    #invoice-card {{
                        background-color: #ffffff !important;
                        color: #1e293b !important;
                        box-shadow: none !important;
                        border: none !important;
                    }}
                }}
            </style>
            <script>
                document.addEventListener('DOMContentLoaded', () => {{
                    const currentTheme = localStorage.getItem('theme') || 'light';
                    if (currentTheme === 'dark') {{
                        document.documentElement.classList.add('dark');
                    }}
                    
                    const currentPath = window.location.pathname;
                    document.querySelectorAll('.nav-link-item').forEach(el => {{
                        if (el.getAttribute('href') === currentPath) {{
                            el.classList.add('bg-blue-600', 'text-white', 'shadow-sm');
                            el.classList.remove('text-slate-300', 'hover:bg-slate-800');
                        }}
                    }});
                }});

function toggleTheme() {{
                    if (document.documentElement.classList.contains('dark')) {{
                        document.documentElement.classList.remove('dark');
                        localStorage.setItem('theme', 'light');
                    }} else {{
                        document.documentElement.classList.add('dark');
                        localStorage.setItem('theme', 'dark');
                    }}
                    fetch('/api/log-theme', {{ method: 'POST' }});
                }}
            </script>
        </head>
        <body class="bg-slate-50 dark:bg-slate-950 font-sans text-slate-800 dark:text-slate-100 flex h-screen overflow-hidden transition-colors duration-200">
            <aside class="w-64 bg-slate-900 text-slate-300 flex flex-col shadow-xl print:hidden">
                <div class="p-6 text-2xl font-bold text-white tracking-wider border-b border-slate-800">
                    ✈️ Velora Travel
                </div>
                <nav class="flex-1 p-4 space-y-1 overflow-y-auto no-scrollbar">
                    {nav_links}
                </nav>
                <div class="p-4 border-t border-slate-800 bg-slate-950 flex justify-between items-center text-xs">
                    <span class="text-white font-semibold truncate">👤 {username}</span>
                    <a href="/logout" onclick="return confirm('Are you sure you want to logout?');" class="text-rose-400 hover:text-rose-300 font-medium transition">Logout</a>
                </div>
            </aside>
            <main class="flex-1 flex flex-col overflow-y-auto">
                <header class="bg-white dark:bg-slate-900 shadow-sm border-b border-slate-200 dark:border-slate-800 px-8 py-4 flex justify-between items-center print:hidden">
                    <h1 class="text-xl font-semibold text-slate-800 dark:text-white">{title}</h1>
                    <div class="space-x-3 flex items-center">
                        <button onclick="toggleTheme()" class="bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-medium px-3 py-2 rounded-lg transition">🌙 Theme</button>
                        <a href="/reports/print-pnl" class="bg-slate-800 dark:bg-slate-700 hover:bg-slate-900 text-white text-xs font-medium px-4 py-2 rounded-lg transition">View P&L Report</a>
                    </div>
                </header>
                <div class="p-8 flex-1">
                    {content}
                </div>
            </main>
        </body>
        </html>
    """

# ==================== AUTHENTICATION ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            session['username'] = user['username']
            session['user_role'] = user['role_name']
            log_activity('LOGIN', f"User {username} signed in successfully.")
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password."
            
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head><meta charset="UTF-8"><title>Login - Velora Travel</title><script src="https://cdn.tailwindcss.com"></script></head>
        <body class="bg-slate-950 font-sans flex items-center justify-center h-screen">
            <div class="bg-white p-8 rounded-2xl shadow-xl w-96 border border-slate-800">
                <h2 class="text-2xl font-bold text-slate-900 mb-2 text-center">✈️ Velora Travel</h2>
                <p class="text-xs text-slate-500 text-center mb-6">Enter your credentials to access portal</p>
                {% if error %}<div class="bg-rose-50 text-rose-700 p-3 rounded-lg text-xs mb-4 font-medium">{{ error }}</div>{% endif %}
                <form method="POST" class="space-y-4">
                    <div><label class="block text-xs font-medium text-slate-700 mb-1">Username</label><input type="text" name="username" required class="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"></div>
                    <div><label class="block text-xs font-medium text-slate-700 mb-1">Password</label><input type="password" name="password" required class="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-600 focus:outline-none"></div>
                    <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg transition text-sm">Sign In</button>
                </form>
            </div>
        </body>
        </html>
    """, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.before_request
def require_login():
    if request.endpoint not in ['login'] and not request.path.startswith('/static'):
        if 'username' not in session:
            return redirect(url_for('login'))
@app.before_request
def log_page_visits():
    if 'username' in session and request.method == 'GET':
        # Map routes to friendly names for your logs
        path_names = {
            '/': 'Dashboard',
            '/bookings': 'Sales & Bookings',
            '/ticketing': 'Airline Ticketing',
            '/invoices': 'Invoices & AR',
            '/customers': 'Customers',
            '/suppliers': 'Suppliers',
            '/expenses': 'Expenses',
            '/commissions': 'Commissions',
            '/profile-types': 'Customer Profiles',
            '/service-types': 'Service Types',
            '/expense-categories': 'Expense Categories',
            '/payment-statuses': 'Payment Statuses',
            '/commission-types': 'Commission Types',
            '/supplier-types': 'Supplier Types',
            '/currencies': 'Currencies',
            '/admin/users': 'Users Management',
            '/admin/permissions': 'Permissions Matrix',
            '/admin/logs': 'Activity Logs',
            '/reports/print-pnl': 'Financial P&L Report'
        }
        
        page_name = path_names.get(request.path)
        if page_name:
            log_activity('PAGE_VIEW', f"Visited {page_name} page")
# ==================== ADMIN & USERS ====================

@app.route('/admin/logs')
def admin_logs():
    if session.get('user_role') != 'Administrator':
        return "Access Denied", 403
        
    conn = get_db_connection()
    
    # Get filter values from request args, or set defaults for today (00:00 to 23:59) if first load
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    from_dt = request.args.get('from_dt', f"{today_str}T00:00")
    to_dt = request.args.get('to_dt', f"{today_str}T23:59")
    selected_users = request.args.getlist('users')
    selected_actions = request.args.getlist('actions')
    export_excel = request.args.get('export') == 'excel'
    
    # Fetch distinct users and actions for filter options
    all_users = conn.execute('SELECT DISTINCT username FROM activity_logs ORDER BY username').fetchall()
    all_actions = conn.execute('SELECT DISTINCT action FROM activity_logs ORDER BY action').fetchall()
    
    # Build dynamic SQL query based on filters
    query = 'SELECT * FROM activity_logs WHERE 1=1'
    params = []
    
    if from_dt:
        query += ' AND timestamp >= ?'
        params.append(from_dt.replace('T', ' '))
    if to_dt:
        query += ' AND timestamp <= ?'
        params.append(to_dt.replace('T', ' '))
    if selected_users:
        placeholders = ','.join(['?'] * len(selected_users))
        query += f' AND username IN ({placeholders})'
        params.extend(selected_users)
    if selected_actions:
        placeholders = ','.join(['?'] * len(selected_actions))
        query += f' AND action IN ({placeholders})'
        params.extend(selected_actions)
        
    query += ' ORDER BY id DESC'
    
    if not export_excel:
        query += ' LIMIT 200'
        
    logs = conn.execute(query, params).fetchall()
    conn.close()
    
    # Handle Excel export via CSV response download
    if export_excel:
        import csv
        import io
        from flask import Response
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Timestamp', 'User', 'Action', 'Details'])
        
        for l in logs:
            writer.writerow([l['id'], l['timestamp'], l['username'], l['action'], l['details'].replace('<br>', ' - ')])
            
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=activity_logs_export.csv"}
        )
    
    # Render table rows
    rows = ""
    for l in logs:
        rows += f"""
            <tr class="border-b dark:border-slate-800 text-sm hover:bg-slate-50 dark:hover:bg-slate-900">
                <td class="py-3 px-4 text-slate-500 font-mono text-xs">{l["timestamp"]}</td>
                <td class="py-3 px-4 font-semibold">{l["username"]}</td>
                <td class="py-3 px-4"><span class="bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded text-xs font-medium">{l["action"]}</span></td>
                <td class="py-3 px-4 text-slate-600 dark:text-slate-300">{l["details"]}</td>
            </tr>
        """
        
    # Generate multi-select checkboxes for Users and Actions
    user_checkboxes = ""
    for u in all_users:
        uname = u["username"]
        checked = "checked" if uname in selected_users else ""
        user_checkboxes += f"""
            <label class="flex items-center space-x-2 text-xs cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 p-1 rounded">
                <input type="checkbox" name="users" value="{uname}" {checked} class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-3.5 w-3.5">
                <span class="text-slate-700 dark:text-slate-300">{uname}</span>
            </label>
        """
        
    action_checkboxes = ""
    for a in all_actions:
        act = a["action"]
        checked = "checked" if act in selected_actions else ""
        action_checkboxes += f"""
            <label class="flex items-center space-x-2 text-xs cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 p-1 rounded">
                <input type="checkbox" name="actions" value="{act}" {checked} class="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-3.5 w-3.5">
                <span class="text-slate-700 dark:text-slate-300">{act}</span>
            </label>
        """
    
    content = f"""
        <div class="space-y-6">
            <!-- Filter Form Bar -->
            <form method="GET" class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800 space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">From Date & Time</label>
                        <input type="datetime-local" name="from_dt" value="{from_dt}" onclick="this.showPicker && this.showPicker();" class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-xs cursor-pointer">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">To Date & Time</label>
                        <input type="datetime-local" name="to_dt" value="{to_dt}" onclick="this.showPicker && this.showPicker();" class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-xs cursor-pointer">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Users</label>
                        <div class="max-h-32 overflow-y-auto no-scrollbar border dark:border-slate-700 rounded-lg p-2 space-y-1 bg-slate-50 dark:bg-slate-950">
                            {user_checkboxes if user_checkboxes else '<span class="text-xs text-slate-400">No users found</span>'}
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-500 mb-1">Actions</label>
                        <div class="max-h-32 overflow-y-auto no-scrollbar border dark:border-slate-700 rounded-lg p-2 space-y-1 bg-slate-50 dark:bg-slate-950">
                            {action_checkboxes if action_checkboxes else '<span class="text-xs text-slate-400">No actions found</span>'}
                        </div>
                    </div>
                </div>
                <div class="flex justify-between items-center pt-2 border-t dark:border-slate-800">
                    <div class="flex gap-2">
                        <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2 rounded-lg text-xs transition">Apply Filters</button>
                        <a href="/admin/logs" class="bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium px-4 py-2 rounded-lg text-xs transition">Reset</a>
                    </div>
                    <div>
                        <button type="submit" name="export" value="excel" class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2 rounded-lg text-xs transition">📥 Export to Excel (CSV)</button>
                    </div>
                </div>
            </form>

            <!-- Logs Table -->
            <div class="bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden">
                <table class="w-full text-left">
                    <thead>
                        <tr class="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-500 uppercase">
                            <th class="py-3 px-4">Timestamp</th>
                            <th class="py-3 px-4">User</th>
                            <th class="py-3 px-4">Action</th>
                            <th class="py-3 px-4">Details</th>
                        </tr>
                    </thead>
                    <tbody>{rows if rows else '<tr><td colspan="4" class="py-6 text-center text-slate-400">No activity logs match your filter criteria.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
    """
    return render_layout("System Activity Logs", content)


@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if session.get('user_role') != 'Administrator':
        return "Access Denied", 403
    conn = get_db_connection()
    if request.method == 'POST':
        current_user = session.get('username', 'System')
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if 'delete_id' in request.form:
            del_id = request.form['delete_id']
            old_user = conn.execute('SELECT * FROM users WHERE id = ?', (del_id,)).fetchone()
            conn.execute('DELETE FROM users WHERE id = ?', (del_id,))
            
            if old_user:
                old_dict = dict(old_user)
                u_id = old_dict.get('id', del_id)
                u_name = old_dict.get('username', 'Unknown')
                u_role = old_dict.get('role_name', 'None')
                
                detail_msg = f"Deleted user ID #{u_id} | Name: {u_name} | Role: {u_role}"
            else:
                detail_msg = f"Deleted user ID {del_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (current_user, 'DELETE_USER', detail_msg, timestamp))
                         
        elif 'edit_id' in request.form:
            user_id = request.form['edit_id']
            uname = request.form['username'].strip()
            role = request.form['role_name']
            pwd = request.form['password'].strip()
            
            old_user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            old_dict = dict(old_user) if old_user else {}
            
            if pwd:
                pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()
                conn.execute('UPDATE users SET username = ?, password = ?, role_name = ? WHERE id = ?', (uname, pwd_hash, role, user_id))
            else:
                conn.execute('UPDATE users SET username = ?, role_name = ? WHERE id = ?', (uname, role, user_id))
                
            old_name = old_dict.get('username', 'Unknown')
            old_role = old_dict.get('role_name', 'Unknown')
            
            detail_msg = (
                f"<b>Updated user ID #{user_id}</b><br>"
                f"Username: {old_name} -> {uname}<br>"
                f"Role: {old_role} -> {role}"
            )
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (current_user, 'EDIT_USER', detail_msg, timestamp))
        else:
            uname = request.form['username'].strip()
            pwd = hashlib.sha256(request.form['password'].encode()).hexdigest()
            role = request.form['role_name']
            try: 
                conn.execute('INSERT INTO users (username, password, role_name) VALUES (?, ?, ?)', (uname, pwd, role))
                detail_msg = f"Created user: {uname} with role {role}"
                conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                             (current_user, 'ADD_USER', detail_msg, timestamp))
            except sqlite3.IntegrityError: 
                pass
                
        conn.commit()
        conn.close()
        return redirect(url_for('admin_users'))
    users = conn.execute('SELECT * FROM users').fetchall()
    roles = conn.execute('SELECT DISTINCT role_name FROM permissions').fetchall()
    conn.close()
    role_opts = ''.join([f'<option value="{r["role_name"]}">{r["role_name"]}</option>' for r in roles])
    
    edit_id = request.args.get('edit', type=int)
    rows = ""
    for u in users:
        if edit_id == u['id']:
            eroles = ''.join([f'<option value="{r["role_name"]}" {"selected" if r["role_name"]==u["role_name"] else ""}>{r["role_name"]}</option>' for r in roles])
            rows += f'<tr class="border-b text-sm bg-blue-50 dark:bg-slate-800"><form method="POST"><input type="hidden" name="edit_id" value="{u["id"]}"><td class="py-3 px-4"><input type="text" name="username" value="{u["username"]}" required class="border rounded px-2 py-1 text-sm bg-white dark:bg-slate-900 text-slate-900 dark:text-white w-full"></td><td class="py-3 px-4"><input type="password" name="password" placeholder="New pwd" class="border rounded px-2 py-1 text-sm bg-white dark:bg-slate-900 text-slate-900 dark:text-white w-full"></td><td class="py-3 px-4"><select name="role_name" class="border rounded px-2 py-1 text-sm bg-white dark:bg-slate-900 text-slate-900 dark:text-white w-full">{eroles}</select></td><td class="py-3 px-4 text-right space-x-2"><button type="submit" class="text-emerald-600 font-medium text-xs bg-emerald-50 px-2 py-1 rounded">Save</button><a href="/admin/users" class="text-slate-500 text-xs">Cancel</a></td></form></tr>'
        else:
            rows += f'<tr class="border-b text-sm hover:bg-slate-50 dark:hover:bg-slate-900"><td class="py-3 px-4 font-semibold">{u["username"]}</td><td class="py-3 px-4 text-slate-400">••••••••</td><td class="py-3 px-4"><span class="bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded text-xs">{u["role_name"]}</span></td><td class="py-3 px-4 text-right space-x-3"><a href="/admin/users?edit={u["id"]}" class="text-blue-600 text-xs font-medium">Edit</a><form method="POST" style="display:inline;" onsubmit="return confirm(\'Delete?\');"><input type="hidden" name="delete_id" value="{u["id"]}"><button type="submit" class="text-red-600 text-xs font-medium">Delete</button></form></td></tr>'
            
    content = f"""
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800 h-fit">
                <h3 class="text-lg font-medium mb-4">Create New User</h3>
                <form method="POST" class="space-y-4">
                    <div><label class="block text-sm mb-1">Username</label><input type="text" name="username" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div><label class="block text-sm mb-1">Password</label><input type="password" name="password" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div><label class="block text-sm mb-1">Assign Role</label><select name="role_name" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">{role_opts}</select></div>
                    <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Create User</button>
                </form>
            </div>
            <div class="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden h-fit">
                <table class="w-full text-left">
                    <thead><tr class="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-500 uppercase"><th class="py-3 px-4">Username</th><th class="py-3 px-4">Password</th><th class="py-3 px-4">Role</th><th class="py-3 px-4 text-right">Action</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="4" class="py-6 text-center text-slate-400">No users.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
    """
    return render_layout("Users Management", content)

@app.route('/admin/permissions', methods=['GET', 'POST'])
def admin_permissions():
    if session.get('user_role') != 'Administrator':
        return "Access Denied", 403
    conn = get_db_connection()
    target_redirect = 'Administrator'
    
    if request.method == 'POST':
        if 'new_role' in request.form:
            nr = request.form['new_role'].strip()
            if nr:
                for m in ['Dashboard', 'Bookings', 'Ticketing', 'Invoices', 'Customers', 'Suppliers', 'Expenses', 'Commissions', 'Settings']:
                    try: conn.execute('INSERT INTO permissions (role_name, module_name, can_view, can_add, can_edit, can_delete) VALUES (?, ?, 0, 0, 0, 0)', (nr, m))
                    except sqlite3.IntegrityError: pass
                target_redirect = nr
        elif 'delete_role' in request.form:
            rd = request.form['delete_role']
            if rd != 'Administrator':
                conn.execute('DELETE FROM permissions WHERE role_name = ?', (rd,))
                conn.execute('UPDATE users SET role_name = "Administrator" WHERE role_name = ?', (rd,))
            target_redirect = 'Administrator'
        else:
            target = request.form.get('target_role')
            if target:
                # Fetch old permissions before updating
                old_perms_raw = conn.execute('SELECT * FROM permissions WHERE role_name = ?', (target,)).fetchall()
                old_matrix = {p['module_name']: {'view': p['can_view'], 'add': p['can_add'], 'edit': p['can_edit'], 'delete': p['can_delete']} for p in old_perms_raw}
                
                conn.execute('UPDATE permissions SET can_view=0, can_add=0, can_edit=0, can_delete=0 WHERE role_name=?', (target,))
                
                changes_summary = []
                modules_list = conn.execute('SELECT DISTINCT module_name FROM permissions').fetchall()
                
                for m in modules_list:
                    mod = m['module_name']
                    v = 1 if request.form.get(f'view_{mod}') == 'on' else 0
                    a = 1 if request.form.get(f'add_{mod}') == 'on' else 0
                    e = 1 if request.form.get(f'edit_{mod}') == 'on' else 0
                    d = 1 if request.form.get(f'delete_{mod}') == 'on' else 0
                    
                    conn.execute('UPDATE permissions SET can_view=?, can_add=?, can_edit=?, can_delete=? WHERE role_name=? AND module_name=?', (v, a, e, d, target, mod))
                    
                    old_p = old_matrix.get(mod, {'view': 0, 'add': 0, 'edit': 0, 'delete': 0})
                    if old_p['view'] != v or old_p['add'] != a or old_p['edit'] != e or old_p['delete'] != d:
                        changes_summary.append(
                            f"<b>{mod}</b>: "
                            f"V({old_p['view']}->{v}) | "
                            f"A({old_p['add']}->{a}) | "
                            f"E({old_p['edit']}->{e}) | "
                            f"D({old_p['delete']}->{d})"
                        )
                
                if changes_summary:
                    current_user = session.get('username', 'System')
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    detail_msg = f"<b>Updated permissions for role: {target}</b><br>" + "<br>".join(changes_summary)
                    conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                                 (current_user, 'EDIT_PERMISSIONS', detail_msg, timestamp))
                                 
                target_redirect = target
        conn.commit()
        conn.close()
        return redirect(url_for('admin_permissions', role=target_redirect))
        
    roles = conn.execute('SELECT DISTINCT role_name FROM permissions').fetchall()
    srole = request.args.get('role', roles[0]['role_name'] if roles else 'Administrator')
    perms = conn.execute('SELECT * FROM permissions WHERE role_name = ?', (srole,)).fetchall()
    modules = conn.execute('SELECT DISTINCT module_name FROM permissions').fetchall()
    conn.close()
    matrix = {p['module_name']: p for p in perms}
    ropts = ''.join([f'<option value="{r["role_name"]}" {"selected" if r["role_name"]==srole else ""}>{r["role_name"]}</option>' for r in roles])
    
    body_rows = ""
    for m in modules:
        mn = m['module_name']
        p = matrix.get(mn, {'can_view':0, 'can_add':0, 'can_edit':0, 'can_delete':0})
        ac = "checked" if (p['can_view'] and p['can_add'] and p['can_edit'] and p['can_delete']) else ""
        body_rows += f'<tr class="border-b dark:border-slate-800 text-sm hover:bg-slate-50 dark:hover:bg-slate-900"><td class="py-3 px-4 font-semibold">{mn}</td><td class="py-3 px-2 text-center border-l dark:border-slate-800"><input type="checkbox" name="view_{mn}" {"checked" if p["can_view"] else ""} class="cls-role h-4 w-4"></td><td class="py-3 px-2 text-center"><input type="checkbox" name="add_{mn}" {"checked" if p["can_add"] else ""} class="cls-role h-4 w-4"></td><td class="py-3 px-2 text-center"><input type="checkbox" name="edit_{mn}" {"checked" if p["can_edit"] else ""} class="cls-role h-4 w-4"></td><td class="py-3 px-2 text-center"><input type="checkbox" name="delete_{mn}" {"checked" if p["can_delete"] else ""} class="cls-role h-4 w-4"></td><td class="py-3 px-2 text-center border-r dark:border-slate-800 bg-slate-50 dark:bg-slate-800"><input type="checkbox" {ac} onclick="toggleRow(this)" class="h-4 w-4"></td></tr>'
        
    content = f"""
        <script>function toggleRow(m) {{ m.closest('tr').querySelectorAll('.cls-role').forEach(cb => cb.checked = m.checked); }}</script>
        <div class="space-y-6 max-w-4xl">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800">
                    <h3 class="text-lg font-medium mb-3">Create New Role</h3>
                    <form method="POST" class="flex gap-2"><input type="text" name="new_role" required placeholder="Role Name" class="flex-1 border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">Add</button></form>
                </div>
                <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800">
                    <h3 class="text-lg font-medium mb-3">Configure Role</h3>
                    <form method="GET" class="flex gap-2"><select name="role" onchange="this.form.submit()" class="flex-1 border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">{ropts}</select></form>
                </div>
            </div>
            {f'<div class="flex justify-end">{f"<form method=\'POST\' onsubmit=\'return confirm(\\\"Delete role?\\\");\'><input type=\'hidden\' name=\'delete_role\' value=\'" + srole + "\'><button type=\'submit\' class=\'bg-rose-600 hover:bg-rose-700 text-white font-medium px-4 py-2 rounded-lg text-xs transition\'>Delete Role</button></form>" if srole != "Administrator" else ""}</div>' if srole and srole != "Administrator" else ""}
            <div class="bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden">
                <form method="POST"><input type="hidden" name="target_role" value="{srole}">
                    <table class="w-full text-left border-collapse">
                        <thead><tr class="bg-slate-100 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300 uppercase"><th class="py-3 px-4">Page</th><th class="py-3 px-2 text-center border-l dark:border-slate-700 w-20">View</th><th class="py-3 px-2 text-center w-20">Add</th><th class="py-3 px-2 text-center w-20">Edit</th><th class="py-3 px-2 text-center w-20">Del</th><th class="py-3 px-4 text-center border-r dark:border-slate-700 bg-slate-200 dark:bg-slate-700 w-20">All</th></tr></thead>
                        <tbody>{body_rows}</tbody>
                    </table>
                    <div class="p-4 bg-slate-50 dark:bg-slate-800 border-t dark:border-slate-700 flex justify-end"><button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-6 py-2 rounded-lg text-sm">Save Permissions</button></div>
                </form>
            </div>
        </div>
    """
    return render_layout("Permissions Matrix", content)

# ==================== CORE ROUTES WITH PERMISSION GUARDS ====================

@app.route('/')
def index():
    if not check_permission('Dashboard', 'view'): return "Access Denied", 403
    conn = get_db_connection()
    book_count = conn.execute('SELECT COUNT(*) FROM bookings').fetchone()[0]
    cust_count = conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
    supp_count = conn.execute('SELECT COUNT(*) FROM suppliers').fetchone()[0]
    inv_count = conn.execute('SELECT COUNT(*) FROM invoices').fetchone()[0]
    
    ts = conn.execute('SELECT SUM(selling_price_iqd) FROM bookings').fetchone()[0] or 0
    tp = conn.execute('SELECT SUM(amount_payable_iqd) FROM suppliers').fetchone()[0] or 0
    te = conn.execute('SELECT SUM(amount_iqd) FROM expenses').fetchone()[0] or 0
    tc = conn.execute('SELECT SUM(amount_iqd) FROM commissions').fetchone()[0] or 0
    net = (ts + tc) - te
    conn.close()

    content = f"""
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800"><p class="text-sm font-medium text-slate-500">Total Bookings</p><p class="text-3xl font-bold mt-2">{book_count}</p></div>
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800"><p class="text-sm font-medium text-slate-500">Invoices Issued</p><p class="text-3xl font-bold mt-2">{inv_count}</p></div>
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800"><p class="text-sm font-medium text-slate-500">Registered Customers</p><p class="text-3xl font-bold mt-2">{cust_count}</p></div>
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800"><p class="text-sm font-medium text-slate-500">Active Suppliers</p><p class="text-3xl font-bold mt-2">{supp_count}</p></div>
        </div>
        <h3 class="text-lg font-semibold mb-4">Financial & P&L Overview (IQD)</h3>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 p-6 rounded-xl"><p class="text-sm font-medium text-emerald-600">Total Sales</p><p class="text-2xl font-bold text-emerald-900 dark:text-emerald-200 mt-2">{ts:,.0f} IQD</p></div>
            <div class="bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 p-6 rounded-xl"><p class="text-sm font-medium text-rose-600">Total Expenses</p><p class="text-2xl font-bold text-rose-900 dark:text-rose-200 mt-2">{te:,.0f} IQD</p></div>
            <div class="bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900 p-6 rounded-xl"><p class="text-sm font-medium text-indigo-600">Net Profit</p><p class="text-2xl font-bold text-indigo-900 dark:text-indigo-200 mt-2">{net:,.0f} IQD</p></div>
            <div class="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 p-6 rounded-xl"><p class="text-sm font-medium text-amber-600">Supplier Payables</p><p class="text-2xl font-bold text-amber-900 dark:text-amber-200 mt-2">{tp:,.0f} IQD</p></div>
        </div>
    """
    return render_layout("Dashboard & Financials", content)

@app.route('/reports/print-pnl')
def print_pnl():
    if not check_permission('Dashboard', 'view'): 
        return "Access Denied", 403
        
    conn = get_db_connection()
    ts = conn.execute('SELECT SUM(selling_price_iqd) FROM bookings').fetchone()[0] or 0
    te = conn.execute('SELECT SUM(amount_iqd) FROM expenses').fetchone()[0] or 0
    tc = conn.execute('SELECT SUM(amount_iqd) FROM commissions').fetchone()[0] or 0
    net = (ts + tc) - te
    conn.close()
    
    content = f"""
        <div class="max-w-4xl mx-auto space-y-6">
            <div class="bg-white dark:bg-slate-900 p-8 rounded-xl shadow-sm border dark:border-slate-800">
                <div class="flex justify-between items-center border-b dark:border-slate-800 pb-6 mb-6">
                    <div>
                        <h2 class="text-2xl font-bold">✈️ Velora Travel Agency</h2>
                        <p class="text-sm text-slate-500 mt-1">Official Profit & Loss Statement</p>
                    </div>
                    <div class="text-right">
                        <p class="text-xs text-slate-500">Generated: <b>{datetime.date.today()}</b></p>
                        <p class="text-xs text-slate-500">Erbil Headquarters</p>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 text-center">
                    <div class="bg-slate-50 dark:bg-slate-800 p-6 rounded-xl border dark:border-slate-700">
                        <p class="text-xs text-slate-500 uppercase tracking-wider font-semibold">Total Sales</p>
                        <p class="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-2">{ts:,.0f} IQD</p>
                    </div>
                    <div class="bg-slate-50 dark:bg-slate-800 p-6 rounded-xl border dark:border-slate-700">
                        <p class="text-xs text-slate-500 uppercase tracking-wider font-semibold">Total Expenses</p>
                        <p class="text-xl font-bold text-rose-600 dark:text-rose-400 mt-2">{te:,.0f} IQD</p>
                    </div>
                    <div class="bg-slate-50 dark:bg-slate-800 p-6 rounded-xl border dark:border-slate-700">
                        <p class="text-xs text-slate-500 uppercase tracking-wider font-semibold">Net Profit</p>
                        <p class="text-xl font-bold text-indigo-600 dark:text-indigo-400 mt-2">{net:,.0f} IQD</p>
                    </div>
                </div>

                <div class="flex justify-end gap-3 print:hidden">
                    <button onclick="window.print();" class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-lg text-sm transition">Print Statement</button>
                </div>
            </div>
        </div>
    """
    return render_layout("Financial P&L Statement", content)

@app.route('/profile-types', methods=['GET', 'POST'])
def profile_types(): return generic_lookup_route('profile_types', 'Customer Profile')

@app.route('/service-types', methods=['GET', 'POST'])
def service_types(): return generic_lookup_route('service_types', 'Service Type')

@app.route('/expense-categories', methods=['GET', 'POST'])
def expense_categories(): return generic_lookup_route('expense_categories', 'Expense Category')

@app.route('/payment-statuses', methods=['GET', 'POST'])
def payment_statuses(): return generic_lookup_route('payment_statuses', 'Payment Status')

@app.route('/commission-types', methods=['GET', 'POST'])
def commission_types(): return generic_lookup_route('commission_types', 'Commission Type')

@app.route('/supplier-types', methods=['GET', 'POST'])
def supplier_types(): return generic_lookup_route('supplier_types', 'Supplier Type')

@app.route('/currencies', methods=['GET', 'POST'])
def currencies():
    if not check_permission('Settings', 'view'): return "Access Denied", 403
    can_add = check_permission('Settings', 'add')
    can_del = check_permission('Settings', 'delete')
    
    conn = get_db_connection()
    if request.method == 'POST':
        username = session.get('username', 'System')
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if 'delete_id' in request.form:
            if not can_del: return "Access Denied", 403
            del_id = request.form['delete_id']
            
            old_item = conn.execute('SELECT * FROM currencies WHERE id = ?', (del_id,)).fetchone()
            conn.execute('DELETE FROM currencies WHERE id = ?', (del_id,))
            
            if old_item:
                item_val = old_item['code'] if 'code' in old_item.keys() and old_item['code'] else 'Unknown'
                detail_msg = f"Deleted Currency: {item_val}"
            else:
                detail_msg = f"Deleted Currency ID {del_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'DELETE_CURRENCIES', detail_msg, timestamp))
        else:
            if not can_add: return "Access Denied", 403
            code_val = request.form.get('code', '').strip().upper()
            if code_val:
                try:
                    conn.execute('INSERT INTO currencies (code, name) VALUES (?, ?)', (code_val, code_val))
                    
                    detail_msg = f"Added Currency: {code_val}"
                    conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                                 (username, 'ADD_CURRENCIES', detail_msg, timestamp))
                except sqlite3.IntegrityError: 
                    pass
                    
        conn.commit()
        conn.close()
        return redirect(url_for('currencies'))
        
    items = conn.execute('SELECT * FROM currencies').fetchall()
    conn.close()
    
    rows = ""
    for item in items:
        db_btn = f'<form method="POST" style="display:inline;" onsubmit="return confirm(\'Delete?\');"><input type="hidden" name="delete_id" value="{item["id"]}"><button type="submit" class="text-red-600 text-xs font-medium">Delete</button></form>' if can_del else ''
        rows += f'<tr class="border-b dark:border-slate-800"><td class="py-3 px-4 font-semibold">{item["code"]}</td><td class="py-3 px-4 text-right">{db_btn}</td></tr>'
        
    add_form = f'<div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800 h-fit"><h3 class="text-lg font-medium mb-4">Add Currency</h3><form method="POST" class="space-y-4"><div><label class="block text-sm mb-1">Currency Code (e.g. USD)</label><input type="text" name="code" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm uppercase"></div><button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Add Currency</button></form></div>' if can_add else ''
    
    content = f"""
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {add_form}
            <div class="{'lg:col-span-2' if can_add else 'lg:col-span-3'} bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden h-fit">
                <table class="w-full text-left"><thead><tr class="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-500 uppercase"><th class="py-3 px-4">Code</th><th class="py-3 px-4 text-right">Action</th></tr></thead><tbody>{rows if rows else '<tr><td colspan="2" class="py-6 text-center text-slate-400">No currencies.</td></tr>'}</tbody></table>
            </div>
        </div>
    """
    return render_layout("Currencies Management", content)

def generic_lookup_route(table_name, page_title):
    if not check_permission('Settings', 'view'): return "Access Denied", 403
    can_add = check_permission('Settings', 'add')
    can_del = check_permission('Settings', 'delete')
    
    conn = get_db_connection()
    if request.method == 'POST':
        username = session.get('username', 'System')
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if 'delete_id' in request.form:
            if not can_del: return "Access Denied", 403
            del_id = request.form['delete_id']
            
            old_item = conn.execute(f'SELECT * FROM {table_name} WHERE id = ?', (del_id,)).fetchone()
            conn.execute(f'DELETE FROM {table_name} WHERE id = ?', (del_id,))
            
            if old_item:
                keys = old_item.keys()
                if 'code' in keys and old_item['code']:
                    item_val = old_item['code']
                elif 'name' in keys and old_item['name']:
                    item_val = old_item['name']
                else:
                    item_val = 'Unknown'
                detail_msg = f"Deleted {page_title}: {item_val}"
            else:
                detail_msg = f"Deleted {page_title} ID {del_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, f'DELETE_{table_name.upper()}', detail_msg, timestamp))
        else:
            if not can_add: return "Access Denied", 403
            val = request.form.get('name', '').strip()
            if val:
                try:
                    col_name = 'code' if table_name == 'currencies' else 'name'
                    insert_val = val.upper() if table_name == 'currencies' else val
                    conn.execute(f'INSERT INTO {table_name} ({col_name}) VALUES (?)', (insert_val,))
                    
                    detail_msg = f"Added {page_title}: {insert_val}"
                    conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                                 (username, f'ADD_{table_name.upper()}', detail_msg, timestamp))
                except sqlite3.IntegrityError: 
                    pass
                    
        conn.commit()
        conn.close()
        return redirect(url_for(table_name))
        
    items = conn.execute(f'SELECT * FROM {table_name}').fetchall()
    conn.close()
    
    rows = ""
    for item in items:
        display_val = item['code'] if table_name == 'currencies' else item['name']
        db_btn = f'<form method="POST" style="display:inline;" onsubmit="return confirm(\'Delete?\');"><input type="hidden" name="delete_id" value="{item["id"]}"><button type="submit" class="text-red-600 text-xs font-medium">Delete</button></form>' if can_del else ''
        rows += f'<tr class="border-b dark:border-slate-800"><td class="py-3 px-4 font-semibold">{display_val}</td><td class="py-3 px-4 text-right">{db_btn}</td></tr>'
        
    add_form = f'<div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800 h-fit"><h3 class="text-lg font-medium mb-4">Add {page_title}</h3><form method="POST" class="space-y-4"><div><label class="block text-sm mb-1">{"Currency Code (e.g. USD)" if table_name=="currencies" else "Name"}</label><input type="text" name="name" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div><button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Add Entry</button></form></div>' if can_add else ''
    
    content = f"""
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {add_form}
            <div class="{'lg:col-span-2' if can_add else 'lg:col-span-3'} bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden h-fit">
                <table class="w-full text-left"><thead><tr class="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-500 uppercase"><th class="py-3 px-4">Name</th><th class="py-3 px-4 text-right">Action</th></tr></thead><tbody>{rows if rows else '<tr><td colspan="2" class="py-6 text-center text-slate-400">No records.</td></tr>'}</tbody></table>
            </div>
        </div>
    """
    return render_layout(f"{page_title} Management", content)

# ==================== MODULES ====================

@app.route('/ticketing', methods=['GET', 'POST'])
def ticketing():
    if not check_permission('Ticketing', 'view'): return "Access Denied", 403
    can_add = check_permission('Ticketing', 'add')
    can_edit = check_permission('Ticketing', 'edit') if 'check_permission' in globals() else can_add
    can_del = check_permission('Ticketing', 'delete')
    
    conn = get_db_connection()
    if request.method == 'POST':
        if 'delete_id' in request.form:
            if not can_del: return "Access Denied", 403
            t_id = request.form['delete_id']
            
            ticket_to_del = conn.execute('SELECT * FROM ticketing WHERE id = ?', (t_id,)).fetchone()
            conn.execute('DELETE FROM ticketing WHERE id = ?', (t_id,))
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            curr = ticket_to_del['currency'] if 'currency' in ticket_to_del.keys() and ticket_to_del['currency'] else 'IQD'
            if ticket_to_del:
                detail_msg = (
                    f"Deleted ticket ID #{t_id} | "
                    f"PNR: {ticket_to_del['pnr'] or 'N/A'} | "
                    f"Ticket #: {ticket_to_del['ticket_number'] or 'N/A'} | "
                    f"Passenger: {ticket_to_del['passenger_name']} | "
                    f"Cost: {float(ticket_to_del['cost_iqd']):,.2f} {curr}"
                )
            else:
                detail_msg = f"Deleted ticket ID {t_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'DELETE_TICKET', detail_msg, timestamp))
                         
        elif 'edit_id' in request.form:
            t_id = request.form['edit_id']
            old_ticket = conn.execute('SELECT * FROM ticketing WHERE id = ?', (t_id,)).fetchone()
            
            pnr_val = request.form['pnr'].upper().strip()
            ticket_num = request.form['ticket_number'].strip()
            passenger_val = request.form['passenger_name'].strip()
            supplier = request.form['supplier']
            currency = request.form['currency']
            amount = float(request.form['cost_iqd'] or 0)
            
            try:
                conn.execute('ALTER TABLE ticketing ADD COLUMN currency TEXT DEFAULT "IQD"')
                conn.commit()
            except Exception:
                pass

            conn.execute('''
                UPDATE ticketing 
                SET pnr = ?, ticket_number = ?, passenger_name = ?, supplier = ?, cost_iqd = ?, cost_secondary = ?, currency = ?
                WHERE id = ?
            ''', (pnr_val, ticket_num, passenger_val, supplier, amount, 0.0, currency, t_id))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if old_ticket:
                old_curr = old_ticket['currency'] if 'currency' in old_ticket.keys() and old_ticket['currency'] else 'IQD'
                detail_msg = (
                    f"<b>Updated ticket ID #{t_id}</b><br>"
                    f"PNR: {old_ticket['pnr'] or 'N/A'} -> {pnr_val or 'N/A'}<br>"
                    f"Ticket #: {old_ticket['ticket_number'] or 'N/A'} -> {ticket_num or 'N/A'}<br>"
                    f"Passenger: {old_ticket['passenger_name']} -> {passenger_val}<br>"
                    f"Supplier: {old_ticket['supplier']} -> {supplier}<br>"
                    f"Cost: {float(old_ticket['cost_iqd']):,.2f} {old_curr} -> {amount:,.2f} {currency}"
                )
            else:
                detail_msg = f"Updated ticket ID #{t_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'EDIT_TICKET', detail_msg, timestamp))
        else:
            if not can_add: return "Access Denied", 403
            
            pnr_val = request.form['pnr'].upper().strip()
            ticket_num = request.form['ticket_number'].strip()
            passenger_val = request.form['passenger_name'].strip()
            supplier = request.form['supplier']
            currency = request.form['currency']
            amount = float(request.form['cost_iqd'] or 0)
            
            try:
                conn.execute('ALTER TABLE ticketing ADD COLUMN currency TEXT DEFAULT "IQD"')
                conn.commit()
            except Exception:
                pass
            
            conn.execute('INSERT INTO ticketing (pnr, ticket_number, passenger_name, supplier, cost_iqd, cost_secondary, currency) VALUES (?, ?, ?, ?, ?, ?, ?)',
                         (pnr_val, ticket_num, passenger_val, supplier, amount, 0.0, currency))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            detail_msg = (
                f"PNR: {pnr_val or 'N/A'} | "
                f"Ticket #: {ticket_num or 'N/A'} | "
                f"Passenger: {passenger_val} | "
                f"Supplier: {supplier} | "
                f"Cost: {amount:,.2f} {currency}"
            )
            
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'ADD_TICKET', detail_msg, timestamp))
        
        conn.commit()
        conn.close()
        return redirect(url_for('ticketing'))
        
    # Ensure ticketing table exists safely
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ticketing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pnr TEXT,
            ticket_number TEXT,
            passenger_name TEXT,
            supplier TEXT,
            cost_iqd REAL DEFAULT 0,
            cost_secondary REAL DEFAULT 0,
            currency TEXT DEFAULT 'IQD'
        )
    ''')
    conn.commit()
    
    t_list = conn.execute('SELECT * FROM ticketing').fetchall()
    suppliers = conn.execute('SELECT * FROM suppliers').fetchall()
    currencies = conn.execute('SELECT * FROM currencies').fetchall()
    conn.close()
    
    supp_opts = ''.join([f'<option value="{s["name"]}">{s["name"]}</option>' for s in suppliers])
    currency_opts = ''.join([f'<option value="{cur["name"]}">{cur["name"]}</option>' for cur in currencies]) if currencies else '<option value="IQD">IQD</option><option value="USD">USD</option>'
    
    supp_opts = ''.join([f'<option value="{s["name"]}">{s["name"]}</option>' for s in suppliers])
    
    rows = ""
    for t in t_list:
        curr = t['currency'] if 'currency' in t.keys() and t['currency'] else 'IQD'
        edit_btn = f'<button type="button" onclick=\'openEditTicketModal({t["id"]}, "{t["pnr"] or ""}", "{t["ticket_number"] or ""}", "{t["passenger_name"]}", "{t["supplier"]}", "{t["cost_iqd"]}", "{curr}")\' class="text-blue-600 text-xs font-medium mr-3">Edit</button>'
        db_btn = f'<form method="POST" style="display:inline;" onsubmit="return confirm(\'Delete?\');"><input type="hidden" name="delete_id" value="{t["id"]}"><button type="submit" class="text-red-600 text-xs font-medium">Delete</button></form>' if can_del else ''
        
        rows += f'<tr class="border-b dark:border-slate-800 text-sm"><td class="py-3 px-4">#{t["id"]}</td><td class="py-3 px-4 font-mono">{t["pnr"] or "-"}</td><td class="py-3 px-4 font-mono">{t["ticket_number"] or "-"}</td><td class="py-3 px-4">{t["passenger_name"]}</td><td class="py-3 px-4">{t["supplier"]}</td><td class="py-3 px-4">{float(t["cost_iqd"]):,.2f} {curr}</td><td class="py-3 px-4 text-right">{edit_btn}{db_btn}</td></tr>'
        
    add_form = f"""
        <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800 h-fit">
            <h3 class="text-lg font-medium mb-4">Record Ticket</h3>
            <form method="POST" class="space-y-4">
                <div><label class="block text-sm mb-1">PNR</label><input type="text" name="pnr" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm uppercase"></div>
                <div><label class="block text-sm mb-1">Ticket Number</label><input type="text" name="ticket_number" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                <div><label class="block text-sm mb-1">Passenger Name</label><input type="text" name="passenger_name" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                <div><label class="block text-sm mb-1">Supplier</label><select name="supplier" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{supp_opts}</select></div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm mb-1">Currency</label>
                        <select name="currency" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                            <option value="">-- Select --</option>
                            {currency_opts}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">Cost</label>
                        <input type="number" step="0.01" name="cost_iqd" value="0" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                    </div>
                </div>
                <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Save Ticket</button>
            </form>
        </div>
    """ if can_add else ''
    
    edit_modal = f"""
        <div id="edit_ticket_modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-lg border dark:border-slate-800 w-full max-w-md">
                <h3 class="text-lg font-medium mb-4">Edit Ticket</h3>
                <form method="POST" class="space-y-4">
                    <input type="hidden" name="edit_id" id="edit_t_id">
                    <div><label class="block text-sm mb-1">PNR</label><input type="text" name="pnr" id="edit_t_pnr" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm uppercase"></div>
                    <div><label class="block text-sm mb-1">Ticket Number</label><input type="text" name="ticket_number" id="edit_t_ticket" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div><label class="block text-sm mb-1">Passenger Name</label><input type="text" name="passenger_name" id="edit_t_passenger" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div><label class="block text-sm mb-1">Supplier</label><select name="supplier" id="edit_t_supplier" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{supp_opts}</select></div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-sm mb-1">Currency</label>
                            <select name="currency" id="edit_t_currency" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                                <option value="">-- Select --</option>
                                {currency_opts}
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm mb-1">Cost</label>
                            <input type="number" step="0.01" name="cost_iqd" id="edit_t_cost" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                        </div>
                    </div>
                    <div class="flex space-x-3 pt-2">
                        <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Update Ticket</button>
                        <button type="button" onclick="closeEditTicketModal()" class="w-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 py-2 rounded-lg text-sm">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        <script>
            function openEditTicketModal(id, pnr, ticket, passenger, supplier, cost, curr) {{
                document.getElementById('edit_t_id').value = id;
                document.getElementById('edit_t_pnr').value = pnr;
                document.getElementById('edit_t_ticket').value = ticket;
                document.getElementById('edit_t_passenger').value = passenger;
                document.getElementById('edit_t_supplier').value = supplier;
                document.getElementById('edit_t_cost').value = cost;
                document.getElementById('edit_t_currency').value = curr;
                document.getElementById('edit_ticket_modal').classList.remove('hidden');
            }}
            function closeEditTicketModal() {{
                document.getElementById('edit_ticket_modal').classList.add('hidden');
            }}
        </script>
    """
    
    content = f"""
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {add_form}
            <div class="{'xl:col-span-2' if can_add else 'xl:col-span-3'} bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden h-fit">
                <table class="w-full text-left">
                    <thead><tr class="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-500 uppercase"><th class="py-3 px-4">ID</th><th class="py-3 px-4">PNR</th><th class="py-3 px-4">Ticket #</th><th class="py-3 px-4">Passenger</th><th class="py-3 px-4">Supplier</th><th class="py-3 px-4">Cost</th><th class="py-3 px-4 text-right">Action</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="7" class="py-6 text-center text-slate-400">No tickets.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        {edit_modal}
    """
    return render_layout("Airline Ticketing & PNR", content)

@app.route('/commissions', methods=['GET', 'POST'])
def commissions():
    if not check_permission('Commissions', 'view'): return "Access Denied", 403
    can_add = check_permission('Commissions', 'add')
    can_edit = check_permission('Commissions', 'edit') if 'check_permission' in globals() else can_add
    can_del = check_permission('Commissions', 'delete')
    
    conn = get_db_connection()

    if request.method == 'POST':
        if 'delete_id' in request.form:
            if not can_del: return "Access Denied", 403
            comm_id = request.form['delete_id']
            
            old_comm = conn.execute('SELECT * FROM commissions WHERE id = ?', (comm_id,)).fetchone()
            conn.execute('DELETE FROM commissions WHERE id = ?', (comm_id,))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if old_comm:
                old_dict = dict(old_comm)
                c_type = old_dict.get('commission_type', 'General')
                c_ref = old_dict.get('reference_no', '-') or '-'
                c_bene = old_dict.get('beneficiary_name', '-') or '-'
                c_amt = float(old_dict.get('amount_iqd', 0))
                c_curr = old_dict.get('currency', 'IQD') or 'IQD'
                c_date = old_dict.get('commission_date', str(datetime.date.today()))
                
                detail_msg = f"Deleted commission: {c_type} | Ref: {c_ref} | Beneficiary: {c_bene} | Amount: {c_amt:,.2f} {c_curr} | Date: {c_date}"
            else:
                detail_msg = f"Deleted commission ID {comm_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'DELETE_COMMISSION', detail_msg, timestamp))
                         
        elif 'edit_id' in request.form and request.form.get('edit_id'):
            if not can_edit: return "Access Denied", 403
            comm_id = request.form['edit_id']
            commission_type = request.form['commission_type']
            reference_no = request.form['reference_no'].strip()
            beneficiary_name = request.form['beneficiary_name'].strip()
            amount = float(request.form['amount_iqd'] or 0)
            curr = request.form.get('currency', 'IQD')
            comm_date = request.form.get('commission_date') or str(datetime.date.today())
            
            old_comm = conn.execute('SELECT * FROM commissions WHERE id = ?', (comm_id,)).fetchone()
            old_dict = dict(old_comm) if old_comm else {}
            
            conn.execute('''
                UPDATE commissions 
                SET commission_type = ?, reference_no = ?, beneficiary_name = ?, amount_iqd = ?, currency = ?, commission_date = ?
                WHERE id = ?
            ''', (commission_type, reference_no, beneficiary_name, amount, curr, comm_date, comm_id))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            old_type = old_dict.get('commission_type', 'General')
            old_ref = old_dict.get('reference_no', '-') or '-'
            old_bene = old_dict.get('beneficiary_name', '-') or '-'
            old_amt = float(old_dict.get('amount_iqd', 0))
            old_curr = old_dict.get('currency', 'IQD') or 'IQD'
            old_date = old_dict.get('commission_date', str(datetime.date.today()))
            
            detail_msg = (
                f"<b>Updated commission ID #{comm_id}</b><br>"
                f"Type: {old_type} -> {commission_type}<br>"
                f"Reference: {old_ref} -> {reference_no}<br>"
                f"Beneficiary: {old_bene} -> {beneficiary_name}<br>"
                f"Amount: {old_amt:,.2f} {old_curr} -> {amount:,.2f} {curr}<br>"
                f"Date: {old_date} -> {comm_date}"
            )
            
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'EDIT_COMMISSION', detail_msg, timestamp))
        else:
            if not can_add: return "Access Denied", 403
            commission_type = request.form['commission_type']
            reference_no = request.form['reference_no'].strip()
            beneficiary_name = request.form['beneficiary_name'].strip()
            amount = float(request.form['amount_iqd'] or 0)
            curr = request.form.get('currency', 'IQD')
            comm_date = request.form.get('commission_date') or str(datetime.date.today())
            
            conn.execute('''
                INSERT INTO commissions (commission_type, reference_no, beneficiary_name, amount_iqd, amount_secondary, currency, commission_date) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (commission_type, reference_no, beneficiary_name, amount, 0.0, curr, comm_date))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            detail_msg = f"Recorded commission: {commission_type} | Ref: {reference_no} | Beneficiary: {beneficiary_name} | Amount: {amount:,.2f} {curr} | Date: {comm_date}"
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'ADD_COMMISSION', detail_msg, timestamp))
                         
        conn.commit()
        conn.close()
        return redirect(url_for('commissions'))
        
    comm_list = conn.execute('SELECT * FROM commissions ORDER BY commission_date DESC').fetchall()
    currencies_list = conn.execute('SELECT * FROM currencies').fetchall()
    comm_types = conn.execute('SELECT * FROM commission_types').fetchall()
    conn.close()
    
    currency_options = ''.join([f'<option value="{cur["code"]}">{cur["code"]}</option>' for cur in currencies_list]) if currencies_list else '<option value="IQD">IQD</option><option value="USD">USD</option>'
    comm_type_options = ''.join([f'<option value="{ct["name"]}">{ct["name"]}</option>' for ct in comm_types])
    
    rows = ""
    for c in comm_list:
        c_dict = dict(c)
        c_id = c_dict.get('id', 1)
        c_date = c_dict.get('commission_date', str(datetime.date.today()))
        c_type = c_dict.get('commission_type', 'General')
        c_ref = c_dict.get('reference_no', '-') or '-'
        c_bene = c_dict.get('beneficiary_name', '-') or '-'
        c_amt = c_dict.get('amount_iqd', 0)
        c_curr = c_dict.get('currency', 'IQD') or 'IQD'
        
        edit_btn = f'<button type="button" onclick=\'openEditCommissionModal({c_id}, "{c_type}", "{c_ref}", "{c_bene}", "{c_amt}", "{c_curr}", "{c_date}")\' class="text-blue-600 text-xs font-medium mr-3">Edit</button>' if can_edit else ''
        db_btn = f'<form method="POST" style="display:inline;" onsubmit="return confirm(\'Delete commission?\');"><input type="hidden" name="delete_id" value="{c_id}"><button type="submit" class="text-red-600 text-xs font-medium">Delete</button></form>' if can_del else ''
        
        rows += f'<tr class="border-b dark:border-slate-800 text-sm"><td class="py-3 px-4">{c_date}</td><td class="py-3 px-4"><span class="bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded text-xs">{c_type}</span></td><td class="py-3 px-4 font-mono">{c_ref}</td><td class="py-3 px-4 font-semibold">{c_bene}</td><td class="py-3 px-4">{float(c_amt):,.2f} {c_curr}</td><td class="py-3 px-4 text-right">{edit_btn}{db_btn}</td></tr>'
        
    add_form = f"""
        <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800 h-fit">
            <h3 class="text-lg font-medium mb-4">Record Commission</h3>
            <form method="POST" class="space-y-4">
                <div><label class="block text-sm mb-1">Type</label><select name="commission_type" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{comm_type_options}</select></div>
                <div><label class="block text-sm mb-1">Reference No</label><input type="text" name="reference_no" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                <div><label class="block text-sm mb-1">Beneficiary</label><input type="text" name="beneficiary_name" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm mb-1">Currency</label>
                        <select name="currency" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                            <option value="">-- Select --</option>
                            {currency_options}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">Amount</label>
                        <input type="number" step="0.01" name="amount_iqd" value="0" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                    </div>
                </div>
                <div><label class="block text-sm mb-1">Date</label><input type="date" name="commission_date" value="{datetime.date.today()}" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Save Commission</button>
            </form>
        </div>
    """ if can_add else ''
    
    edit_modal = f"""
        <div id="edit_commission_modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-lg border dark:border-slate-800 w-full max-w-md">
                <h3 class="text-lg font-medium mb-4">Edit Commission</h3>
                <form method="POST" class="space-y-4">
                    <input type="hidden" name="edit_id" id="edit_comm_id">
                    <div><label class="block text-sm mb-1">Type</label><select name="commission_type" id="edit_comm_type" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{comm_type_options}</select></div>
                    <div><label class="block text-sm mb-1">Reference No</label><input type="text" name="reference_no" id="edit_comm_ref" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div><label class="block text-sm mb-1">Beneficiary</label><input type="text" name="beneficiary_name" id="edit_comm_bene" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-sm mb-1">Currency</label>
                            <select name="currency" id="edit_comm_curr" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                                <option value="">-- Select --</option>
                                {currency_options}
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm mb-1">Amount</label>
                            <input type="number" step="0.01" name="amount_iqd" id="edit_comm_amount" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                        </div>
                    </div>
                    <div><label class="block text-sm mb-1">Date</label><input type="date" name="commission_date" id="edit_comm_date" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div class="flex space-x-3 pt-2">
                        <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Update Commission</button>
                        <button type="button" onclick="closeEditCommissionModal()" class="w-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 py-2 rounded-lg text-sm">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        <script>
            function openEditCommissionModal(id, type, ref, bene, amount, curr, date) {{
                document.getElementById('edit_comm_id').value = id;
                document.getElementById('edit_comm_type').value = type;
                document.getElementById('edit_comm_ref').value = ref;
                document.getElementById('edit_comm_bene').value = bene;
                document.getElementById('edit_comm_amount').value = amount;
                document.getElementById('edit_comm_curr').value = curr;
                document.getElementById('edit_comm_date').value = date;
                document.getElementById('edit_commission_modal').classList.remove('hidden');
            }}
            function closeEditCommissionModal() {{
                document.getElementById('edit_commission_modal').classList.add('hidden');
            }}
        </script>
    """
    
    content = f"""
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {add_form}
            <div class="{'xl:col-span-2' if can_add else 'xl:col-span-3'} bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden h-fit">
                <table class="w-full text-left">
                    <thead><tr class="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-500 uppercase"><th class="py-3 px-4">Date</th><th class="py-3 px-4">Type</th><th class="py-3 px-4">Reference</th><th class="py-3 px-4">Beneficiary</th><th class="py-3 px-4">Amount</th><th class="py-3 px-4 text-right">Action</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="6" class="py-6 text-center text-slate-400">No records.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        {edit_modal}
    """
    return render_layout("Commission Management", content)


@app.route('/invoices', methods=['GET', 'POST'])
def invoices():
    if not check_permission('Invoices', 'view'): return "Access Denied", 403
    can_add = check_permission('Invoices', 'add')
    can_edit = check_permission('Invoices', 'edit') if 'check_permission' in globals() else can_add
    can_del = check_permission('Invoices', 'delete')
    
    conn = get_db_connection()
    
    # Ensure all required columns exist safely in the database table
    for col_def in ['currency TEXT DEFAULT "IQD"', 'status TEXT DEFAULT "Unpaid"', 'total_iqd REAL DEFAULT 0', 'invoice_number TEXT', 'issue_date TEXT', 'due_date TEXT']:
        try:
            conn.execute(f'ALTER TABLE invoices ADD COLUMN {col_def}')
            conn.commit()
        except Exception:
            pass

    if request.method == 'POST':
        if 'delete_id' in request.form:
            if not can_del: return "Access Denied", 403
            inv_id = request.form.get('delete_id')
            
            old_inv = conn.execute('SELECT * FROM invoices WHERE id = ?', (inv_id,)).fetchone()
            conn.execute('DELETE FROM invoices WHERE id = ?', (inv_id,))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if old_inv:
                old_dict = dict(old_inv)
                cust = conn.execute('SELECT name FROM customers WHERE id = ?', (old_dict.get('customer_id'),)).fetchone() if 'customer_id' in old_dict else None
                c_name = cust['name'] if cust else 'Unknown'
                curr = old_dict.get('currency', 'IQD') or 'IQD'
                inv_no = old_dict.get('invoice_number', 'N/A')
                detail_msg = f"Deleted invoice #{inv_no} | Customer: {c_name} | Amount: {float(old_dict.get('total_iqd', 0)):,.2f} {curr}"
            else:
                detail_msg = f"Deleted invoice ID {inv_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'DELETE_INVOICE', detail_msg, timestamp))
                         
        elif 'edit_id' in request.form and request.form.get('edit_id'):
            if not can_edit: return "Access Denied", 403
            inv_id = request.form.get('edit_id')
            
            old_inv = conn.execute('SELECT * FROM invoices WHERE id = ?', (inv_id,)).fetchone()
            old_dict = dict(old_inv) if old_inv else {}
            
            customer_id = request.form['customer_id']
            invoice_num = request.form.get('invoice_number', '').strip()
            if not invoice_num:
                invoice_num = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                
            raw_amount = request.form.get('amount')
            amount = float(raw_amount) if raw_amount else 0.0
            currency = request.form['currency']
            status = request.form['status']
            
            conn.execute('''
                UPDATE invoices 
                SET customer_id = ?, invoice_number = ?, total_iqd = ?, currency = ?, status = ?
                WHERE id = ?
            ''', (customer_id, invoice_num, amount, currency, status, inv_id))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cust_old = conn.execute('SELECT name FROM customers WHERE id = ?', (old_dict.get('customer_id'),)).fetchone() if 'customer_id' in old_dict else None
            cust_new = conn.execute('SELECT name FROM customers WHERE id = ?', (customer_id,)).fetchone()
            
            old_c_name = cust_old['name'] if cust_old else 'Unknown'
            new_c_name = cust_new['name'] if cust_new else 'Unknown'
            old_curr = old_dict.get('currency', 'IQD') or 'IQD'
            old_status = old_dict.get('status', 'Unpaid') or 'Unpaid'
            old_amt = float(old_dict.get('total_iqd', 0))
            old_inv_no = old_dict.get('invoice_number', 'N/A')
            
            detail_msg = (
                f"<b>Updated invoice #{old_inv_no} -> #{invoice_num}</b><br>"
                f"Customer: {old_c_name} -> {new_c_name}<br>"
                f"Amount: {old_amt:,.2f} {old_curr} -> {amount:,.2f} {currency}<br>"
                f"Status: {old_status} -> {status}"
            )
            
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'EDIT_INVOICE', detail_msg, timestamp))
        else:
            if not can_add: return "Access Denied", 403
            
            customer_id = request.form['customer_id']
            invoice_num = request.form.get('invoice_number', '').strip()
            
            if not invoice_num:
                today_prefix = datetime.datetime.now().strftime('%Y%m%d')
                existing = conn.execute(
                    "SELECT invoice_number FROM invoices WHERE invoice_number LIKE ?", 
                    (f"{today_prefix}%",)
                ).fetchall()
                
                max_counter = 0
                for row in existing:
                    inv_str = dict(row).get('invoice_number', '')
                    suffix = inv_str[len(today_prefix):]
                    if suffix.isdigit():
                        max_counter = max(max_counter, int(suffix))
                
                invoice_num = f"{today_prefix}{max_counter + 1}"
            
            raw_amount = request.form.get('amount')
            amount = float(raw_amount) if raw_amount else 0.0
            currency = request.form['currency']
            status = request.form.get('status', 'Unpaid')
            today_str = datetime.datetime.now().strftime('%Y-%m-%d')
            
            conn.execute('''
                INSERT INTO invoices (customer_id, invoice_number, issue_date, due_date, total_iqd, total_secondary, currency, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, invoice_num, today_str, today_str, amount, 0.0, currency, status))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cust = conn.execute('SELECT name FROM customers WHERE id = ?', (customer_id,)).fetchone()
            c_name = cust['name'] if cust else 'Unknown'
            
            detail_msg = f"Invoice #: {invoice_num} | Customer: {c_name} | Amount: {amount:,.2f} {currency} | Status: {status}"
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'ADD_INVOICE', detail_msg, timestamp))
        
        conn.commit()
        conn.close()
        return redirect(url_for('invoices'))
        
    raw_invoices = conn.execute('SELECT * FROM invoices').fetchall()
    custs = conn.execute('SELECT * FROM customers').fetchall()
    currencies = conn.execute('SELECT * FROM currencies').fetchall()
    conn.close()
    
    inv_list = []
    for inv in raw_invoices:
        inv_dict = dict(inv)
        inv_id = inv_dict.get('id', 1)
        cust_id = inv_dict.get('customer_id', 1)
        invoice_num = inv_dict.get('invoice_number', f"INV-{inv_id}")
        amount = inv_dict.get('total_iqd', 0)
        curr = inv_dict.get('currency', 'IQD') or 'IQD'
        status = inv_dict.get('status', 'Unpaid') or 'Unpaid'
        
        cust_match = next((c for c in custs if c['id'] == cust_id), None)
        cust_name = cust_match['name'] if cust_match else 'Unknown'
        
        inv_list.append({
            'id': inv_id,
            'customer_id': cust_id,
            'customer_name': cust_name,
            'invoice_number': invoice_num,
            'amount': amount,
            'currency': curr,
            'status': status
        })
    
    cust_opts = ''.join([f'<option value="{c["id"]}">{c["name"]}</option>' for c in custs])
    currency_opts = ''.join([f'<option value="{cur["name"]}">{cur["name"]}</option>' for cur in currencies]) if currencies else '<option value="IQD">IQD</option><option value="USD">USD</option>'
    
    rows = ""
    for inv in inv_list:
        print_btn = f'<a href="/invoices/print/{inv["id"]}" class="text-emerald-600 text-xs font-medium mr-3">Print</a>'
        edit_btn = f'<button type="button" onclick=\'openEditInvoiceModal({inv["id"]}, "{inv["customer_id"]}", "{inv["invoice_number"]}", "{inv["amount"]}", "{inv["currency"]}", "{inv["status"]}")\' class="text-blue-600 text-xs font-medium mr-3">Edit</button>' if can_edit else ''
        db_btn = f'<form method="POST" style="display:inline;" onsubmit="return confirm(\'Delete?\');"><input type="hidden" name="delete_id" value="{inv["id"]}"><button type="submit" class="text-red-600 text-xs font-medium">Delete</button></form>' if can_del else ''
        
        rows += f'<tr class="border-b dark:border-slate-800 text-sm"><td class="py-3 px-4 font-mono">#{inv["invoice_number"]}</td><td class="py-3 px-4 font-semibold">{inv["customer_name"]}</td><td class="py-3 px-4">{float(inv["amount"]):,.2f} {inv["currency"]}</td><td class="py-3 px-4"><span class="px-2 py-1 rounded text-xs {"bg-green-100 text-green-800" if inv["status"]=="Paid" else "bg-yellow-100 text-yellow-800"}">{inv["status"]}</span></td><td class="py-3 px-4 text-right">{print_btn}{edit_btn}{db_btn}</td></tr>'    
    add_form = f"""
        <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800 h-fit">
            <h3 class="text-lg font-medium mb-4">Create Invoice</h3>
            <form method="POST" class="space-y-4">
                <div><label class="block text-sm mb-1">Invoice Number <span class="text-xs text-slate-400">(Optional)</span></label><input type="text" name="invoice_number" placeholder="Leave blank for auto-numbering (e.g., 202610021)" class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm uppercase"></div>
                <div><label class="block text-sm mb-1">Customer</label><select name="customer_id" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{cust_opts}</select></div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm mb-1">Currency</label>
                        <select name="currency" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                            <option value="">-- Select --</option>
                            {currency_opts}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">Amount</label>
                        <input type="number" step="0.01" name="amount" placeholder="0.00" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                    </div>
                </div>
                <div>
                    <label class="block text-sm mb-1">Status</label>
                    <select name="status" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                        <option value="Unpaid">Unpaid</option>
                        <option value="Paid">Paid</option>
                    </select>
                </div>
                <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Save Invoice</button>
            </form>
        </div>
    """ if can_add else ''
    
    edit_modal = f"""
        <div id="edit_invoice_modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-lg border dark:border-slate-800 w-full max-w-md">
                <h3 class="text-lg font-medium mb-4">Edit Invoice</h3>
                <form method="POST" class="space-y-4">
                    <input type="hidden" name="edit_id" id="edit_inv_id">
                    <div><label class="block text-sm mb-1">Invoice Number</label><input type="text" name="invoice_number" id="edit_inv_number" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm uppercase"></div>
                    <div><label class="block text-sm mb-1">Customer</label><select name="customer_id" id="edit_inv_customer_id" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{cust_opts}</select></div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-sm mb-1">Currency</label>
                            <select name="currency" id="edit_inv_currency" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                                <option value="">-- Select --</option>
                                {currency_opts}
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm mb-1">Amount</label>
                            <input type="number" step="0.01" name="amount" id="edit_inv_amount" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">Status</label>
                        <select name="status" id="edit_inv_status" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                            <option value="Unpaid">Unpaid</option>
                            <option value="Paid">Paid</option>
                        </select>
                    </div>
                    <div class="flex space-x-3 pt-2">
                        <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Update Invoice</button>
                        <button type="button" onclick="closeEditInvoiceModal()" class="w-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 py-2 rounded-lg text-sm">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        <script>
            function openEditInvoiceModal(id, custId, invNumber, amount, curr, status) {{
                document.getElementById('edit_inv_id').value = id;
                document.getElementById('edit_inv_customer_id').value = custId;
                document.getElementById('edit_inv_number').value = invNumber;
                document.getElementById('edit_inv_amount').value = amount;
                document.getElementById('edit_inv_currency').value = curr;
                document.getElementById('edit_inv_status').value = status;
                document.getElementById('edit_invoice_modal').classList.remove('hidden');
            }}
            function closeEditInvoiceModal() {{
                document.getElementById('edit_invoice_modal').classList.add('hidden');
            }}
        </script>
    """
    
    content = f"""
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {add_form}
            <div class="{'xl:col-span-2' if can_add else 'xl:col-span-3'} bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden h-fit">
                <table class="w-full text-left">
                    <thead><tr class="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-500 uppercase"><th class="py-3 px-4">Invoice #</th><th class="py-3 px-4">Customer</th><th class="py-3 px-4">Amount</th><th class="py-3 px-4">Status</th><th class="py-3 px-4 text-right">Action</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="5" class="py-6 text-center text-slate-400">No invoices.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        {edit_modal}
    """
    return render_layout("Invoices & AR", content)
@app.route('/invoices/print/<int:id>')
def print_invoice(id):
    if not check_permission('Invoices', 'view'): return "Access Denied", 403
    conn = get_db_connection()
    inv = conn.execute('SELECT invoices.*, customers.name AS customer_name, customers.profile_type FROM invoices JOIN customers ON invoices.customer_id = customers.id WHERE invoices.id = ?', (id,)).fetchone()
    conn.close()
    if not inv: return "Not found", 404
    
    content = f"""
        <!-- Include html2pdf library for instant PDF downloads -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
        
        <div class="max-w-4xl mx-auto space-y-6">
            <!-- Back & Print Actions -->
            <div class="flex justify-between items-center print:hidden">
                <a href="/invoices" class="text-xs text-blue-600 dark:text-blue-400 font-medium hover:underline">← Back to Invoices</a>
                <div class="flex gap-2">
                    <button onclick="printPDF()" class="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-xs transition shadow-sm">🖨️ Print</button>
                    <button onclick="downloadPDF()" class="bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-4 py-2 rounded-lg text-xs transition shadow-sm">📥 Save as PDF</button>
                </div>
            </div>

            <!-- A4 Invoice Container -->
            <div id="invoice-card" class="bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 p-10 rounded-2xl shadow-sm border dark:border-slate-800 flex flex-col justify-between print:shadow-none print:border-none print:p-0" style="min-height: 260mm;">
                <div>
                    <!-- Header -->
                    <div class="flex justify-between items-start border-b dark:border-slate-800 pb-8 mb-8">
                        <div>
                            <h2 class="text-3xl font-bold tracking-wide">✈️ VELORA TRAVEL</h2>
                            <p class="text-xs text-slate-500 mt-1">Bakhtiyar and Waziran Main Rd, Erbil, Iraq 44001</p>
                            <p class="text-xs text-slate-500">info@veloratravel.co</p>
                            <p class="text-xs text-slate-500">+964 751 542 9004 | +964 788 742 9004</p>
                        </div>
                        <div class="text-right">
                            <h3 class="text-xl font-bold text-blue-600 dark:text-blue-400">{inv['invoice_number']}</h3>
                            <p class="text-xs text-slate-500 mt-1">Issue Date: <b>{inv['issue_date']}</b></p>
                            <p class="text-xs text-slate-500">Due Date: <b>{inv['due_date']}</b></p>
                        </div>
                    </div>

                    <!-- Client Details -->
                    <div class="grid grid-cols-2 gap-6 bg-slate-50 dark:bg-slate-800/50 p-6 rounded-xl border dark:border-slate-800 mb-8">
                        <div>
                            <p class="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1">Billed To: <span class="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">{inv['customer_name']}</span></p>
                            <p class="text-xs text-slate-500">Profile Type: {inv['profile_type']}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-1">Payment Status:<span class="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300">{inv['status']}</span></p>
                        </div>
                    </div>

                    <!-- Line Items Table -->
                    <table class="w-full text-left border-collapse mb-8">
                        <thead>
                            <tr class="border-b dark:border-slate-800 text-xs text-slate-400 uppercase">
                                <th class="py-3 px-4 font-semibold">Description</th>
                                <th class="py-3 px-4 font-semibold text-right">Amount</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y dark:divide-slate-800 text-sm">
                            <tr>
                                <td class="py-4 px-4 font-medium">Travel Services & Bookings Reference ({inv['invoice_number']})</td>
                                <td class="py-4 px-4 text-right font-semibold">{float(inv['total_iqd']):,.0f} {inv['currency']}</td>
                            </tr>
                            {"<tr><td class='py-4 px-4 text-slate-500'>Secondary Currency Equivalent</td><td class='py-4 px-4 text-right text-slate-500'>" + f"{float(inv['total_secondary']):,.2f} {inv['currency']}" + "</td></tr>" if inv['total_secondary'] > 0 else ""}
                        </tbody>
                    </table>

                    <!-- Totals Summary -->
                    <div class="flex justify-end pt-4 border-t dark:border-slate-800">
                        <div class="w-72 space-y-2">
                            <div class="flex justify-between text-sm">
                                <span class="text-slate-500">Subtotal:</span>
                                <span class="font-semibold">{float(inv['total_iqd']):,.0f} {inv['currency']}</span>
                            </div>
                            <div class="flex justify-between text-lg font-bold border-t dark:border-slate-800 pt-2">
                                <span>Total Due:</span>
                                <span class="text-blue-600 dark:text-blue-400">{float(inv['total_iqd']):,.0f} {inv['currency']}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Footer Notes (Always pushed to the bottom) -->
                <div class="border-t dark:border-slate-800 pt-6 text-center text-xs text-slate-400 space-y-1 mt-12">
                    <p>Thank you for choosing Velora Travel for your journey!</p>
                </div>
            </div>
        </div>

        <script>
            function downloadPDF() {{
                const originalElement = document.getElementById('invoice-card');
                
                // Clone the invoice container so the screen stays untouched in dark mode
                const clone = originalElement.cloneNode(true);
                
                // Force pure white background and dark text on the clone and ALL child elements
                clone.style.backgroundColor = '#ffffff';
                clone.style.color = '#1e293b';
                
                const allElements = clone.querySelectorAll('*');
                allElements.forEach(el => {{
                    el.style.backgroundColor = '#ffffff';
                    el.style.color = '#1e293b';
                    el.style.borderColor = '#e2e8f0';
                }});
                
                // Keep clean badge coloring for Paid / Unpaid statuses
                clone.querySelectorAll('span').forEach(el => {{
                    if (el.innerText.includes('Paid')) {{
                        el.style.backgroundColor = '#dcfce7';
                        el.style.color = '#166534';
                    }} else if (el.innerText.includes('Unpaid')) {{
                        el.style.backgroundColor = '#fef9c3';
                        el.style.color = '#854d0e';
                    }}
                }});

                const container = document.createElement('div');
                container.style.position = 'absolute';
                container.style.left = '-9999px';
                container.appendChild(clone);
                document.body.appendChild(container);
                
                const opt = {{
                    margin:       10,
                    filename:     'Invoice_{inv['invoice_number']}.pdf',
                    image:        {{ type: 'jpeg', quality: 0.98 }},
                    html2canvas:  {{ scale: 2, useCORS: true, logging: false, backgroundColor: '#ffffff' }},
                    jsPDF:        {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
                }};
                
                html2pdf().from(clone).set(opt).save().then(() => {{
                    document.body.removeChild(container);
                }});
            }}

            function printPDF() {{
                const originalElement = document.getElementById('invoice-card');
                const clone = originalElement.cloneNode(true);
                
                clone.style.backgroundColor = '#ffffff';
                clone.style.color = '#1e293b';
                
                const allElements = clone.querySelectorAll('*');
                allElements.forEach(el => {{
                    el.style.backgroundColor = '#ffffff';
                    el.style.color = '#1e293b';
                    el.style.borderColor = '#e2e8f0';
                }});
                
                clone.querySelectorAll('span').forEach(el => {{
                    if (el.innerText.includes('Paid')) {{
                        el.style.backgroundColor = '#dcfce7';
                        el.style.color = '#166534';
                    }} else if (el.innerText.includes('Unpaid')) {{
                        el.style.backgroundColor = '#fef9c3';
                        el.style.color = '#854d0e';
                    }}
                }});

                const container = document.createElement('div');
                container.style.position = 'absolute';
                container.style.left = '-9999px';
                container.appendChild(clone);
                document.body.appendChild(container);
                
                const opt = {{
                    margin:       10,
                    filename:     'Invoice_{inv['invoice_number']}.pdf',
                    image:        {{ type: 'jpeg', quality: 0.98 }},
                    html2canvas:  {{ scale: 2, useCORS: true, logging: false, backgroundColor: '#ffffff' }},
                    jsPDF:        {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
                }};
                
                html2pdf().from(clone).set(opt).outputPdf('bloburl').then((pdfUrl) => {{
                    document.body.removeChild(container);
                    const printWindow = window.open(pdfUrl, '_blank');
                    if (printWindow) {{
                        printWindow.onload = function() {{
                            printWindow.print();
                        }};
                    }}
                }});
            }}
        </script>
    """
    return render_layout(f"Invoice {inv['invoice_number']}", content)


@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if not check_permission('Customers', 'view'): return "Access Denied", 403
    can_add = check_permission('Customers', 'add')
    can_edit = check_permission('Customers', 'edit') if 'check_permission' in globals() else can_add
    can_del = check_permission('Customers', 'delete')
    
    conn = get_db_connection()
    
    # Ensure preferred_currency column exists in customers table
    try:
        conn.execute('ALTER TABLE customers ADD COLUMN preferred_currency TEXT DEFAULT "IQD"')
        conn.commit()
    except Exception:
        pass

    if request.method == 'POST':
        if 'delete_id' in request.form:
            if not can_del: return "Access Denied", 403
            cust_id = request.form['delete_id']
            
            old_cust = conn.execute('SELECT * FROM customers WHERE id = ?', (cust_id,)).fetchone()
            conn.execute('DELETE FROM customers WHERE id = ?', (cust_id,))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if old_cust:
                old_dict = dict(old_cust)
                c_name = old_dict.get('name', 'Unknown')
                c_profile = old_dict.get('profile_type', 'Individual')
                c_limit = float(old_dict.get('credit_limit_iqd', 0))
                c_curr = old_dict.get('preferred_currency', 'IQD') or 'IQD'
                
                detail_msg = f"Deleted customer: {c_name} | Profile: {c_profile} | Credit Limit: {c_limit:,.2f} {c_curr}"
            else:
                detail_msg = f"Deleted customer ID {cust_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'DELETE_CUSTOMER', detail_msg, timestamp))
                         
        elif 'edit_id' in request.form and request.form.get('edit_id'):
            if not can_edit: return "Access Denied", 403
            cust_id = request.form['edit_id']
            name = request.form['name']
            profile_type = request.form['profile_type']
            credit_limit = float(request.form['credit_limit_iqd'] or 0)
            pref_curr = request.form.get('preferred_currency', 'IQD')
            
            old_cust = conn.execute('SELECT * FROM customers WHERE id = ?', (cust_id,)).fetchone()
            old_dict = dict(old_cust) if old_cust else {}
            
            conn.execute('''
                UPDATE customers 
                SET name = ?, profile_type = ?, credit_limit_iqd = ?, preferred_currency = ?
                WHERE id = ?
            ''', (name, profile_type, credit_limit, pref_curr, cust_id))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            old_name = old_dict.get('name', 'Unknown')
            old_profile = old_dict.get('profile_type', 'Individual')
            old_limit = float(old_dict.get('credit_limit_iqd', 0))
            old_curr = old_dict.get('preferred_currency', 'IQD') or 'IQD'
            
            detail_msg = (
                f"<b>Updated customer ID #{cust_id}</b><br>"
                f"Name: {old_name} -> {name}<br>"
                f"Profile: {old_profile} -> {profile_type}<br>"
                f"Credit Limit: {old_limit:,.2f} {old_curr} -> {credit_limit:,.2f} {pref_curr}"
            )
            
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'EDIT_CUSTOMER', detail_msg, timestamp))
        else:
            if not can_add: return "Access Denied", 403
            name = request.form['name']
            profile_type = request.form['profile_type']
            credit_limit = float(request.form['credit_limit_iqd'] or 0)
            pref_curr = request.form.get('preferred_currency', 'IQD')
            
            conn.execute('INSERT INTO customers (name, profile_type, credit_limit_iqd, preferred_currency) VALUES (?, ?, ?, ?)', 
                         (name, profile_type, credit_limit, pref_curr))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            detail_msg = f"Added customer: {name} | Profile: {profile_type} | Credit Limit: {credit_limit:,.2f} {pref_curr}"
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'ADD_CUSTOMER', detail_msg, timestamp))
                         
        conn.commit()
        conn.close()
        return redirect(url_for('customers'))
        
    raw_customers = conn.execute('SELECT * FROM customers').fetchall()
    currencies = conn.execute('SELECT * FROM currencies').fetchall()
    conn.close()
    
    currency_opts = ''.join([f'<option value="{cur["name"]}">{cur["name"]}</option>' for cur in currencies]) if currencies else '<option value="IQD">IQD</option><option value="USD">USD</option>'
    
    rows = ""
    for c in raw_customers:
        c_dict = dict(c)
        c_id = c_dict.get('id', 1)
        c_name = c_dict.get('name', 'Unknown')
        c_profile = c_dict.get('profile_type', 'Individual')
        c_limit = c_dict.get('credit_limit_iqd', 0)
        c_curr = c_dict.get('preferred_currency', 'IQD') or 'IQD'
        
        edit_btn = f'<button type="button" onclick=\'openEditCustomerModal({c_id}, "{c_name}", "{c_profile}", "{c_limit}", "{c_curr}")\' class="text-blue-600 text-xs font-medium mr-3">Edit</button>' if can_edit else ''
        db_btn = f'<form method="POST" style="display:inline;" onsubmit="return confirm(\'Delete customer?\');"><input type="hidden" name="delete_id" value="{c_id}"><button type="submit" class="text-red-600 text-xs font-medium">Delete</button></form>' if can_del else ''
        
        rows += f'<tr class="border-b dark:border-slate-800 text-sm"><td class="py-3 px-4 font-semibold">{c_name}</td><td class="py-3 px-4">{c_profile}</td><td class="py-3 px-4">{float(c_limit):,.2f} {c_curr}</td><td class="py-3 px-4 text-right">{edit_btn}{db_btn}</td></tr>'
        
    add_form = f"""
        <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800 h-fit">
            <h3 class="text-lg font-medium mb-4">Add Customer</h3>
            <form method="POST" class="space-y-4">
                <div><label class="block text-sm mb-1">Customer Name</label><input type="text" name="name" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                <div><label class="block text-sm mb-1">Profile Type</label><select name="profile_type" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="Individual">Individual</option><option value="Corporate">Corporate</option></select></div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm mb-1">Currency</label>
                        <select name="preferred_currency" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                            <option value="">-- Select --</option>
                            {currency_opts}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">Credit Limit</label>
                        <input type="number" step="0.01" name="credit_limit_iqd" value="0" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                    </div>
                </div>
                <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Save Customer</button>
            </form>
        </div>
    """ if can_add else ''
    
    edit_modal = f"""
        <div id="edit_customer_modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-lg border dark:border-slate-800 w-full max-w-md">
                <h3 class="text-lg font-medium mb-4">Edit Customer</h3>
                <form method="POST" class="space-y-4">
                    <input type="hidden" name="edit_id" id="edit_cust_id">
                    <div><label class="block text-sm mb-1">Customer Name</label><input type="text" name="name" id="edit_cust_name" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div><label class="block text-sm mb-1">Profile Type</label><select name="profile_type" id="edit_cust_profile" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="Individual">Individual</option><option value="Corporate">Corporate</option></select></div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-sm mb-1">Currency</label>
                            <select name="preferred_currency" id="edit_cust_curr" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                                <option value="">-- Select --</option>
                                {currency_opts}
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm mb-1">Credit Limit</label>
                            <input type="number" step="0.01" name="credit_limit_iqd" id="edit_cust_limit" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                        </div>
                    </div>
                    <div class="flex space-x-3 pt-2">
                        <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Update Customer</button>
                        <button type="button" onclick="closeEditCustomerModal()" class="w-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 py-2 rounded-lg text-sm">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        <script>
            function openEditCustomerModal(id, name, profile, limit, curr) {{
                document.getElementById('edit_cust_id').value = id;
                document.getElementById('edit_cust_name').value = name;
                document.getElementById('edit_cust_profile').value = profile;
                document.getElementById('edit_cust_limit').value = limit;
                document.getElementById('edit_cust_curr').value = curr;
                document.getElementById('edit_customer_modal').classList.remove('hidden');
            }}
            function closeEditCustomerModal() {{
                document.getElementById('edit_customer_modal').classList.add('hidden');
            }}
        </script>
    """
    
    content = f"""
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {add_form}
            <div class="{'xl:col-span-2' if can_add else 'xl:col-span-3'} bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden h-fit">
                <table class="w-full text-left">
                    <thead><tr class="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-500 uppercase"><th class="py-3 px-4">Name</th><th class="py-3 px-4">Profile Type</th><th class="py-3 px-4">Credit Limit</th><th class="py-3 px-4 text-right">Action</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="4" class="py-6 text-center text-slate-400">No customers.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        {edit_modal}
    """
    return render_layout("Customer Management", content)

@app.route('/bookings', methods=['GET', 'POST'])
def bookings():
    if not check_permission('Bookings', 'view'): return "Access Denied", 403
    can_add = check_permission('Bookings', 'add')
    can_edit = check_permission('Bookings', 'edit') if 'check_permission' in globals() else can_add
    can_del = check_permission('Bookings', 'delete')
    
    conn = get_db_connection()
    if request.method == 'POST':
        if 'delete_id' in request.form:
            if not can_del: return "Access Denied", 403
            book_id = request.form['delete_id']
            
            booking_to_del = conn.execute('SELECT bookings.*, customers.name AS customer_name FROM bookings JOIN customers ON bookings.customer_id = customers.id WHERE bookings.id = ?', (book_id,)).fetchone()
            
            conn.execute('DELETE FROM bookings WHERE id = ?', (book_id,))
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if booking_to_del:
                detail_msg = (
                    f"Deleted booking ID #{book_id} | "
                    f"Customer: {booking_to_del['customer_name']} | "
                    f"Service: {booking_to_del['service_type']} | "
                    f"PNR: {booking_to_del['pnr'] or 'N/A'} | "
                    f"Ticket #: {booking_to_del['ticket_number'] or 'N/A'} | "
                    f"Passenger: {booking_to_del['passenger_name']} | "
                    f"Price: {float(booking_to_del['selling_price_iqd']):,.2f} {booking_to_del['currency']}"
                )
            else:
                detail_msg = f"Deleted booking ID {book_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'DELETE_BOOKING', detail_msg, timestamp))
                         
        elif 'edit_id' in request.form:
            book_id = request.form['edit_id']
            
            old_booking = conn.execute('SELECT bookings.*, customers.name AS customer_name FROM bookings JOIN customers ON bookings.customer_id = customers.id WHERE bookings.id = ?', (book_id,)).fetchone()
            
            customer_id = request.form['customer_id']
            service_type = request.form['service_type']
            pnr_val = request.form['pnr'].upper().strip()
            ticket_num = request.form['ticket_number'].strip()
            passenger_val = request.form['passenger_name'].strip()
            currency = request.form['currency']
            amount = float(request.form['amount'] or 0)
            
            cust_record = conn.execute('SELECT name FROM customers WHERE id = ?', (customer_id,)).fetchone()
            new_cust_name = cust_record['name'] if cust_record else "Unknown"
            
            conn.execute('''
                UPDATE bookings 
                SET customer_id = ?, service_type = ?, pnr = ?, ticket_number = ?, passenger_name = ?, selling_price_iqd = ?, selling_price_secondary = ?, currency = ?
                WHERE id = ?
            ''', (customer_id, service_type, pnr_val, ticket_num, passenger_val, amount, 0.0, currency, book_id))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if old_booking:
                old_curr = old_booking['currency'] if 'currency' in old_booking.keys() and old_booking['currency'] else 'IQD'
                detail_msg = (
                    f"<b>Updated booking ID #{book_id}</b><br>"
                    f"Customer: {old_booking['customer_name']} -> {new_cust_name}<br>"
                    f"Service: {old_booking['service_type']} -> {service_type}<br>"
                    f"PNR: {old_booking['pnr'] or 'N/A'} -> {pnr_val or 'N/A'}<br>"
                    f"Ticket #: {old_booking['ticket_number'] or 'N/A'} -> {ticket_num or 'N/A'}<br>"
                    f"Passenger: {old_booking['passenger_name']} -> {passenger_val}<br>"
                    f"Price: {float(old_booking['selling_price_iqd']):,.2f} {old_curr} -> {amount:,.2f} {currency}"
                )
            else:
                detail_msg = f"Updated booking ID #{book_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'EDIT_BOOKING', detail_msg, timestamp))
        else:
            if not can_add: return "Access Denied", 403
            
            customer_id = request.form['customer_id']
            service_type = request.form['service_type']
            pnr_val = request.form['pnr'].upper().strip()
            ticket_num = request.form['ticket_number'].strip()
            passenger_val = request.form['passenger_name'].strip()
            currency = request.form['currency']
            amount = float(request.form['amount'] or 0)
            
            try:
                conn.execute('ALTER TABLE bookings ADD COLUMN currency TEXT DEFAULT "IQD"')
                conn.commit()
            except Exception:
                pass
            
            cust_record = conn.execute('SELECT name FROM customers WHERE id = ?', (customer_id,)).fetchone()
            cust_name = cust_record['name'] if cust_record else "Unknown"
            
            conn.execute('INSERT INTO bookings (customer_id, service_type, pnr, ticket_number, passenger_name, selling_price_iqd, selling_price_secondary, currency) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                         (customer_id, service_type, pnr_val, ticket_num, passenger_val, amount, 0.0, currency))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            detail_msg = (
                f"Customer: {cust_name} | "
                f"Service: {service_type} | "
                f"PNR: {pnr_val or 'N/A'} | "
                f"Ticket #: {ticket_num or 'N/A'} | "
                f"Passenger: {passenger_val} | "
                f"Price: {amount:,.2f} {currency}"
            )
            
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'ADD_BOOKING', detail_msg, timestamp))
        
        conn.commit()
        conn.close()
        return redirect(url_for('bookings'))
        
    b_list = conn.execute('SELECT bookings.*, customers.name AS customer_name FROM bookings JOIN customers ON bookings.customer_id = customers.id').fetchall()
    custs = conn.execute('SELECT * FROM customers').fetchall()
    services = conn.execute('SELECT * FROM service_types').fetchall()
    currencies = conn.execute('SELECT * FROM currencies').fetchall()
    conn.close()
    
    cust_opts = ''.join([f'<option value="{c["id"]}">{c["name"]}</option>' for c in custs])
    service_opts = ''.join([f'<option value="{s["name"]}">{s["name"]}</option>' for s in services])
    currency_opts = ''.join([f'<option value="{cur["name"]}">{cur["name"]}</option>' for cur in currencies]) if currencies else '<option value="IQD">IQD</option><option value="USD">USD</option>'
    
    rows = ""
    for b in b_list:
        curr = b['currency'] if 'currency' in b.keys() and b['currency'] else 'IQD'
        edit_btn = f'<button type="button" onclick=\'openEditModal({b["id"]}, "{b["customer_id"]}", "{b["service_type"]}", "{b["pnr"] or ""}", "{b["ticket_number"] or ""}", "{b["passenger_name"]}", "{b["selling_price_iqd"]}", "{curr}")\' class="text-blue-600 text-xs font-medium mr-3">Edit</button>'
        db_btn = f'<form method="POST" style="display:inline;" onsubmit="return confirm(\'Delete?\');"><input type="hidden" name="delete_id" value="{b["id"]}"><button type="submit" class="text-red-600 text-xs font-medium">Delete</button></form>' if can_del else ''
        
        rows += f'<tr class="border-b dark:border-slate-800 text-sm"><td class="py-3 px-4">#{b["id"]}</td><td class="py-3 px-4 font-semibold">{b["customer_name"]}</td><td class="py-3 px-4">{b["service_type"]}</td><td class="py-3 px-4 font-mono">{b["pnr"] or "-"}</td><td class="py-3 px-4">{b["passenger_name"]}</td><td class="py-3 px-4">{float(b["selling_price_iqd"]):,.2f} {curr}</td><td class="py-3 px-4 text-right">{edit_btn}{db_btn}</td></tr>'
        
    add_form = f"""
        <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800 h-fit">
            <h3 class="text-lg font-medium mb-4">Record Booking</h3>
            <form method="POST" class="space-y-4">
                <div><label class="block text-sm mb-1">Customer</label><select name="customer_id" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{cust_opts}</select></div>
                <div><label class="block text-sm mb-1">Service</label><select name="service_type" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{service_opts}</select></div>
                <div><label class="block text-sm mb-1">PNR</label><input type="text" name="pnr" class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm uppercase"></div>
                <div><label class="block text-sm mb-1">Ticket Number</label><input type="text" name="ticket_number" class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                <div><label class="block text-sm mb-1">Passenger Name</label><input type="text" name="passenger_name" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm mb-1">Currency</label>
                        <select name="currency" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                            <option value="">-- Select --</option>
                            {currency_opts}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">Amount</label>
                        <input type="number" step="0.01" name="amount" value="0" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                    </div>
                </div>
                <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Save Booking</button>
            </form>
        </div>
    """ if can_add else ''
    
    edit_modal = f"""
        <div id="edit_modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-lg border dark:border-slate-800 w-full max-w-md">
                <h3 class="text-lg font-medium mb-4">Edit Booking</h3>
                <form method="POST" class="space-y-4">
                    <input type="hidden" name="edit_id" id="edit_id">
                    <div><label class="block text-sm mb-1">Customer</label><select name="customer_id" id="edit_customer_id" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{cust_opts}</select></div>
                    <div><label class="block text-sm mb-1">Service</label><select name="service_type" id="edit_service_type" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{service_opts}</select></div>
                    <div><label class="block text-sm mb-1">PNR</label><input type="text" name="pnr" id="edit_pnr" class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm uppercase"></div>
                    <div><label class="block text-sm mb-1">Ticket Number</label><input type="text" name="ticket_number" id="edit_ticket_number" class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div><label class="block text-sm mb-1">Passenger Name</label><input type="text" name="passenger_name" id="edit_passenger_name" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-sm mb-1">Currency</label>
                            <select name="currency" id="edit_currency" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                                <option value="">-- Select --</option>
                                {currency_opts}
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm mb-1">Amount</label>
                            <input type="number" step="0.01" name="amount" id="edit_amount" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                        </div>
                    </div>
                    <div class="flex space-x-3 pt-2">
                        <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Update Booking</button>
                        <button type="button" onclick="closeEditModal()" class="w-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 py-2 rounded-lg text-sm">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        <script>
            function openEditModal(id, custId, service, pnr, ticket, passenger, amount, curr) {{
                document.getElementById('edit_id').value = id;
                document.getElementById('edit_customer_id').value = custId;
                document.getElementById('edit_service_type').value = service;
                document.getElementById('edit_pnr').value = pnr;
                document.getElementById('edit_ticket_number').value = ticket;
                document.getElementById('edit_passenger_name').value = passenger;
                document.getElementById('edit_amount').value = amount;
                document.getElementById('edit_currency').value = curr;
                document.getElementById('edit_modal').classList.remove('hidden');
            }}
            function closeEditModal() {{
                document.getElementById('edit_modal').classList.add('hidden');
            }}
        </script>
    """
    
    content = f"""
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {add_form}
            <div class="{'xl:col-span-2' if can_add else 'xl:col-span-3'} bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden h-fit">
                <table class="w-full text-left">
                    <thead><tr class="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-500 uppercase"><th class="py-3 px-4">ID</th><th class="py-3 px-4">Customer</th><th class="py-3 px-4">Service</th><th class="py-3 px-4">PNR</th><th class="py-3 px-4">Passenger</th><th class="py-3 px-4">Price</th><th class="py-3 px-4 text-right">Action</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="7" class="py-6 text-center text-slate-400">No bookings.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        {edit_modal}
    """
    return render_layout("Sales & Bookings", content)

@app.route('/suppliers', methods=['GET', 'POST'])
def suppliers():
    if not check_permission('Suppliers', 'view'): return "Access Denied", 403
    can_add = check_permission('Suppliers', 'add')
    can_edit = check_permission('Suppliers', 'edit') if 'check_permission' in globals() else can_add
    can_del = check_permission('Suppliers', 'delete')
    
    conn = get_db_connection()
    
    # Ensure currency column exists in suppliers table safely
    try:
        conn.execute('ALTER TABLE suppliers ADD COLUMN currency TEXT DEFAULT "IQD"')
        conn.commit()
    except Exception:
        pass

    if request.method == 'POST':
        if 'delete_id' in request.form:
            if not can_del: return "Access Denied", 403
            supp_id = request.form['delete_id']
            
            old_supp = conn.execute('SELECT * FROM suppliers WHERE id = ?', (supp_id,)).fetchone()
            conn.execute('DELETE FROM suppliers WHERE id = ?', (supp_id,))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if old_supp:
                old_dict = dict(old_supp)
                s_name = old_dict.get('name', 'Unknown')
                s_type = old_dict.get('supplier_type', 'General')
                s_amt = float(old_dict.get('amount_payable_iqd', 0))
                s_curr = old_dict.get('currency', 'IQD') or 'IQD'
                
                detail_msg = f"Deleted supplier: {s_name} | Type: {s_type} | Amount Payable: {s_amt:,.2f} {s_curr}"
            else:
                detail_msg = f"Deleted supplier ID {supp_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'DELETE_SUPPLIER', detail_msg, timestamp))
                         
        elif 'edit_id' in request.form and request.form.get('edit_id'):
            if not can_edit: return "Access Denied", 403
            supp_id = request.form['edit_id']
            name = request.form['name'].strip()
            supplier_type = request.form['supplier_type']
            amount = float(request.form['amount_payable_iqd'] or 0)
            curr = request.form.get('currency', 'IQD')
            credit_limit = float(request.form.get('credit_limit_iqd', 0) or 0)
            
            old_supp = conn.execute('SELECT * FROM suppliers WHERE id = ?', (supp_id,)).fetchone()
            old_dict = dict(old_supp) if old_supp else {}
            
            conn.execute('''
                UPDATE suppliers 
                SET name = ?, supplier_type = ?, amount_payable_iqd = ?, currency = ?, credit_limit_iqd = ?
                WHERE id = ?
            ''', (name, supplier_type, amount, curr, credit_limit, supp_id))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            old_name = old_dict.get('name', 'Unknown')
            old_type = old_dict.get('supplier_type', 'General')
            old_amt = float(old_dict.get('amount_payable_iqd', 0))
            old_curr = old_dict.get('currency', 'IQD') or 'IQD'
            
            detail_msg = (
                f"<b>Updated supplier ID #{supp_id}</b><br>"
                f"Name: {old_name} -> {name}<br>"
                f"Type: {old_type} -> {supplier_type}<br>"
                f"Amount Payable: {old_amt:,.2f} {old_curr} -> {amount:,.2f} {curr}"
            )
            
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'EDIT_SUPPLIER', detail_msg, timestamp))
        else:
            if not can_add: return "Access Denied", 403
            name = request.form['name'].strip()
            supplier_type = request.form['supplier_type']
            amount = float(request.form['amount_payable_iqd'] or 0)
            curr = request.form.get('currency', 'IQD')
            credit_limit = float(request.form.get('credit_limit_iqd', 0) or 0)
            
            conn.execute('''
                INSERT INTO suppliers (name, supplier_type, amount_payable_iqd, currency, credit_limit_iqd) 
                VALUES (?, ?, ?, ?, ?)
            ''', (name, supplier_type, amount, curr, credit_limit))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            detail_msg = f"Added supplier: {name} | Type: {supplier_type} | Amount Payable: {amount:,.2f} {curr}"
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'ADD_SUPPLIER', detail_msg, timestamp))
                         
        conn.commit()
        conn.close()
        return redirect(url_for('suppliers'))
        
    supps = conn.execute('SELECT * FROM suppliers').fetchall()
    types = conn.execute('SELECT * FROM supplier_types').fetchall()
    currencies = conn.execute('SELECT * FROM currencies').fetchall()
    conn.close()
    
    type_opts = ''.join([f'<option value="{t["name"]}">{t["name"]}</option>' for t in types])
    currency_opts = ''.join([f'<option value="{cur["name"]}">{cur["name"]}</option>' for cur in currencies]) if currencies else '<option value="IQD">IQD</option><option value="USD">USD</option>'
    
    rows = ""
    for s in supps:
        s_dict = dict(s)
        s_id = s_dict.get('id', 1)
        s_name = s_dict.get('name', 'Unknown')
        s_type = s_dict.get('supplier_type', 'General')
        s_amt = s_dict.get('amount_payable_iqd', 0)
        s_curr = s_dict.get('currency', 'IQD') or 'IQD'
        s_limit = s_dict.get('credit_limit_iqd', 0)
        
        edit_btn = f'<button type="button" onclick=\'openEditSupplierModal({s_id}, "{s_name}", "{s_type}", "{s_amt}", "{s_curr}", "{s_limit}")\' class="text-blue-600 text-xs font-medium mr-3">Edit</button>' if can_edit else ''
        db_btn = f'<form method="POST" style="display:inline;" onsubmit="return confirm(\'Delete supplier?\');"><input type="hidden" name="delete_id" value="{s_id}"><button type="submit" class="text-red-600 text-xs font-medium">Delete</button></form>' if can_del else ''
        
        rows += f'<tr class="border-b dark:border-slate-800 text-sm"><td class="py-3 px-4 font-semibold">{s_name}</td><td class="py-3 px-4">{s_type}</td><td class="py-3 px-4">{float(s_amt):,.2f} {s_curr}</td><td class="py-3 px-4 text-right">{edit_btn}{db_btn}</td></tr>'
        
    add_form = f"""
        <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800 h-fit">
            <h3 class="text-lg font-medium mb-4">Add Supplier</h3>
            <form method="POST" class="space-y-4">
                <div><label class="block text-sm mb-1">Supplier Name</label><input type="text" name="name" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                <div><label class="block text-sm mb-1">Supplier Type</label><select name="supplier_type" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{type_opts}</select></div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm mb-1">Currency</label>
                        <select name="currency" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                            <option value="">-- Select --</option>
                            {currency_opts}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">Amount Payable</label>
                        <input type="number" step="0.01" name="amount_payable_iqd" value="0" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                    </div>
                </div>
                <input type="hidden" name="credit_limit_iqd" value="0">
                <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Save Supplier</button>
            </form>
        </div>
    """ if can_add else ''
    
    edit_modal = f"""
        <div id="edit_supplier_modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-lg border dark:border-slate-800 w-full max-w-md">
                <h3 class="text-lg font-medium mb-4">Edit Supplier</h3>
                <form method="POST" class="space-y-4">
                    <input type="hidden" name="edit_id" id="edit_supp_id">
                    <div><label class="block text-sm mb-1">Supplier Name</label><input type="text" name="name" id="edit_supp_name" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div><label class="block text-sm mb-1">Supplier Type</label><select name="supplier_type" id="edit_supp_type" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{type_opts}</select></div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-sm mb-1">Currency</label>
                            <select name="currency" id="edit_supp_curr" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                                <option value="">-- Select --</option>
                                {currency_opts}
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm mb-1">Amount Payable</label>
                            <input type="number" step="0.01" name="amount_payable_iqd" id="edit_supp_amount" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                        </div>
                    </div>
                    <input type="hidden" name="credit_limit_iqd" id="edit_supp_limit" value="0">
                    <div class="flex space-x-3 pt-2">
                        <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Update Supplier</button>
                        <button type="button" onclick="closeEditSupplierModal()" class="w-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 py-2 rounded-lg text-sm">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        <script>
            function openEditSupplierModal(id, name, type, amount, curr, limit) {{
                document.getElementById('edit_supp_id').value = id;
                document.getElementById('edit_supp_name').value = name;
                document.getElementById('edit_supp_type').value = type;
                document.getElementById('edit_supp_amount').value = amount;
                document.getElementById('edit_supp_curr').value = curr;
                document.getElementById('edit_supp_limit').value = limit;
                document.getElementById('edit_supplier_modal').classList.remove('hidden');
            }}
            function closeEditSupplierModal() {{
                document.getElementById('edit_supplier_modal').classList.add('hidden');
            }}
        </script>
    """
    
    content = f"""
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {add_form}
            <div class="{'xl:col-span-2' if can_add else 'xl:col-span-3'} bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden h-fit">
                <table class="w-full text-left">
                    <thead><tr class="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-500 uppercase"><th class="py-3 px-4">Name</th><th class="py-3 px-4">Type</th><th class="py-3 px-4">Amount Payable</th><th class="py-3 px-4 text-right">Action</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="4" class="py-6 text-center text-slate-400">No suppliers.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        {edit_modal}
    """
    return render_layout("Supplier Management", content)

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if not check_permission('Expenses', 'view'): return "Access Denied", 403
    can_add = check_permission('Expenses', 'add')
    can_edit = check_permission('Expenses', 'edit') if 'check_permission' in globals() else can_add
    can_del = check_permission('Expenses', 'delete')
    
    conn = get_db_connection()
    
    # Ensure currency column exists in expenses table safely
    try:
        conn.execute('ALTER TABLE expenses ADD COLUMN currency TEXT DEFAULT "IQD"')
        conn.commit()
    except Exception:
        pass

    if request.method == 'POST':
        if 'delete_id' in request.form:
            if not can_del: return "Access Denied", 403
            exp_id = request.form['delete_id']
            
            old_exp = conn.execute('SELECT * FROM expenses WHERE id = ?', (exp_id,)).fetchone()
            conn.execute('DELETE FROM expenses WHERE id = ?', (exp_id,))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if old_exp:
                old_dict = dict(old_exp)
                e_cat = old_dict.get('category', 'General')
                e_desc = old_dict.get('description', '-') or '-'
                e_amt = float(old_dict.get('amount_iqd', 0))
                e_curr = old_dict.get('currency', 'IQD') or 'IQD'
                e_date = old_dict.get('expense_date', str(datetime.date.today()))
                
                detail_msg = f"Deleted expense: {e_cat} | Desc: {e_desc} | Amount: {e_amt:,.2f} {e_curr} | Date: {e_date}"
            else:
                detail_msg = f"Deleted expense ID {exp_id}"
                
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'DELETE_EXPENSE', detail_msg, timestamp))
                         
        elif 'edit_id' in request.form and request.form.get('edit_id'):
            if not can_edit: return "Access Denied", 403
            exp_id = request.form['edit_id']
            category = request.form['category']
            description = request.form.get('description', '').strip()
            amount = float(request.form['amount_iqd'] or 0)
            curr = request.form.get('currency', 'IQD')
            exp_date = request.form.get('expense_date') or str(datetime.date.today())
            
            old_exp = conn.execute('SELECT * FROM expenses WHERE id = ?', (exp_id,)).fetchone()
            old_dict = dict(old_exp) if old_exp else {}
            
            conn.execute('''
                UPDATE expenses 
                SET category = ?, description = ?, amount_iqd = ?, currency = ?, expense_date = ?
                WHERE id = ?
            ''', (category, description, amount, curr, exp_date, exp_id))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            old_cat = old_dict.get('category', 'General')
            old_desc = old_dict.get('description', '-') or '-'
            old_amt = float(old_dict.get('amount_iqd', 0))
            old_curr = old_dict.get('currency', 'IQD') or 'IQD'
            old_date = old_dict.get('expense_date', str(datetime.date.today()))
            
            detail_msg = (
                f"<b>Updated expense ID #{exp_id}</b><br>"
                f"Category: {old_cat} -> {category}<br>"
                f"Description: {old_desc} -> {description}<br>"
                f"Amount: {old_amt:,.2f} {old_curr} -> {amount:,.2f} {curr}<br>"
                f"Date: {old_date} -> {exp_date}"
            )
            
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'EDIT_EXPENSE', detail_msg, timestamp))
        else:
            if not can_add: return "Access Denied", 403
            category = request.form['category']
            description = request.form.get('description', '').strip()
            amount = float(request.form['amount_iqd'] or 0)
            curr = request.form.get('currency', 'IQD')
            exp_date = request.form.get('expense_date') or str(datetime.date.today())
            
            conn.execute('''
                INSERT INTO expenses (category, description, amount_iqd, amount_secondary, currency, expense_date) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (category, description, amount, 0.0, curr, exp_date))
            
            username = session.get('username', 'System')
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            detail_msg = f"Recorded expense: {category} | Desc: {description or '-'} | Amount: {amount:,.2f} {curr} | Date: {exp_date}"
            conn.execute('INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)', 
                         (username, 'ADD_EXPENSE', detail_msg, timestamp))
                         
        conn.commit()
        conn.close()
        return redirect(url_for('expenses'))
        
    expenses_list = conn.execute('SELECT * FROM expenses ORDER BY expense_date DESC').fetchall()
    categories = conn.execute('SELECT * FROM expense_categories').fetchall()
    currencies = conn.execute('SELECT * FROM currencies').fetchall()
    conn.close()
    
    cat_options = ''.join([f'<option value="{cat["name"]}">{cat["name"]}</option>' for cat in categories])
    currency_opts = ''.join([f'<option value="{cur["name"]}">{cur["name"]}</option>' for cur in currencies]) if currencies else '<option value="IQD">IQD</option><option value="USD">USD</option>'
    
    rows = ""
    for e in expenses_list:
        e_dict = dict(e)
        e_id = e_dict.get('id', 1)
        e_date = e_dict.get('expense_date', str(datetime.date.today()))
        e_cat = e_dict.get('category', 'General')
        e_desc = e_dict.get('description', '-') or '-'
        e_amt = e_dict.get('amount_iqd', 0)
        e_curr = e_dict.get('currency', 'IQD') or 'IQD'
        
        edit_btn = f'<button type="button" onclick=\'openEditExpenseModal({e_id}, "{e_cat}", "{e_desc}", "{e_amt}", "{e_curr}", "{e_date}")\' class="text-blue-600 text-xs font-medium mr-3">Edit</button>' if can_edit else ''
        db_btn = f'<form method="POST" style="display:inline;" onsubmit="return confirm(\'Delete expense?\');"><input type="hidden" name="delete_id" value="{e_id}"><button type="submit" class="text-red-600 text-xs font-medium">Delete</button></form>' if can_del else ''
        
        rows += f'<tr class="border-b dark:border-slate-800 text-sm"><td class="py-3 px-4">{e_date}</td><td class="py-3 px-4"><span class="bg-rose-50 dark:bg-rose-950 text-rose-700 dark:text-rose-300 px-2 py-0.5 rounded text-xs">{e_cat}</span></td><td class="py-3 px-4">{e_desc}</td><td class="py-3 px-4">{float(e_amt):,.2f} {e_curr}</td><td class="py-3 px-4 text-right">{edit_btn}{db_btn}</td></tr>'
        
    add_form = f"""
        <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-sm border dark:border-slate-800 h-fit">
            <h3 class="text-lg font-medium mb-4">Record Expense</h3>
            <form method="POST" class="space-y-4">
                <div><label class="block text-sm mb-1">Category</label><select name="category" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{cat_options}</select></div>
                <div><label class="block text-sm mb-1">Description</label><input type="text" name="description" class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm mb-1">Currency</label>
                        <select name="currency" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                            <option value="">-- Select --</option>
                            {currency_opts}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">Amount</label>
                        <input type="number" step="0.01" name="amount_iqd" value="0" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                    </div>
                </div>
                <div><label class="block text-sm mb-1">Date</label><input type="date" name="expense_date" value="{datetime.date.today()}" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Save Expense</button>
            </form>
        </div>
    """ if can_add else ''
    
    edit_modal = f"""
        <div id="edit_expense_modal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div class="bg-white dark:bg-slate-900 p-6 rounded-xl shadow-lg border dark:border-slate-800 w-full max-w-md">
                <h3 class="text-lg font-medium mb-4">Edit Expense</h3>
                <form method="POST" class="space-y-4">
                    <input type="hidden" name="edit_id" id="edit_exp_id">
                    <div><label class="block text-sm mb-1">Category</label><select name="category" id="edit_exp_category" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"><option value="">-- Select --</option>{cat_options}</select></div>
                    <div><label class="block text-sm mb-1">Description</label><input type="text" name="description" id="edit_exp_desc" class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-sm mb-1">Currency</label>
                            <select name="currency" id="edit_exp_curr" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                                <option value="">-- Select --</option>
                                {currency_opts}
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm mb-1">Amount</label>
                            <input type="number" step="0.01" name="amount_iqd" id="edit_exp_amount" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm">
                        </div>
                    </div>
                    <div><label class="block text-sm mb-1">Date</label><input type="date" name="expense_date" id="edit_exp_date" required class="w-full border dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white rounded-lg px-3 py-2 text-sm"></div>
                    <div class="flex space-x-3 pt-2">
                        <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm">Update Expense</button>
                        <button type="button" onclick="closeEditExpenseModal()" class="w-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 py-2 rounded-lg text-sm">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        <script>
            function openEditExpenseModal(id, category, description, amount, curr, date) {{
                document.getElementById('edit_exp_id').value = id;
                document.getElementById('edit_exp_category').value = category;
                document.getElementById('edit_exp_desc').value = description === '-' ? '' : description;
                document.getElementById('edit_exp_amount').value = amount;
                document.getElementById('edit_exp_curr').value = curr;
                document.getElementById('edit_exp_date').value = date;
                document.getElementById('edit_expense_modal').classList.remove('hidden');
            }}
            function closeEditExpenseModal() {{
                document.getElementById('edit_expense_modal').classList.add('hidden');
            }}
        </script>
    """
    
    content = f"""
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {add_form}
            <div class="{'xl:col-span-2' if can_add else 'xl:col-span-3'} bg-white dark:bg-slate-900 rounded-xl shadow-sm border dark:border-slate-800 overflow-hidden h-fit">
                <table class="w-full text-left">
                    <thead><tr class="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700 text-xs text-slate-500 uppercase"><th class="py-3 px-4">Date</th><th class="py-3 px-4">Category</th><th class="py-3 px-4">Description</th><th class="py-3 px-4">Amount</th><th class="py-3 px-4 text-right">Action</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="5" class="py-6 text-center text-slate-400">No expenses.</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        {edit_modal}
    """
    return render_layout("Expense Management", content)



@app.route('/api/log-theme', methods=['POST'])
def log_theme():
    if 'username' in session:
        log_activity('THEME_TOGGLE', 'Switched portal color theme')
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)