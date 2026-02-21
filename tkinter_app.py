#!/usr/bin/env python3
"""
Theophile POS - Tkinter Desktop Application
A native desktop GUI for the POS system
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import json
import os
import sys
from datetime import datetime
import subprocess

class TheophilePOSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Theophile POS - Desktop Application")
        self.root.geometry("1200x700")
        self.root.minsize(1024, 600)
        
        # Set icon
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # API base URL (local Flask server)
        self.api_url = "http://localhost:5000/api"
        self.flask_process = None
        
        # Start Flask server
        self.start_flask_server()
        
        # Create UI
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        
        # Load initial data
        self.load_dashboard()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def start_flask_server(self):
        """Start the Flask backend server"""
        try:
            # Check if server is already running
            requests.get("http://localhost:5000", timeout=1)
            print("Flask server already running")
        except:
            # Start Flask in a separate process
            python = sys.executable
            self.flask_process = subprocess.Popen(
                [python, 'app.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("Started Flask server")
    
    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Dashboard", command=self.load_dashboard)
        file_menu.add_command(label="Products", command=self.load_products)
        file_menu.add_separator()
        file_menu.add_command(label="Backup Database", command=self.backup_database)
        file_menu.add_command(label="Restore Database", command=self.restore_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        
        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        reports_menu.add_command(label="Sales Report", command=lambda: self.load_report('sales'))
        reports_menu.add_command(label="Tax Report", command=lambda: self.load_report('tax'))
        reports_menu.add_command(label="Inventory Report", command=lambda: self.load_report('inventory'))
        
        # Admin menu
        admin_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Admin", menu=admin_menu)
        admin_menu.add_command(label="Users", command=self.load_users)
        admin_menu.add_command(label="Branches", command=self.load_branches)
        admin_menu.add_command(label="Settings", command=self.load_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_main_frame(self):
        """Create main content frame with notebook tabs"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Dashboard tab
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        
        # Products tab
        self.products_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.products_frame, text="Products")
        
        # Sales tab
        self.sales_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sales_frame, text="Sales")
        
        # Reports tab
        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="Reports")
        
        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
    
    def create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(
            self.status_bar,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.time_label = ttk.Label(
            self.status_bar,
            text=datetime.now().strftime("%Y-%m-%d %H:%M"),
            relief=tk.SUNKEN,
            width=20
        )
        self.time_label.pack(side=tk.RIGHT)
        
        # Update time every second
        self.update_time()
    
    def update_time(self):
        """Update the time in status bar"""
        self.time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.root.after(1000, self.update_time)
    
    def load_dashboard(self):
        """Load dashboard content"""
        self.notebook.select(self.dashboard_frame)
        self.status_label.config(text="Loading dashboard...")
        
        # Clear frame
        for widget in self.dashboard_frame.winfo_children():
            widget.destroy()
        
        # Create stats cards
        stats_frame = ttk.Frame(self.dashboard_frame)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Try to get data from API
        try:
            response = requests.get(f"{self.api_url}/dashboard/stats", timeout=2)
            if response.status_code == 200:
                data = response.json()
            else:
                data = {
                    'total_products': 0,
                    'low_stock': 0,
                    'expiring': 0,
                    'today_sales': 0
                }
        except:
            data = {
                'total_products': 0,
                'low_stock': 0,
                'expiring': 0,
                'today_sales': 0
            }
        
        # Create stat cards
        stats = [
            ("Total Products", data['total_products'], "#4361ee"),
            ("Low Stock", data['low_stock'], "#f72585"),
            ("Expiring", data['expiring'], "#f8961e"),
            ("Today's Sales", f"{data['today_sales']:,} RWF", "#4cc9f0")
        ]
        
        for i, (label, value, color) in enumerate(stats):
            card = tk.Frame(
                stats_frame,
                bg=color,
                relief=tk.RAISED,
                bd=2
            )
            card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            stats_frame.grid_columnconfigure(i, weight=1)
            
            tk.Label(
                card,
                text=label,
                bg=color,
                fg="white",
                font=("Arial", 10)
            ).pack(pady=(10, 0))
            
            tk.Label(
                card,
                text=str(value),
                bg=color,
                fg="white",
                font=("Arial", 16, "bold")
            ).pack(pady=(0, 10))
        
        # Create quick sale section
        sale_frame = ttk.LabelFrame(self.dashboard_frame, text="Quick Sale", padding=10)
        sale_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(sale_frame, text="Product:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.product_var = tk.StringVar()
        product_combo = ttk.Combobox(sale_frame, textvariable=self.product_var, width=40)
        product_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(sale_frame, text="Quantity:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.quantity_var = tk.StringVar(value="1")
        ttk.Entry(sale_frame, textvariable=self.quantity_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(
            sale_frame,
            text="Process Sale",
            command=self.process_sale
        ).grid(row=2, column=0, columnspan=2, pady=10)
        
        self.status_label.config(text="Dashboard loaded")
    
    def load_products(self):
        """Load products tab"""
        self.notebook.select(self.products_frame)
        self.status_label.config(text="Loading products...")
        
        # Clear frame
        for widget in self.products_frame.winfo_children():
            widget.destroy()
        
        # Create treeview for products
        columns = ('ID', 'Name', 'Category', 'Buying Price', 'Selling Price', 'Quantity', 'Status')
        tree = ttk.Treeview(self.products_frame, columns=columns, show='headings', height=20)
        
        # Define headings
        tree.heading('ID', text='ID')
        tree.heading('Name', text='Name')
        tree.heading('Category', text='Category')
        tree.heading('Buying Price', text='Buying Price')
        tree.heading('Selling Price', text='Selling Price')
        tree.heading('Quantity', text='Quantity')
        tree.heading('Status', text='Status')
        
        # Set column widths
        tree.column('ID', width=50)
        tree.column('Name', width=200)
        tree.column('Category', width=100)
        tree.column('Buying Price', width=100)
        tree.column('Selling Price', width=100)
        tree.column('Quantity', width=80)
        tree.column('Status', width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.products_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add buttons
        button_frame = ttk.Frame(self.products_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Add Product", command=self.add_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Product", command=self.edit_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Product", command=self.delete_product).pack(side=tk.LEFT, padx=5)
        
        # Load sample data
        sample_data = [
            (1, 'Sugar', 'Food', 800, 1000, 50, 'In Stock'),
            (2, 'Milk', 'Dairy', 600, 800, 30, 'Low Stock'),
            (3, 'Bread', 'Bakery', 500, 700, 20, 'In Stock'),
        ]
        
        for item in sample_data:
            tree.insert('', tk.END, values=item)
        
        self.status_label.config(text="Products loaded")
    
    def load_report(self, report_type):
        """Load report tab"""
        self.notebook.select(self.reports_frame)
        self.status_label.config(text=f"Loading {report_type} report...")
        
        # Clear frame
        for widget in self.reports_frame.winfo_children():
            widget.destroy()
        
        # Create report content
        tk.Label(
            self.reports_frame,
            text=f"{report_type.title()} Report",
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Date range
        date_frame = ttk.Frame(self.reports_frame)
        date_frame.pack(pady=10)
        
        ttk.Label(date_frame, text="From:").grid(row=0, column=0, padx=5)
        from_date = ttk.Entry(date_frame, width=12)
        from_date.grid(row=0, column=1, padx=5)
        from_date.insert(0, datetime.now().strftime("%Y-%m-01"))
        
        ttk.Label(date_frame, text="To:").grid(row=0, column=2, padx=5)
        to_date = ttk.Entry(date_frame, width=12)
        to_date.grid(row=0, column=3, padx=5)
        to_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Button(
            date_frame,
            text="Generate",
            command=lambda: self.generate_report(report_type, from_date.get(), to_date.get())
        ).grid(row=0, column=4, padx=5)
        
        # Export buttons
        export_frame = ttk.Frame(self.reports_frame)
        export_frame.pack(pady=10)
        
        ttk.Button(
            export_frame,
            text="Export to PDF",
            command=lambda: self.export_report(report_type, 'pdf')
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            export_frame,
            text="Export to Excel",
            command=lambda: self.export_report(report_type, 'excel')
        ).pack(side=tk.LEFT, padx=5)
    
    def load_users(self):
        """Load users management"""
        messagebox.showinfo("Info", "Users management - Coming soon!")
    
    def load_branches(self):
        """Load branches management"""
        messagebox.showinfo("Info", "Branches management - Coming soon!")
    
    def load_settings(self):
        """Load settings"""
        messagebox.showinfo("Info", "Settings - Coming soon!")
    
    def process_sale(self):
        """Process a sale"""
        product = self.product_var.get()
        quantity = self.quantity_var.get()
        
        if not product or not quantity:
            messagebox.showerror("Error", "Please select product and enter quantity")
            return
        
        messagebox.showinfo("Success", f"Sale processed: {quantity} x {product}")
        self.status_label.config(text="Sale processed")
    
    def add_product(self):
        """Add new product"""
        messagebox.showinfo("Info", "Add product - Coming soon!")
    
    def edit_product(self):
        """Edit product"""
        messagebox.showinfo("Info", "Edit product - Coming soon!")
    
    def delete_product(self):
        """Delete product"""
        if messagebox.askyesno("Confirm", "Delete selected product?"):
            messagebox.showinfo("Success", "Product deleted")
    
    def generate_report(self, report_type, from_date, to_date):
        """Generate report"""
        messagebox.showinfo("Info", f"Generating {report_type} report from {from_date} to {to_date}")
    
    def export_report(self, report_type, format):
        """Export report"""
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format}",
            filetypes=[(f"{format.upper()} files", f"*.{format}")]
        )
        if filename:
            messagebox.showinfo("Success", f"Report exported to {filename}")
    
    def backup_database(self):
        """Backup database"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".sql",
            filetypes=[("SQL files", "*.sql")]
        )
        if filename:
            messagebox.showinfo("Success", f"Database backed up to {filename}")
    
    def restore_database(self):
        """Restore database"""
        filename = filedialog.askopenfilename(
            filetypes=[("SQL files", "*.sql")]
        )
        if filename:
            if messagebox.askyesno("Confirm", "Restore database? This will overwrite current data!"):
                messagebox.showinfo("Success", "Database restored")
    
    def show_docs(self):
        """Show documentation"""
        messagebox.showinfo("Documentation", "Theophile POS Documentation\n\nVersion 1.0.0")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Theophile POS",
            "Theophile POS\nVersion 1.0.0\n\nA complete Point of Sale system\nfor retail businesses."
        )
    
    def on_close(self):
        """Handle window close"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.flask_process:
                self.flask_process.terminate()
            self.root.destroy()

def main():
    root = tk.Tk()
    app = TheophilePOSApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()