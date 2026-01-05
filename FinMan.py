import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkcalendar import DateEntry
import json
import csv
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os
import math

class FinanceManager:
    
    
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Manager")
        self.root.geometry("1500x950")
        
        self.data_file = "finance_data.json"
        self.initial_euro_balance = 0.0
        
        # --- 1. INITIALIZE EVERY TKINTER VARIABLE FIRST (CRITICAL) ---
        
        # Database Tab Variables
        self.db_year_var = tk.StringVar(value=str(datetime.now().year))
        self.subcat_filter_cat_var = tk.StringVar()
        self.subsub_filter_cat_var = tk.StringVar()
        self.subsub_filter_sub_var = tk.StringVar()
        
        # Analysis Tab (Euro) Variables
        self.analysis_year_var = tk.StringVar(value=str(datetime.now().year))
        self.analysis_month_var = tk.StringVar(value="Whole Year")
        self.analysis_cat_var = tk.StringVar()
        self.analysis_sub_var = tk.StringVar()

        # BD Section Main Filter Variables
        self.bd_db_year_var = tk.StringVar(value=str(datetime.now().year))
        self.bd_subcat_filter_cat = tk.StringVar()
        self.bd_subsubcat_filter_cat = tk.StringVar()
        self.bd_subsubcat_filter_sub = tk.StringVar()
        
        # BD Section Analysis Tab Variables
        self.bd_ana_year_var = tk.StringVar(value=str(datetime.now().year))
        self.bd_ana_month_var = tk.StringVar(value="Whole Year")
        self.bd_ana_level_var = tk.StringVar(value="Category")
        self.bd_ana_cat_var = tk.StringVar()
        self.bd_ana_sub_var = tk.StringVar()

        # Hierarchy Manager Variables (FIX: ADDED THESE)
        self.mgr_cat_var = tk.StringVar()
        self.mgr_sub_var = tk.StringVar()
        
        # --- 2. INITIALIZE DATA STRUCTURES ---
        self.categories = ["Household cost", "Car", "Health/Medicine", "Sadaka", "Fixed/contract",
                           "Extra", "Entertainment", "Family Education", "Savings cost"]
        self.subcategories = {}
        self.transactions = [] 
        self.income_sources = []
        self.investments = []
        self.investment_returns = []
        self.investment_categories = []
        self.bd_balance = 0.0
        self.bd_conversion_rate = 140.0
        self.bd_transactions = [] 

        # --- 3. LOAD DATA AND BUILD UI ---
        self.load_data()
        self.create_widgets()
        self.auto_save()
        
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.categories = data.get('categories', self.categories)
                    
                    # Load subcategories
                    loaded_sub = data.get('subcategories', {})
                    self.subcategories = loaded_sub 
                    
                    self.transactions = data.get('transactions', [])
                    self.income_sources = data.get('income_sources', [])
                    self.investments = data.get('investments', [])
                    self.investment_returns = data.get('investment_returns', [])
                    self.investment_categories = data.get('investment_categories', [])
                    self.bd_balance = data.get('bd_balance', 0.0)
                    self.bd_conversion_rate = data.get('bd_conversion_rate', 140.0)
                    self.bd_transactions = data.get('bd_transactions', [])
                    self.initial_euro_balance = data.get('initial_euro_balance', 0.0)
                    
                    # Ensure transactions have subsubcategory field for legacy data
                    for t in self.transactions:
                        if 'subsubcategory' not in t: t['subsubcategory'] = ''
                    for t in self.bd_transactions:
                        if 'subsubcategory' not in t: t['subsubcategory'] = ''
                        
            except Exception as e:
                print(f"Load error: {e}")
                pass


    
    
    def save_data(self):
        data = {
            'categories': self.categories, 'subcategories': self.subcategories,
            'transactions': self.transactions, 'income_sources': self.income_sources,
            'investments': self.investments, 'investment_returns': self.investment_returns,
            'investment_categories': self.investment_categories, 'bd_balance': self.bd_balance,
            'bd_conversion_rate': self.bd_conversion_rate, 'bd_transactions': self.bd_transactions, 
            'initial_euro_balance': self.initial_euro_balance,
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Auto-CSV Save
        self.export_to_csv_auto()
        self.update_input_summary_table() # This updates the Matrix
        if hasattr(self, 'bd_taka_label'): 
            self.update_bd_display()      # This updates the BD Tab
        

    def export_to_csv_auto(self):
        """Automatically saves all transactions to CSV file"""
        with open("finance_backup.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Type", "Date", "Category", "Subcategory", "Sub-Sub", "Amount", "Currency"])
            for t in self.transactions:
                writer.writerow(["Euro Exp", t['date'], t['category'], t['subcategory'], t.get('subsubcategory',''), t['amount'], "EUR"])
            for t in self.bd_transactions:
                writer.writerow(["BD Exp", t['date'], t['category'], t['subcategory'], t.get('subsubcategory',''), t['amount'], "BDT"])

    def propagate_rename(self, level, old_name, new_name, p_cat=None, p_sub=None):
        """Updates all existing transaction records when a name is edited"""
        target_lists = [self.transactions, self.bd_transactions]
        for t_list in target_lists:
            for t in t_list:
                if level == 'cat' and t.get('category') == old_name:
                    t['category'] = new_name
                elif level == 'sub' and t.get('category') == p_cat and t.get('subcategory') == old_name:
                    t['subcategory'] = new_name
                elif level == 'subsub' and t.get('category') == p_cat and t.get('subcategory') == p_sub and t.get('subsubcategory') == old_name:
                    t['subsubcategory'] = new_name

    def auto_export_csv_backup(self):
        """Generates a flat CSV file of all transactions for Excel/External use"""
        try:
            with open("finance_data_backup.csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Type', 'Date', 'Category', 'Subcategory', 'Sub-Subcategory', 'Amount', 'Currency', 'Details'])
                
                # Euro Expenses
                for t in self.transactions:
                    writer.writerow(['Euro Expense', t.get('date'), t.get('category'), t.get('subcategory'), t.get('subsubcategory'), t.get('amount'), 'EUR', t.get('location', '')])
                
                # BD Expenses
                for t in self.bd_transactions:
                    writer.writerow(['BD Expense', t.get('date'), t.get('category'), t.get('subcategory'), t.get('subsubcategory'), t.get('amount'), 'BDT', ''])
                
                # Income
                for i in self.income_sources:
                    writer.writerow(['Income', i.get('date'), 'Income', i.get('source'), '', i.get('amount'), 'EUR', ''])
        except Exception as e:
            print(f"Auto-CSV Error: {e}")

    def update_subsubcategory_table(self):
        #"""Sub-Subcategory View: Month rows vs Sub-Subcategories in Columns"""
        for item in self.subsub_tree.get_children():
            self.subsub_tree.delete(item)

        year = self.db_year_var.get()
        cat = self.subsub_filter_cat_var.get()
        sub = self.subsub_filter_sub_var.get()
        
        if not cat or not sub:
            messagebox.showwarning("Filter", "Please select Category and Subcategory")
            return

        # Get the sub-sub items list
        ss_list = self.subcategories.get(cat, {}).get(sub, [])
        
        columns = ['Month'] + ss_list + ['Total']
        self.subsub_tree['columns'] = columns
        self.subsub_tree['show'] = 'headings'
        
        for col in columns:
            self.subsub_tree.heading(col, text=col)
            self.subsub_tree.column(col, width=100, anchor='center')
        
        # Clear existing rows using the correct name
        for item in self.subsub_tree.get_children():
            self.subsub_tree.delete(item)

        # Calculate Matrix logic...
        matrix = defaultdict(lambda: defaultdict(float))
        for t in self.transactions:
            if t.get('date', '').endswith(year) and t.get('category') == cat and t.get('subcategory') == sub:
                try:
                    m_idx = int(t['date'].split('/')[1])
                    ss = t.get('subsubcategory')
                    if ss in ss_list:
                        matrix[m_idx][ss] += float(t.get('amount', 0))
                except: continue

        # Render rows using the correct name
        self._render_database_rows(self.subsub_tree, ss_list, matrix)
        
    
    
    def auto_save(self):
        self.save_data()
        self.root.after(30000, self.auto_save)
    
    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Input
        self.input_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.input_tab, text="Input")
        self.create_input_tab()
        
        # Tab 2: Database
        self.database_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.database_tab, text="Database")
        self.create_database_tab()
        
        # Tab 3: Investments
        self.investment_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.investment_tab, text="Investments")
        self.create_investment_tab()
        
        # Tab 4: BD Section
        self.bd_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.bd_tab, text="BD Section")
        self.create_bd_tab()
        
        # Tab 5: Analysis
        self.analysis_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_tab, text="Analysis")
        self.create_analysis_tab() # RESTORED
        
    def set_initial_balance(self):
        try:
            val = float(self.initial_bal_entry.get())
            self.initial_euro_balance = val
            self.save_data()
            self.update_input_summary_table()
            messagebox.showinfo("Success", f"Initial balance set to €{val:.2f}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for initial balance.")
            
    def create_input_tab(self):
        # Header
        header_frame = ttk.Frame(self.input_tab, height=150) 
        header_frame.pack(fill='x', padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        header_canvas = tk.Canvas(header_frame, height=150, bg='#E8F5E9', highlightthickness=0)
        header_canvas.pack(fill='both', expand=True)
        
        # Sun
        sun_x, sun_y = 120, 40
        header_canvas.create_oval(sun_x-25, sun_y-25, sun_x+25, sun_y+25, 
                                 fill='#FFD54F', outline='#FFA000', width=2)
        for angle in range(0, 360, 45):
            angle_rad = math.radians(angle)
            x1 = sun_x + 30 * math.cos(angle_rad)
            y1 = sun_y + 30 * math.sin(angle_rad)
            x2 = sun_x + 40 * math.cos(angle_rad)
            y2 = sun_y + 40 * math.sin(angle_rad)
            header_canvas.create_line(x1, y1, x2, y2, fill='#FFA000', width=3)
        
        # Tree
        trunk_x, trunk_y = 80, 120
        header_canvas.create_rectangle(trunk_x-8, trunk_y-20, trunk_x+8, trunk_y, 
                                       fill='#6D4C41', outline='#4E342E', width=2)
        foliage_positions = [(trunk_x, trunk_y-30, 20), (trunk_x-15, trunk_y-25, 18), 
                             (trunk_x+15, trunk_y-25, 18), (trunk_x-8, trunk_y-40, 16), 
                             (trunk_x+8, trunk_y-40, 16), (trunk_x, trunk_y-50, 15)]
        for x, y, r in foliage_positions:
            header_canvas.create_oval(x-r, y-r, x+r, y+r, 
                                     fill='#4CAF50', outline='#388E3C', width=1)
        
        # Clock
        clock_x, clock_y = 400, 75
        self.header_clock_canvas = tk.Canvas(header_canvas, width=120, height=120, 
                                            bg='#E8F5E9', highlightthickness=0)
        header_canvas.create_window(clock_x, clock_y, window=self.header_clock_canvas)
        
        blessing_text = "In name of Allah,\nwho is Most Gracious and Most Merciful"
        header_canvas.create_text(700, 75, text=blessing_text, 
                                 font=('Times New Roman', 14, 'italic bold'),
                                 fill='#1B5E20', justify='center')
        
        # Date Display
        date_frame = ttk.LabelFrame(self.input_tab, text="Current Date & Time", padding=10)
        date_frame.pack(fill='x', padx=10, pady=5)
        
        date_info_frame = ttk.Frame(date_frame)
        date_info_frame.pack(padx=20, fill='x')
        
        current_date = datetime.now()
        self.weekday_label = ttk.Label(date_info_frame, text=f"Day: {current_date.strftime('%A')}", 
                                      font=('Arial', 11, 'bold'))
        self.weekday_label.pack(side='left', padx=20)
        self.date_label = ttk.Label(date_info_frame, text=f"Date: {current_date.strftime('%d/%m/%Y')}", 
                                   font=('Arial', 10))
        self.date_label.pack(side='left', padx=20)
        self.month_label = ttk.Label(date_info_frame, text=f"Month: {current_date.strftime('%B %Y')}", 
                                    font=('Arial', 10))
        self.month_label.pack(side='left', padx=20)
        self.time_label = ttk.Label(date_info_frame, text=f"Time: {current_date.strftime('%H:%M:%S')}", 
                                   font=('Arial', 10))
        self.time_label.pack(side='left', padx=20)
        
        self.update_clocks()
        
        # Category Management
        cat_frame = ttk.LabelFrame(self.input_tab, text="Category Management", padding=10)
        cat_frame.pack(fill='x', padx=10, pady=5)
        ttk.Button(cat_frame, text="Manage Subcategories (Sub-Sub)", command=self.manage_subcategories).pack(side='left', padx=5)
        ttk.Button(cat_frame, text="Add Category", command=self.add_category).pack(side='left', padx=5)
        
        # Forms Container
        forms_container = ttk.Frame(self.input_tab)
        forms_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Income Section
        income_frame = ttk.LabelFrame(forms_container, text="Add Income", padding=10)
        income_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        ttk.Label(income_frame, text="Source:").grid(row=0, column=0, sticky='w', pady=2)
        self.income_source_var = tk.StringVar(value="Salary")
        income_source_combo = ttk.Combobox(income_frame, textvariable=self.income_source_var, 
                                           values=["Salary", "Profit", "Return", "Other"])
        income_source_combo.grid(row=0, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(income_frame, text="Amount (€):").grid(row=1, column=0, sticky='w', pady=2)
        self.income_amount = ttk.Entry(income_frame)
        self.income_amount.grid(row=1, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(income_frame, text="Date:").grid(row=2, column=0, sticky='w', pady=2)
        self.income_date = DateEntry(income_frame, date_pattern='dd/mm/yyyy')
        self.income_date.grid(row=2, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Button(income_frame, text="Add Income", command=self.add_income).grid(row=3, column=0, columnspan=2, pady=10)
        self.current_month_income_label = ttk.Label(income_frame, text="Current Month Income: €0.00", 
                                                     font=('Arial', 11, 'bold'))
        self.current_month_income_label.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Add these lines at the bottom of the income_frame (around line 430)
        ttk.Separator(income_frame, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Label(income_frame, text="Set Initial Balance (€):").grid(row=6, column=0, sticky='w', pady=2)
        self.initial_bal_entry = ttk.Entry(income_frame)
        self.initial_bal_entry.insert(0, str(self.initial_euro_balance))
        self.initial_bal_entry.grid(row=6, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Button(income_frame, text="Update Initial Balance", 
                   command=self.set_initial_balance).grid(row=7, column=0, columnspan=2, pady=5)
        
        # Expenditure Section
        expense_frame = ttk.LabelFrame(forms_container, text="Add Expenditure", padding=10)
        expense_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        ttk.Label(expense_frame, text="Category:").grid(row=0, column=0, sticky='w', pady=2)
        self.expense_category_var = tk.StringVar()
        self.expense_category_combo = ttk.Combobox(expense_frame, textvariable=self.expense_category_var)
        self.expense_category_combo.grid(row=0, column=1, sticky='ew', pady=2, padx=5)
        self.expense_category_combo.bind('<<ComboboxSelected>>', self.update_subcategory_combo)
        
        ttk.Label(expense_frame, text="Subcategory:").grid(row=1, column=0, sticky='w', pady=2)
        self.expense_subcategory_var = tk.StringVar()
        self.expense_subcategory_combo = ttk.Combobox(expense_frame, textvariable=self.expense_subcategory_var)
        self.expense_subcategory_combo.grid(row=1, column=1, sticky='ew', pady=2, padx=5)
        self.expense_subcategory_combo.bind('<<ComboboxSelected>>', self.update_subsubcategory_combo)
        
        ttk.Label(expense_frame, text="Sub-subcategory:").grid(row=2, column=0, sticky='w', pady=2)
        self.expense_subsubcategory_var = tk.StringVar()
        self.expense_subsubcategory_combo = ttk.Combobox(expense_frame, textvariable=self.expense_subsubcategory_var)
        self.expense_subsubcategory_combo.grid(row=2, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(expense_frame, text="Location:").grid(row=3, column=0, sticky='w', pady=2)
        self.expense_location = ttk.Entry(expense_frame)
        self.expense_location.grid(row=3, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(expense_frame, text="Amount (€):").grid(row=4, column=0, sticky='w', pady=2)
        self.expense_amount = ttk.Entry(expense_frame)
        self.expense_amount.grid(row=4, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(expense_frame, text="Date:").grid(row=5, column=0, sticky='w', pady=2)
        self.expense_date = DateEntry(expense_frame, date_pattern='dd/mm/yyyy')
        self.expense_date.grid(row=5, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Button(expense_frame, text="Add Expenditure", command=self.add_expenditure).grid(row=6, column=0, columnspan=2, pady=10)
        
        # Summary Table
        summary_frame = ttk.LabelFrame(self.input_tab, text="Financial Summary (Monthly Matrix)", padding=10)
        summary_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.current_bd_balance_label = ttk.Label(summary_frame, text="BD Current Balance: 0.00 Taka", 
                                               font=('Arial', 12, 'bold'), foreground='green')
        self.current_bd_balance_label.pack(side='right', padx=10)
        
        columns = ('month', 'income', 'expense', 'net_invest', 'bd_expense', 'balance')
        self.summary_tree = ttk.Treeview(summary_frame, columns=columns, show='headings', height=8)
        
        self.summary_tree.heading('month', text='Month')
        self.summary_tree.heading('income', text='Income (€)')
        self.summary_tree.heading('expense', text='Expense (€)')
        self.summary_tree.heading('net_invest', text='Investment (€)')
        self.summary_tree.heading('bd_expense', text='BD Exp (Tk)')
        self.summary_tree.heading('balance', text='Balance (€)')
        
        self.summary_tree.column('month', width=100, anchor='center')
        self.summary_tree.column('income', width=100, anchor='center')
        self.summary_tree.column('expense', width=100, anchor='center')
        self.summary_tree.column('net_invest', width=100, anchor='center')
        self.summary_tree.column('bd_expense', width=100, anchor='center')
        self.summary_tree.column('balance', width=100, anchor='center')
        
        self.summary_tree.tag_configure('even', background='#ffffff')
        self.summary_tree.tag_configure('odd', background='#f2f2f2')
        self.summary_tree.tag_configure('total', background='#d0e0ff', font=('Arial', 10, 'bold'))
        self.summary_tree.tag_configure('average', background='#e6e6fa', font=('Arial', 10, 'bold'))
        
        vs = ttk.Scrollbar(summary_frame, orient="vertical", command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=vs.set)
        
        self.summary_tree.pack(side='left', fill='both', expand=True)
        vs.pack(side='right', fill='y')
        
        self.update_category_combos()
        self.update_current_month_income()
        self.update_input_summary_table()
        
        

    # --- Defensive Updates to prevent Crash ---
    def update_subcategory_combo(self, event=None):
        cat = self.expense_category_var.get()
        cat_data = self.subcategories.get(cat, {})
        
        if isinstance(cat_data, dict):
            subs = list(cat_data.keys())
        elif isinstance(cat_data, list):
            subs = cat_data
        else:
            subs = []
            
        self.expense_subcategory_combo['values'] = subs
        self.expense_subcategory_var.set('')
        self.update_subsubcategory_combo()

    def update_subsubcategory_combo(self, event=None):
        cat = self.expense_category_var.get()
        sub = self.expense_subcategory_var.get()
        
        sub_data = self.subcategories.get(cat, {}).get(sub, [])
        
        if isinstance(sub_data, list):
            pass
        else:
            sub_data = []
            
        self.expense_subsubcategory_combo['values'] = sub_data
        self.expense_subsubcategory_var.set('')
    
        
    def update_input_summary_table(self):
        """Refreshes the Matrix with the specific Balance formula:
           Balance = Income - Expense + Net_Invest - (BD_Expense / Conversion)
        """
        if not hasattr(self, 'summary_tree'): return
        
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        
        # Header display for BD
        euro_eq = self.bd_balance / self.bd_conversion_rate if self.bd_conversion_rate > 0 else 0
        self.current_bd_balance_label.config(
            text=f"BD Balance: {self.bd_balance:.2f} Taka (≈{euro_eq:.2f} €)"
        )

        current_year = self.db_year_var.get()
        rate = self.bd_conversion_rate if self.bd_conversion_rate > 0 else 1.0
        
        # Use a dictionary to store all values for 12 months
        months_data = defaultdict(lambda: {
            'income': 0.0, 'expense': 0.0, 'invest_out': 0.0, 
            'returns': 0.0, 'bd_expense': 0.0
        })

        # --- 1. Aggregation (Filter by current_year) ---
        for inc in self.income_sources:
            if inc['date'].endswith(current_year):
                m = int(inc['date'].split('/')[1])
                months_data[m]['income'] += float(inc['amount'])
        
        for exp in self.transactions:
            if exp['date'].endswith(current_year) and exp.get('category') != "Savings cost":
                m = int(exp['date'].split('/')[1])
                months_data[m]['expense'] += float(exp['amount'])
                
        for inv in self.investments:
            if inv['date'].endswith(current_year):
                m = int(inv['date'].split('/')[1])
                months_data[m]['invest_out'] += float(inv['amount'])
        
        for ret in self.investment_returns:
            if ret['date'].endswith(current_year):
                m = int(ret['date'].split('/')[1])
                months_data[m]['returns'] += float(ret['amount'])
                
        for bd_exp in self.bd_transactions:
            if bd_exp['date'].endswith(current_year):
                m = int(bd_exp['date'].split('/')[1])
                months_data[m]['bd_expense'] += float(bd_exp['amount'])

        # --- 2. Calculation and Rendering ---
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        
        totals = defaultdict(float)
        for i, m_name in enumerate(month_names):
            m_num = i + 1
            d = months_data[m_num]
            
            # MATH LOGIC:
            # 1. Net Investment Income
            net_invest_inc = d['returns'] - d['invest_out']
            
            # 2. Convert Taka expense to Euro for the balance calculation
            bd_exp_euro = d['bd_expense'] / rate
            
            # 3. Final Formula: Income - Expense + Net_Invest - BD_Exp(converted)
            month_balance = d['income'] - d['expense'] + net_invest_inc - bd_exp_euro
            
            self.summary_tree.insert('', 'end', values=(
                m_name,
                f"{d['income']:.2f}",
                f"{d['expense']:.2f}",
                f"{net_invest_inc:.2f}",
                f"{d['bd_expense']:.0f}", # Shown in Taka
                f"{month_balance:.2f}"   # Result in Euro
            ), tags=('even' if i % 2 == 0 else 'odd'))
            
            # Update Grand Totals (Summing everything for the year)
            totals['income'] += d['income']
            totals['expense'] += d['expense']
            totals['net_invest'] += net_invest_inc
            totals['bd_expense'] += d['bd_expense']
            totals['balance'] += month_balance

        # --- 3. Final Footer Rows ---
        # Inside update_input_summary_table, locate the totals['balance'] part
        # Change the TOTAL row insertion to:
        
        total_bal_with_initial = totals['balance'] + self.initial_euro_balance
        
        self.summary_tree.insert('', 'end', values=(
            "TOTAL", 
            f"{totals['income']:.2f}", 
            f"{totals['expense']:.2f}",
            f"{totals['net_invest']:.2f}", 
            f"{totals['bd_expense']:.0f}",
            f"{total_bal_with_initial:.2f}" # This now includes the starting money
        ), tags=('summary',))
        
        # self.summary_tree.insert('', 'end', values=(
        #     "TOTAL", 
        #     f"{totals['income']:.2f}", 
        #     f"{totals['expense']:.2f}",
        #     f"{totals['net_invest']:.2f}", 
        #     f"{totals['bd_expense']:.0f}",
        #     f"{totals['balance']:.2f}"
        # ), tags=('summary',))

        self.summary_tree.insert('', 'end', values=(
            "AVERAGE", 
            f"{totals['income']/12:.2f}", 
            f"{totals['expense']/12:.2f}",
            f"{totals['net_invest']/12:.2f}", 
            f"{totals['bd_expense']/12:.0f}",
            f"{totals['balance']/12:.2f}"
        ), tags=('summary',))

        self.summary_tree.tag_configure('summary', background='#d0e0ff', font=('Arial', 9, 'bold'))
        
        
  

    # --- Helper Methods (Input) ---

    def manage_subcategories(self):
        """Hierarchy Manager with full Rename and Delete functionality for all 3 levels"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit & Manage Hierarchy")
        dialog.geometry("1100x650")
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # --- LEFT: CATEGORY & SUBCATEGORY MANAGEMENT ---
        left_panel = ttk.LabelFrame(main_frame, text="1. Main Categories & Subcategories", padding=10)
        left_panel.pack(side='left', fill='y', padx=5)
        
        # Category Controls
        ttk.Label(left_panel, text="Select Main Category:").pack(anchor='w')
        cat_row = ttk.Frame(left_panel)
        cat_row.pack(fill='x', pady=2)
        
        self.mgr_cat_combo = ttk.Combobox(cat_row, textvariable=self.mgr_cat_var, values=self.categories, state="readonly")
        self.mgr_cat_combo.pack(side='left', fill='x', expand=True)
        ttk.Button(cat_row, text="✎", width=3, command=self.rename_category).pack(side='left', padx=2)
        ttk.Button(cat_row, text="❌", width=3, command=self.delete_category).pack(side='left', padx=2)
        self.mgr_cat_combo.bind("<<ComboboxSelected>>", self.mgr_update_subs)
        
        ttk.Separator(left_panel, orient='horizontal').pack(fill='x', pady=15)
        
        # Subcategory Controls
        ttk.Label(left_panel, text="Select Subcategory:").pack(anchor='w')
        sub_row = ttk.Frame(left_panel)
        sub_row.pack(fill='x', pady=2)
        
        self.mgr_sub_combo = ttk.Combobox(sub_row, textvariable=self.mgr_sub_var, state="readonly")
        self.mgr_sub_combo.pack(side='left', fill='x', expand=True)
        ttk.Button(sub_row, text="✎", width=3, command=self.rename_subcategory).pack(side='left', padx=2)
        ttk.Button(sub_row, text="❌", width=3, command=self.delete_subcategory).pack(side='left', padx=2)
        self.mgr_sub_combo.bind("<<ComboboxSelected>>", self.refresh_mgr_list)

        # Add New Subcategory
        ttk.Label(left_panel, text="Add New Subcategory:", font=('', 9, 'italic')).pack(anchor='w', pady=(15,0))
        self.new_sub_entry = ttk.Entry(left_panel)
        self.new_sub_entry.pack(fill='x', pady=5)
        ttk.Button(left_panel, text="+ Create Subcategory", command=self.mgr_add_subcategory).pack(fill='x')

        # --- RIGHT: SUB-SUBCATEGORY MANAGEMENT ---
        right_panel = ttk.LabelFrame(main_frame, text="2. Sub-Subcategories", padding=10)
        right_panel.pack(side='left', fill='both', expand=True, padx=5)
        
        add_ss_frame = ttk.Frame(right_panel)
        add_ss_frame.pack(fill='x', pady=5)
        self.new_subsub_entry = ttk.Entry(add_ss_frame)
        self.new_subsub_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(add_ss_frame, text="+ Add Item", command=self.mgr_add_sub_subcategory).pack(side='right')

        self.mgr_tree = ttk.Treeview(right_panel, columns=('Name'), show='headings')
        self.mgr_tree.heading('Name', text='Current Sub-Subcategory Items')
        self.mgr_tree.pack(fill='both', expand=True, pady=5)
        
        btn_ss_frame = ttk.Frame(right_panel)
        btn_ss_frame.pack(fill='x')
        ttk.Button(btn_ss_frame, text="Rename Selected", command=self.rename_subsubcategory).pack(side='left', padx=5)
        ttk.Button(btn_ss_frame, text="Delete Selected", command=self.delete_subsubcategory).pack(side='left', padx=5)
        
        if self.categories:
            self.mgr_cat_combo.current(0)
            self.mgr_update_subs()

    
    def propagate_name_change(self, level, old_val, new_val, parent_cat=None, parent_sub=None):
        """Standard helper to ensure existing database records match new names"""
        count = 0
        all_lists = [self.transactions, self.bd_transactions]
        for t_list in all_lists:
            for t in t_list:
                if level == 'category' and t.get('category') == old_val:
                    t['category'] = new_val
                    count += 1
                elif level == 'subcategory' and t.get('category') == parent_cat and t.get('subcategory') == old_val:
                    t['subcategory'] = new_val
                    count += 1
                elif level == 'subsubcategory' and t.get('category') == parent_cat and t.get('subcategory') == parent_sub and t.get('subsubcategory') == old_val:
                    t['subsubcategory'] = new_val
                    count += 1
        return count

    # --- CATEGORY ACTIONS ---
    def rename_category(self):
        old_name = self.mgr_cat_var.get()
        if not old_name: return
        new_name = simpledialog.askstring("Rename", f"Rename Category '{old_name}' to:", initialvalue=old_name)
        if new_name and new_name != old_name:
            idx = self.categories.index(old_name)
            self.categories[idx] = new_name
            self.subcategories[new_name] = self.subcategories.pop(old_name)
            self.propagate_name_change('category', old_name, new_name)
            self.save_data()
            self.mgr_cat_combo['values'] = self.categories
            self.mgr_cat_var.set(new_name)
            self.update_category_combos()
            messagebox.showinfo("Success", "Category renamed throughout database.")

    def delete_category(self):
        cat = self.mgr_cat_var.get()
        if not cat or not messagebox.askyesno("Confirm", f"Delete '{cat}' and ALL its transaction history?"): return
        self.categories.remove(cat)
        self.subcategories.pop(cat, None)
        self.transactions = [t for t in self.transactions if t.get('category') != cat]
        self.bd_transactions = [t for t in self.bd_transactions if t.get('category') != cat]
        self.save_data()
        self.mgr_cat_combo['values'] = self.categories
        self.mgr_cat_var.set('')
        self.mgr_update_subs()

    # --- SUBCATEGORY ACTIONS ---
    def rename_subcategory(self):
        cat = self.mgr_cat_var.get()
        old_sub = self.mgr_sub_var.get()
        if not cat or not old_sub: return
        new_sub = simpledialog.askstring("Rename", f"Rename Subcategory '{old_sub}' to:", initialvalue=old_sub)
        if new_sub and new_sub != old_sub:
            self.subcategories[cat][new_sub] = self.subcategories[cat].pop(old_sub)
            self.propagate_name_change('subcategory', old_sub, new_sub, parent_cat=cat)
            self.save_data()
            self.mgr_update_subs()
            self.mgr_sub_var.set(new_sub)

    def delete_subcategory(self):
        cat = self.mgr_cat_var.get()
        sub = self.mgr_sub_var.get()
        if not cat or not sub or not messagebox.askyesno("Confirm", f"Delete Subcategory '{sub}'?"): return
        self.subcategories[cat].pop(sub, None)
        self.transactions = [t for t in self.transactions if not (t.get('category') == cat and t.get('subcategory') == sub)]
        self.bd_transactions = [t for t in self.bd_transactions if not (t.get('category') == cat and t.get('subcategory') == sub)]
        self.save_data()
        self.mgr_update_subs()

    # --- SUB-SUBCATEGORY ACTIONS ---
    def rename_subsubcategory(self):
        selection = self.mgr_tree.selection()
        if not selection: return
        old_val = self.mgr_tree.item(selection[0])['values'][0]
        cat, sub = self.mgr_cat_var.get(), self.mgr_sub_var.get()
        new_val = simpledialog.askstring("Rename", f"Rename '{old_val}' to:", initialvalue=old_val)
        if new_val and new_val != old_val:
            idx = self.subcategories[cat][sub].index(old_val)
            self.subcategories[cat][sub][idx] = new_val
            self.propagate_name_change('subsubcategory', old_val, new_val, parent_cat=cat, parent_sub=sub)
            self.save_data()
            self.refresh_mgr_list()

    def delete_subsubcategory(self):
        selection = self.mgr_tree.selection()
        if not selection: return
        val = self.mgr_tree.item(selection[0])['values'][0]
        cat, sub = self.mgr_cat_var.get(), self.mgr_sub_var.get()
        if messagebox.askyesno("Confirm", f"Delete item '{val}'?"):
            self.subcategories[cat][sub].remove(val)
            self.transactions = [t for t in self.transactions if not (t.get('category')==cat and t.get('subcategory')==sub and t.get('subsubcategory')==val)]
            self.bd_transactions = [t for t in self.bd_transactions if not (t.get('category')==cat and t.get('subcategory')==sub and t.get('subsubcategory')==val)]
            self.save_data()
            self.refresh_mgr_list()
            
    


    def rename_item(self, level):
        cat = self.mgr_cat_var.get()
        sub = self.mgr_sub_var.get()
        
        if level == 'cat':
            old = cat
            new = simpledialog.askstring("Rename", f"Rename Category '{old}':")
            if new:
                self.categories[self.categories.index(old)] = new
                self.subcategories[new] = self.subcategories.pop(old)
                self.propagate_rename('cat', old, new)
        elif level == 'sub':
            old = sub
            new = simpledialog.askstring("Rename", f"Rename Subcategory '{old}':")
            if new:
                self.subcategories[cat][new] = self.subcategories[cat].pop(old)
                self.propagate_rename('sub', old, new, p_cat=cat)
        
        self.save_data()
        messagebox.showinfo("Success", "Renamed successfully!")
        
    def propagate_name_change2(self, level, old_val, new_val, parent_cat=None, parent_sub=None):
        """Helper to ensure existing database records match new names"""
        count = 0
        # Check both standard and BD transactions
        all_lists = [self.transactions, self.bd_transactions]
        
        for t_list in all_lists:
            for t in t_list:
                if level == 'category' and t.get('category') == old_val:
                    t['category'] = new_val
                    count += 1
                elif level == 'subcategory' and t.get('category') == parent_cat and t.get('subcategory') == old_val:
                    t['subcategory'] = new_val
                    count += 1
                elif level == 'subsubcategory' and t.get('category') == parent_cat and t.get('subcategory') == parent_sub and t.get('subsubcategory') == old_val:
                    t['subsubcategory'] = new_val
                    count += 1
        return count

    def mgr_update_subs(self, event=None):
        """Updates the subcategory dropdown based on chosen category"""
        cat = self.mgr_cat_var.get()
        # Ensure data is a dict
        if cat not in self.subcategories or not isinstance(self.subcategories[cat], dict):
            self.subcategories[cat] = {}
            
        subs = list(self.subcategories[cat].keys())
        self.mgr_sub_combo['values'] = subs
        self.mgr_sub_var.set('')
        self.refresh_mgr_list()

    def mgr_add_subcategory(self):
        """Adds the middle layer (Subcategory)"""
        cat = self.mgr_cat_var.get()
        new_sub = self.new_sub_entry.get().strip()
        
        if not cat:
            messagebox.showwarning("Warning", "Please select a Category first!")
            return
        if not new_sub:
            messagebox.showwarning("Warning", "Enter a subcategory name!")
            return
            
        if new_sub not in self.subcategories[cat]:
            self.subcategories[cat][new_sub] = []
            self.save_data()
            self.mgr_update_subs()
            self.mgr_sub_var.set(new_sub)
            self.refresh_mgr_list()
            self.new_sub_entry.delete(0, 'end')
            messagebox.showinfo("Success", f"Subcategory '{new_sub}' added!")
        else:
            messagebox.showwarning("Warning", "Subcategory already exists!")

    def mgr_add_sub_subcategory(self):
        """Adds the third layer (Sub-Subcategory)"""
        cat = self.mgr_cat_var.get()
        sub = self.mgr_sub_var.get()
        val = self.new_subsub_entry.get().strip()
        
        if not cat or not sub:
            messagebox.showwarning("Warning", "Select both Category and Subcategory!")
            return
        if not val:
            return

        if val not in self.subcategories[cat][sub]:
            self.subcategories[cat][sub].append(val)
            self.save_data()
            self.refresh_mgr_list()
            self.new_subsub_entry.delete(0, 'end')
        else:
            messagebox.showwarning("Warning", "Already exists!")

    def refresh_mgr_list(self, event=None):
        """Refreshes the treeview list of sub-subcategories"""
        for i in self.mgr_tree.get_children():
            self.mgr_tree.delete(i)
            
        cat = self.mgr_cat_var.get()
        sub = self.mgr_sub_var.get()
        
        if cat and sub:
            items = self.subcategories.get(cat, {}).get(sub, [])
            for item in items:
                self.mgr_tree.insert('', 'end', values=(item,))    
    
    def add_category(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Category")
        dialog.geometry("300x100")
        
        ttk.Label(dialog, text="Category Name:").pack(pady=10)
        entry = ttk.Entry(dialog, width=30)
        entry.pack(pady=5)
        
        def save_category():
            cat_name = entry.get().strip()
            if cat_name and cat_name not in self.categories:
                self.categories.append(cat_name)
                self.subcategories[cat_name] = {}
                self.update_category_combos()
                self.update_bd_category_combos()
                self.save_data()
                dialog.destroy()
                messagebox.showinfo("Success", "Category added successfully!")
            else:
                messagebox.showwarning("Warning", "Invalid or duplicate category name!")
        
        ttk.Button(dialog, text="Add", command=save_category).pack(pady=10)

    def update_category_combos(self):
        self.expense_category_combo['values'] = self.categories
        if self.categories:
            self.expense_category_var.set(self.categories[0])
            self.update_subcategory_combo()

    def add_income(self):
        try:
            amount = float(self.income_amount.get())
            source = self.income_source_var.get()
            date = self.income_date.get_date().strftime('%d/%m/%Y')
            
            self.income_sources.append({
                'source': source,
                'amount': amount,
                'date': date
            })
            
            self.income_amount.delete(0, 'end')
            self.save_data()
            self.update_current_month_income()
            messagebox.showinfo("Success", "Income added successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount!")
    
    def add_expenditure(self):
        try:
            category = self.expense_category_var.get()
            subcategory = self.expense_subcategory_var.get()
            subsubcategory = self.expense_subsubcategory_var.get()
            location = self.expense_location.get()
            amount = float(self.expense_amount.get())
            date = self.expense_date.get_date().strftime('%d/%m/%Y')
            
            if not category:
                messagebox.showwarning("Warning", "Please select a category!")
                return
            
            self.transactions.append({
                'type': 'expense',
                'category': category,
                'subcategory': subcategory,
                'subsubcategory': subsubcategory, 
                'location': location,
                'amount': amount,
                'date': date
            })
            
            self.expense_amount.delete(0, 'end')
            self.expense_location.delete(0, 'end')
            self.save_data()
            messagebox.showinfo("Success", "Expenditure added successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount!")
            
    def update_current_month_income(self):
        current_month = datetime.now().strftime('%m/%Y')
        total = sum(income['amount'] for income in self.income_sources 
                   if income['date'].endswith(current_month))
        self.current_month_income_label.config(text=f"Current Month Income: €{total:.2f}")
    
    def update_clocks(self):
        now = datetime.now()
        self.weekday_label.config(text=f"Day: {now.strftime('%A')}")
        self.date_label.config(text=f"Date: {now.strftime('%d/%m/%Y')}")
        self.month_label.config(text=f"Month: {now.strftime('%B %Y')}")
        self.time_label.config(text=f"Time: {now.strftime('%H:%M:%S')}")
        self.draw_clock(self.header_clock_canvas, 60, 60, 55)
        self.root.after(1000, self.update_clocks)
    
    def draw_clock(self, canvas, cx, cy, radius):
        canvas.delete("all")
        canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, 
                          outline='#1B5E20', width=3, fill='white')
        for i in range(12):
            angle = math.radians(90 - i * 30)
            x1 = cx + (radius - 12) * math.cos(angle)
            y1 = cy - (radius - 12) * math.sin(angle)
            x2 = cx + (radius - 6) * math.cos(angle)
            y2 = cy - (radius - 6) * math.sin(angle)
            canvas.create_line(x1, y1, x2, y2, width=2, fill='#1B5E20')
            num_x = cx + (radius - 20) * math.cos(angle)
            num_y = cy - (radius - 20) * math.sin(angle)
            hour_num = 12 if i == 0 else i
            canvas.create_text(num_x, num_y, text=str(hour_num), 
                             font=('Arial', 11, 'bold'), fill='#1B5E20')
        now = datetime.now()
        hour = now.hour % 12
        minute = now.minute
        second = now.second
        second_angle = math.radians(90 - second * 6)
        minute_angle = math.radians(90 - (minute * 6 + second * 0.1))
        hour_angle = math.radians(90 - (hour * 30 + minute * 0.5))
        sec_len = radius - 12
        sec_x = cx + sec_len * math.cos(second_angle)
        sec_y = cy - sec_len * math.sin(second_angle)
        canvas.create_line(cx, cy, sec_x, sec_y, fill='red', width=2)
        min_len = radius - 18
        min_x = cx + min_len * math.cos(minute_angle)
        min_y = cy - min_len * math.sin(minute_angle)
        canvas.create_line(cx, cy, min_x, min_y, fill='#1976D2', width=4)
        hour_len = radius - 28
        hour_x = cx + hour_len * math.cos(hour_angle)
        hour_y = cy - hour_len * math.sin(hour_angle)
        canvas.create_line(cx, cy, hour_x, hour_y, fill='#1B5E20', width=5)
        canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill='#1B5E20')

    # --- Database Section ---
    
        
    def create_database_tab(self):
        # --- MAIN SCROLLABLE AREA ---
        self.db_canvas = tk.Canvas(self.database_tab)
        v_scroll_main = ttk.Scrollbar(self.database_tab, orient="vertical", command=self.db_canvas.yview)
        self.db_scroll_frame = ttk.Frame(self.db_canvas)

        self.db_scroll_frame.bind(
            "<Configure>",
            lambda e: self.db_canvas.configure(scrollregion=self.db_canvas.bbox("all"))
        )

        self.db_canvas.create_window((0, 0), window=self.db_scroll_frame, anchor="nw")
        self.db_canvas.configure(yscrollcommand=v_scroll_main.set)

        v_scroll_main.pack(side="right", fill="y")
        self.db_canvas.pack(side="left", fill="both", expand=True)

        # ---------------------------------------------------------
        # TOP SECTION: FILTERS & CSV DATABASE OPERATIONS
        # ---------------------------------------------------------
        top_frame = ttk.LabelFrame(self.db_scroll_frame, text="Global Controls & CSV Database", padding=10)
        top_frame.pack(fill='x', padx=10, pady=5)
        
        # Year Filter
        filter_f = ttk.Frame(top_frame)
        filter_f.pack(side='left')
        ttk.Label(filter_f, text="Select Year:").pack(side='left', padx=5)
        ttk.Combobox(filter_f, textvariable=self.db_year_var, values=[str(y) for y in range(2020, 2031)], width=10).pack(side='left')

        ttk.Separator(top_frame, orient='vertical').pack(side='left', fill='y', padx=20)

        # NEW CSV DATABASE BUTTONS
        ttk.Button(top_frame, text="Save Database to CSV", 
                   command=self.export_csv_comprehensive).pack(side='left', padx=5)
        ttk.Button(top_frame, text="Load Database from CSV", 
                   command=self.import_csv_comprehensive).pack(side='left', padx=5)

        # ---------------------------------------------------------
        # SECTION 1: CATEGORY TABLE
        # ---------------------------------------------------------
        s1 = ttk.LabelFrame(self.db_scroll_frame, text="1. Category Overview (Year Filter)", padding=10)
        s1.pack(fill='x', padx=10, pady=10)
        ttk.Button(s1, text="Refresh Category Table", command=self.update_category_table).pack(anchor='w', pady=5)

        t1_container = ttk.Frame(s1)
        t1_container.pack(fill='x', expand=True)
        self.cat_tree = ttk.Treeview(t1_container, show='headings', height=13)
        h_scroll1 = ttk.Scrollbar(t1_container, orient="horizontal", command=self.cat_tree.xview)
        self.cat_tree.configure(xscrollcommand=h_scroll1.set)
        self.cat_tree.grid(row=0, column=0, sticky='nsew')
        h_scroll1.grid(row=1, column=0, sticky='ew')
        t1_container.grid_columnconfigure(0, weight=1)

        # ---------------------------------------------------------
        # SECTION 2: SUBCATEGORY TABLE
        # ---------------------------------------------------------
        
        
        # SECTION 2: SUBCATEGORY TABLE
        s2 = ttk.LabelFrame(self.db_scroll_frame, text="2. Subcategory Overview", padding=10)
        s2.pack(fill='x', padx=10, pady=10)
        f2 = ttk.Frame(s2)
        f2.pack(fill='x', pady=5)
        ttk.Label(f2, text="Select Category:").pack(side='left')
        
        # Note: Do NOT define self.subcat_filter_cat_var here anymore!
        self.subcat_filter_cat_combo = ttk.Combobox(f2, textvariable=self.subcat_filter_cat_var, 
                                                   values=self.categories, state="readonly")
        self.subcat_filter_cat_combo.pack(side='left', padx=5)
        ttk.Button(f2, text="Update Table", command=self.update_subcategory_table).pack(side='left')
        
        #self.subcat_filter_cat_combo = ttk.Combobox(f2, textvariable=self.subcat_filter_cat_var, values=self.categories)
        # self.subcat_filter_cat_combo.pack(side='left', padx=5)
        # ttk.Button(f2, text="Update Table", command=self.update_subcategory_table).pack(side='left')

        t2_frame = ttk.Frame(s2)
        t2_frame.pack(fill='x', expand=True)
        self.subcat_tree = ttk.Treeview(t2_frame, show='headings', height=13)
        h_scroll2 = ttk.Scrollbar(t2_frame, orient="horizontal", command=self.subcat_tree.xview)
        self.subcat_tree.configure(xscrollcommand=h_scroll2.set)
        self.subcat_tree.grid(row=0, column=0, sticky='nsew')
        h_scroll2.grid(row=1, column=0, sticky='ew')
        t2_frame.grid_columnconfigure(0, weight=1)

        # ---------------------------------------------------------
        # SECTION 3: SUB-SUBCATEGORY TABLE
        # ---------------------------------------------------------
        s3 = ttk.LabelFrame(self.db_scroll_frame, text="3. Sub-Subcategory Overview (Year + Cat + Sub)", padding=10)
        s3.pack(fill='x', padx=10, pady=10)

        f3 = ttk.Frame(s3)
        f3.pack(fill='x', pady=5)

        # 1. Category Filter for Sub-Sub
        ttk.Label(f3, text="Category:").pack(side='left')
        self.db_subsub_cat_combo = ttk.Combobox(f3, textvariable=self.subsub_filter_cat_var, 
                                               values=self.categories, state="readonly", width=20)
        self.db_subsub_cat_combo.pack(side='left', padx=5)
        # BINDING: When Category changes, update the Subcategory list
        self.db_subsub_cat_combo.bind('<<ComboboxSelected>>', self.sync_db_subsub_filters)

        # 2. Subcategory Filter for Sub-Sub
        ttk.Label(f3, text="Subcategory:").pack(side='left', padx=5)
        self.db_subsub_sub_combo = ttk.Combobox(f3, textvariable=self.subsub_filter_sub_var, 
                                               state="readonly", width=20)
        self.db_subsub_sub_combo.pack(side='left', padx=5)

        # 3. Update Button
        ttk.Button(f3, text="Update Sub-Sub Table", command=self.update_subsubcategory_table).pack(side='left', padx=10)

        # 4. Table Container
        t3_frame = ttk.Frame(s3)
        t3_frame.pack(fill='x', expand=True)
        self.subsub_tree = ttk.Treeview(t3_frame, show='headings', height=12)
        h_scroll3 = ttk.Scrollbar(t3_frame, orient="horizontal", command=self.subsub_tree.xview)
        self.subsub_tree.configure(xscrollcommand=h_scroll3.set)
        self.subsub_tree.pack(fill='x')
        h_scroll3.pack(fill='x')
        
    
    def export_csv_comprehensive(self):
        """Exports all financial records (Euro, BD, Income, Investments) into one CSV file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfilename=f"finance_db_backup_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if not filename: return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Standardized Header
                writer.writerow(['Date', 'Type', 'Category', 'Subcategory', 'Sub-Subcategory', 'Amount', 'Currency', 'Details'])
                
                # 1. Euro Expenses
                for t in self.transactions:
                    writer.writerow([t.get('date'), 'Euro Expense', t.get('category'), t.get('subcategory'), 
                                     t.get('subsubcategory'), t.get('amount'), 'EUR', t.get('location')])
                
                # 2. BD Expenses
                for t in self.bd_transactions:
                    writer.writerow([t.get('date'), 'BD Expense', t.get('category'), t.get('subcategory'), 
                                     t.get('subsubcategory'), t.get('amount'), 'BDT', ''])

                # 3. Income
                for i in self.income_sources:
                    writer.writerow([i.get('date'), 'Income', 'Income', i.get('source'), '', i.get('amount'), 'EUR', ''])

                # 4. Investments
                for inv in self.investments:
                    writer.writerow([inv.get('date'), 'Investment', inv.get('category'), '', '', 
                                     inv.get('amount'), 'EUR', inv.get('description')])

                # 5. Returns
                for ret in self.investment_returns:
                    writer.writerow([ret.get('date'), 'Return', ret.get('category'), '', '', 
                                     ret.get('amount'), 'EUR', ret.get('type')])

            messagebox.showinfo("Success", "Full database exported to CSV successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    def import_csv_comprehensive(self):
        """Imports data from a comprehensive CSV and replaces current memory (Confirmation Required)"""
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filename: return

        if not messagebox.askyesno("Confirm Load", "This will merge CSV data with current data. Continue?"):
            return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    etype = row['Type']
                    data = {
                        'date': row['Date'],
                        'amount': float(row['Amount']),
                        'category': row['Category'],
                        'subcategory': row['Subcategory'],
                        'subsubcategory': row['Sub-Subcategory']
                    }

                    if etype == 'Euro Expense':
                        data['location'] = row['Details']
                        data['type'] = 'expense'
                        self.transactions.append(data)
                    elif etype == 'BD Expense':
                        self.bd_transactions.append(data)
                    elif etype == 'Income':
                        self.income_sources.append({'date': data['date'], 'amount': data['amount'], 'source': data['subcategory']})
                    elif etype == 'Investment':
                        self.investments.append({'date': data['date'], 'amount': data['amount'], 'category': data['category'], 'description': row['Details']})
                    elif etype == 'Return':
                        self.investment_returns.append({'date': data['date'], 'amount': data['amount'], 'category': data['category'], 'type': row['Details']})

            self.save_data() # Persist to JSON
            messagebox.showinfo("Success", "Database loaded and merged from CSV. All tables updated.")
            self.update_category_table()
            self.update_input_summary_table()
            if hasattr(self, 'update_investment_display'): self.update_investment_display()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import: {e}. Ensure CSV format is correct.")

    def sync_db_subsub_filters(self, event=None):
        """Updates the Subcategory dropdown based on Category in Section 3"""
        cat = self.subsub_filter_cat_var.get()
        if cat in self.subcategories:
            # Get the keys (Subcategories) from your nested dictionary
            subs = list(self.subcategories[cat].keys())
            self.db_subsub_sub_combo['values'] = subs
            # Clear the subcategory variable so user has to pick a new one
            self.subsub_filter_sub_var.set('')
        
    
            
    def db_sync_subsubs(self, event=None):
        """Updates the Subcategory dropdown in the Database tab specifically"""
        cat = self.subsub_filter_cat_var.get()
        if cat in self.subcategories:
            subs = list(self.subcategories[cat].keys())
            self.subsub_filter_sub_combo['values'] = subs
            self.subsub_filter_sub_var.set('')
            
    def update_subsub_filter_sub_combo(self, event=None):
        cat = self.subsub_filter_cat_var.get()
        if cat in self.subcategories:
            self.subsub_filter_sub_combo['values'] = list(self.subcategories[cat].keys())
            if self.subsub_filter_sub_combo['values']:
                self.subsub_filter_sub_var.current(0)
        
    # --- Database Update Functions ---
   
    def update_category_table(self):
        """Rebuilds Category Table: Ensures ALL categories are shown"""
        year = self.db_year_var.get()
        # Get all currently active categories
        cols_to_show = self.categories 
        
        matrix = defaultdict(lambda: defaultdict(float))
        for t in self.transactions:
            if t.get('date', '').endswith(year):
                try:
                    m_idx = int(t['date'].split('/')[1])
                    cat = t.get('category')
                    if cat in cols_to_show:
                        matrix[m_idx][cat] += float(t.get('amount', 0))
                except: continue
        
        self._render_database_rows(self.cat_tree, cols_to_show, matrix)
    
    

    def _render_database_rows(self, tree, col_items, matrix):
        """Universal Rendering for Euro and BD Tabs. Forces ALL columns to show."""
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        
        # 1. Reset columns completely
        full_cols = ['Month'] + list(col_items) + ['Total']
        tree['columns'] = full_cols
        tree['displaycolumns'] = full_cols # FORCES visibility of every column
        
        for c in full_cols:
            tree.heading(c, text=c)
            # stretch=False + width ensures the horizontal scrollbar triggers correctly
            tree.column(c, width=125, anchor='center', stretch=False)

        # 2. Clear rows
        for item in tree.get_children():
            tree.delete(item)

        # 3. Insert Data
        col_sums = defaultdict(float)
        grand_total = 0

        for m_idx in range(1, 13):
            m_name = month_names[m_idx-1]
            row = [m_name]
            row_sum = 0
            for item in col_items:
                val = matrix[m_idx][item]
                row.append(f"{val:.2f}" if val != 0 else "0.00")
                row_sum += val
                col_sums[item] += val
            row.append(f"{row_sum:.2f}")
            grand_total += row_sum
            tree.insert('', 'end', values=row)

        # 4. Total and Average
        t_row, a_row = ["TOTAL"], ["AVERAGE"]
        for item in col_items:
            t_row.append(f"{col_sums[item]:.2f}")
            a_row.append(f"{(col_sums[item]/12):.2f}")
        t_row.append(f"{grand_total:.2f}")
        a_row.append(f"{(grand_total/12):.2f}")

        tree.insert('', 'end', values=t_row, tags=('summary',))
        tree.insert('', 'end', values=a_row, tags=('summary',))
        tree.tag_configure('summary', background='#f0f0f0', font=('Arial', 10, 'bold'))
        
    def update_subcategory_table(self):
        year = self.db_year_var.get()
        cat = self.subcat_filter_cat_var.get()
        if not cat: return

        subs = list(self.subcategories.get(cat, {}).keys())
        matrix = defaultdict(lambda: defaultdict(float))
        

        
        for t in self.transactions:
            if t.get('date', '').endswith(year) and t.get('category') == cat:
                try:
                    m_idx = int(t['date'].split('/')[1])
                    sub = t.get('subcategory')
                    if sub in subs:
                        matrix[m_idx][sub] += float(t.get('amount', 0))
                except: continue
        
        # Call the helper to render the table
        self._render_database_rows(self.subcat_tree, subs, matrix)

 
        
    
    
    
        
    def _fill_table_rows(self, tree, col_items, matrix):
        """Helper to fill 12 months, Total, and Average for any treeview"""
        grand_total = 0
        col_sums = defaultdict(float)
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]

        for m_idx in range(1, 13):
            m_name = month_names[m_idx-1]
            row = [m_name]
            row_sum = 0
            for item in col_items:
                val = matrix[m_idx][item]
                row.append(f"{val:.2f}")
                row_sum += val
                col_sums[item] += val
            row.append(f"{row_sum:.2f}")
            grand_total += row_sum
            tree.insert('', 'end', values=row)

        # Total Row
        total_row = ["TOTAL"]
        for item in col_items:
            total_row.append(f"{col_sums[item]:.2f}")
        total_row.append(f"{grand_total:.2f}")
        tree.insert('', 'end', values=total_row, tags=('bold_row',))

        # Average Row
        avg_row = ["AVERAGE"]
        for item in col_items:
            avg_row.append(f"{(col_sums[item]/12):.2f}")
        avg_row.append(f"{(grand_total/12):.2f}")
        tree.insert('', 'end', values=avg_row, tags=('bold_row',))

        tree.tag_configure('bold_row', background='#f0f0f0', font=('Arial', 10, 'bold'))

    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", 
                                                filetypes=[("CSV files", "*.csv")])
        if filename:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Type', 'Category', 'Subcategory', 'Subsubcategory', 'Location', 'Amount', 'Date', 'Source'])
                
                for trans in self.transactions:
                    writer.writerow([
                        'Expense',
                        trans.get('category', ''),
                        trans.get('subcategory', ''),
                        trans.get('subsubcategory', ''),
                        trans.get('location', ''),
                        trans['amount'],
                        trans['date'],
                        ''
                    ])
                
                for income in self.income_sources:
                    writer.writerow([
                        'Income',
                        '',
                        '',
                        '',
                        '',
                        '',
                        income['amount'],
                        income['date'],
                        income['source']
                    ])
            
            messagebox.showinfo("Success", "Data exported successfully!")
    
    def import_csv(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                with open(filename, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['Type'] == 'Expense':
                            self.transactions.append({
                                'type': 'expense',
                                'category': row['Category'],
                                'subcategory': row['Subcategory'],
                                'subsubcategory': row.get('Subsubcategory', ''),
                                'location': row['Location'],
                                'amount': float(row['Amount']),
                                'date': row['Date']
                            })
                        elif row['Type'] == 'Income':
                            self.income_sources.append({
                                'source': row['Source'],
                                'amount': float(row['Amount']),
                                'date': row['Date']
                            })
                
                self.save_data()
                messagebox.showinfo("Success", "Data imported successfully!")
                self.update_category_table() 
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {str(e)}")
    
    # --- BD Section ---
    def create_bd_tab(self):
        # Top: Settings & Live Balance
        settings_frame = ttk.LabelFrame(self.bd_tab, text="Conversion Settings & Balance", padding=10)
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(settings_frame, text="Conversion Rate (1 Euro to BD Taka):").pack(side='left', padx=5)
        self.bd_rate_var = tk.DoubleVar(value=self.bd_conversion_rate)
        rate_entry = ttk.Entry(settings_frame, textvariable=self.bd_rate_var, width=10)
        rate_entry.pack(side='left', padx=5)
        
        ttk.Button(settings_frame, text="Update Rate", command=self.update_bd_rate).pack(side='left', padx=5)
        
        self.bd_taka_label = ttk.Label(settings_frame, text="Balance: 0.00 Taka", font=('Arial', 18, 'bold'), foreground='green')
        self.bd_taka_label.pack(side='right', padx=20)
        
        self.bd_euro_label = ttk.Label(settings_frame, text="(0.00 Euro)", font=('Arial', 14))
        self.bd_euro_label.pack(side='right', padx=5)
        
        self.update_bd_display()

        # Middle: Inputs
        input_split_frame = ttk.Frame(self.bd_tab)
        input_split_frame.pack(fill='x', padx=10, pady=5)
        
        # Left: Add Money
        left_form = ttk.LabelFrame(input_split_frame, text="Add Money to BD Balance", padding=10)
        left_form.pack(side='left', fill='both', expand=True, padx=5)
        
        ttk.Label(left_form, text="Convert Euro to Taka").pack(pady=5)
        ttk.Label(left_form, text="Euro Amount:").pack(anchor='w')
        self.bd_euro_amount = ttk.Entry(left_form)
        self.bd_euro_amount.pack(fill='x', pady=2)
        
        ttk.Label(left_form, text="Rate:").pack(anchor='w')
        self.bd_calc_rate = ttk.Entry(left_form)
        self.bd_calc_rate.insert(0, str(self.bd_conversion_rate))
        self.bd_calc_rate.pack(fill='x', pady=2)
        
        ttk.Button(left_form, text="Convert & Add to Balance", command=self.add_bd_from_euro).pack(pady=10)
        
        ttk.Label(left_form, text="Add Taka Directly").pack(pady=5)
        ttk.Label(left_form, text="Taka Amount:").pack(anchor='w')
        self.bd_taka_amount = ttk.Entry(left_form)
        self.bd_taka_amount.pack(fill='x', pady=2)
        ttk.Button(left_form, text="Add to Balance", command=self.add_bd_taka).pack(pady=10)

        # Right: Add Expenditure
        right_form = ttk.LabelFrame(input_split_frame, text="Add Expenditure (BD)", padding=10)
        right_form.pack(side='left', fill='both', expand=True, padx=5)
        
        ttk.Label(right_form, text="Category:").grid(row=0, column=0, sticky='w', pady=2)
        self.bd_exp_cat_var = tk.StringVar()
        self.bd_exp_cat_combo = ttk.Combobox(right_form, textvariable=self.bd_exp_cat_var)
        self.bd_exp_cat_combo.grid(row=0, column=1, sticky='ew', pady=2, padx=5)
        self.bd_exp_cat_combo.bind('<<ComboboxSelected>>', self.bd_update_subcategory_combo)
        
        ttk.Label(right_form, text="Subcategory:").grid(row=1, column=0, sticky='w', pady=2)
        self.bd_exp_subcat_var = tk.StringVar()
        self.bd_exp_subcat_combo = ttk.Combobox(right_form, textvariable=self.bd_exp_subcat_var)
        self.bd_exp_subcat_combo.grid(row=1, column=1, sticky='ew', pady=2, padx=5)
        self.bd_exp_subcat_combo.bind('<<ComboboxSelected>>', self.bd_update_subsubcategory_combo)
        
        ttk.Label(right_form, text="Sub-subcategory:").grid(row=2, column=0, sticky='w', pady=2)
        self.bd_exp_subsubcat_var = tk.StringVar()
        self.bd_exp_subsubcat_combo = ttk.Combobox(right_form, textvariable=self.bd_exp_subsubcat_var)
        self.bd_exp_subsubcat_combo.grid(row=2, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(right_form, text="Amount (Taka):").grid(row=3, column=0, sticky='w', pady=2)
        self.bd_exp_amount = ttk.Entry(right_form)
        self.bd_exp_amount.grid(row=3, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(right_form, text="Date:").grid(row=4, column=0, sticky='w', pady=2)
        self.bd_exp_date = DateEntry(right_form, date_pattern='dd/mm/yyyy')
        self.bd_exp_date.grid(row=4, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Button(right_form, text="Add Expenditure", command=self.add_bd_expenditure).grid(row=5, column=0, columnspan=2, pady=10)

        # Bottom: BD Analysis Notebook (Categories, Subcategories, Sub-subcategories ONLY)
        bd_notebook = ttk.Notebook(self.bd_tab)
        bd_notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Tab 1: Categories View
        bd_cat_tab = ttk.Frame(bd_notebook)
        bd_notebook.add(bd_cat_tab, text="Categories View")
        self.create_bd_categories_view(bd_cat_tab)
        
        # Tab 2: Subcategories View
        bd_subcat_tab = ttk.Frame(bd_notebook)
        bd_notebook.add(bd_subcat_tab, text="Subcategories View")
        self.create_bd_subcategories_view(bd_subcat_tab)
        
        # Tab 3: Sub-subcategories View
        bd_subsubcat_tab = ttk.Frame(bd_notebook)
        bd_notebook.add(bd_subsubcat_tab, text="Sub-subcategories View")
        self.create_bd_subsubcategories_view(bd_subsubcat_tab)
        
        # Tab 4: BD Analysis (NEW)
        bd_ana_tab = ttk.Frame(bd_notebook)
        bd_notebook.add(bd_ana_tab, text="BD Analysis")
        self.create_bd_analysis_tab(bd_ana_tab)
        
        # REMOVED: Matrix Summary Tab
        # REMOVED: Transaction Log

        self.update_bd_category_combos()
    
    def create_bd_analysis_tab(self, parent):
        """UI for the BD Analysis Tab with hierarchical pie charts"""
        # --- Filter Frame ---
        filter_frame = ttk.LabelFrame(parent, text="BD Chart Filters", padding=10)
        filter_frame.pack(fill='x', padx=10, pady=5)

        # 1. Year Filter
        ttk.Label(filter_frame, text="Year:").grid(row=0, column=0, padx=5)
        self.bd_ana_year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Combobox(filter_frame, textvariable=self.bd_ana_year_var, 
                     values=[str(y) for y in range(2020, 2031)], width=8).grid(row=0, column=1, padx=5)

        # 2. Month Filter
        ttk.Label(filter_frame, text="Month:").grid(row=0, column=2, padx=5)
        self.bd_ana_month_var = tk.StringVar(value="Whole Year")
        months = ["Whole Year"] + [datetime(2000, m, 1).strftime('%B') for m in range(1, 13)]
        ttk.Combobox(filter_frame, textvariable=self.bd_ana_month_var, values=months, width=12).grid(row=0, column=3, padx=5)

        # 3. Plot Level
        ttk.Label(filter_frame, text="Level:").grid(row=0, column=4, padx=5)
        self.bd_ana_level_var = tk.StringVar(value="Category")
        ttk.Combobox(filter_frame, textvariable=self.bd_ana_level_var, 
                     values=["Category", "Subcategory", "Sub-subcategory"], width=15).grid(row=0, column=5, padx=5)

        # 4. Hierarchical Selectors
        ttk.Label(filter_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5)
        self.bd_ana_cat_var = tk.StringVar()
        self.bd_ana_cat_combo = ttk.Combobox(filter_frame, textvariable=self.bd_ana_cat_var, 
                                             values=self.categories, width=15)
        self.bd_ana_cat_combo.grid(row=1, column=1, padx=5)
        self.bd_ana_cat_combo.bind('<<ComboboxSelected>>', self.sync_bd_ana_pie_subs)

        ttk.Label(filter_frame, text="Subcategory:").grid(row=1, column=2, padx=5)
        self.bd_ana_sub_var = tk.StringVar()
        self.bd_ana_sub_combo = ttk.Combobox(filter_frame, textvariable=self.bd_ana_sub_var, width=15)
        self.bd_ana_sub_combo.grid(row=1, column=3, padx=5)

        ttk.Button(filter_frame, text="Generate BD Chart", command=self.update_bd_pie_chart).grid(row=1, column=5, padx=10)

        # Chart Container
        self.bd_pie_container = ttk.Frame(parent)
        self.bd_pie_container.pack(fill='both', expand=True, padx=10, pady=10)

    def sync_bd_ana_pie_subs(self, event=None):
        """Updates BD subcategory filter list based on Category"""
        cat = self.bd_ana_cat_var.get()
        if cat in self.subcategories:
            subs = list(self.subcategories[cat].keys())
            self.bd_ana_sub_combo['values'] = subs
            self.bd_ana_sub_var.set('')

    def update_bd_pie_chart(self):
        """Processes BD transactions and plots the pie chart"""
        for widget in self.bd_pie_container.winfo_children():
            widget.destroy()

        year = self.bd_ana_year_var.get()
        month_name = self.bd_ana_month_var.get()
        level = self.bd_ana_level_var.get()
        sel_cat = self.bd_ana_cat_var.get()
        sel_sub = self.bd_ana_sub_var.get()

        target_month = None if month_name == "Whole Year" else datetime.strptime(month_name, '%B').month
        data = defaultdict(float)

        # Logic for aggregating BD Transactions
        for t in self.bd_transactions:
            try:
                t_parts = t['date'].split('/')
                if t_parts[2] != year: continue
                if target_month and int(t_parts[1]) != target_month: continue
                
                if level == "Category":
                    data[t['category']] += t['amount']
                elif level == "Subcategory":
                    if t['category'] == sel_cat:
                        data[t['subcategory']] += t['amount']
                elif level == "Sub-subcategory":
                    if t['category'] == sel_cat and t['subcategory'] == sel_sub:
                        ss = t.get('subsubcategory', 'General')
                        data[ss] += t['amount']
            except: continue

        # Plotting
        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)

        if data:
            labels = list(data.keys())
            values = list(data.values())
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Set3.colors)
            ax.set_title(f"BD {level} Breakdown\n({month_name} {year})", fontweight='bold')
        else:
            ax.text(0.5, 0.5, "No BD Data Found\nCheck Category/Subcategory selection", 
                    ha='center', va='center', fontsize=12)
            ax.set_title("No Data", fontweight='bold')

        canvas = FigureCanvasTkAgg(fig, master=self.bd_pie_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    # Fix for create_bd_subcategories_view method
    def create_bd_subcategories_view(self, parent_frame):
        # 1. Filter Section (Top)
        filter_frame = ttk.LabelFrame(parent_frame, text="Filters", padding=5)
        filter_frame.pack(fill='x', pady=5, padx=10)
        
        ttk.Label(filter_frame, text="Category:").pack(side='left')
        self.bd_subcat_filter_cat = tk.StringVar()
        bd_subcat_combo = ttk.Combobox(filter_frame, textvariable=self.bd_subcat_filter_cat, values=self.categories, width=20, state="readonly")
        bd_subcat_combo.pack(side='left', padx=5)
        
        # Updated command to point directly to logic
        ttk.Button(filter_frame, text="Update", command=self.update_bd_subcategories_table).pack(side='left', padx=10)
        
        # 2. Tree Container (Bottom)
        table_frame = ttk.Frame(parent_frame)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Vertical Scrollbar
        vs = ttk.Scrollbar(table_frame, orient="vertical")
        # Horizontal Scrollbar
        hs = ttk.Scrollbar(table_frame, orient="horizontal")
        
        # Initialize Treeview
        self.bd_subcat_tree_view = ttk.Treeview(table_frame, show='headings', height=18, 
                                                yscrollcommand=vs.set, xscrollcommand=hs.set)
        
        vs.config(command=self.bd_subcat_tree_view.yview)
        hs.config(command=self.bd_subcat_tree_view.xview)
        
        # --- PACKING ORDER (Fixes the "right side" issue) ---
        vs.pack(side='right', fill='y')
        hs.pack(side='bottom', fill='x')
        self.bd_subcat_tree_view.pack(side='left', fill='both', expand=True)

    # Fix for create_bd_subsubcategories_view method (around line 1560)
    def create_bd_subsubcategories_view(self, parent_frame):
        # 1. Filter Section
        filter_frame = ttk.LabelFrame(parent_frame, text="Filters", padding=5)
        filter_frame.pack(fill='x', pady=5, padx=10)
        
        ttk.Label(filter_frame, text="Category:").pack(side='left')
        bd_subsubcat_cat_combo = ttk.Combobox(filter_frame, textvariable=self.bd_subsubcat_filter_cat, 
                                              values=self.categories, width=20, state="readonly")
        bd_subsubcat_cat_combo.pack(side='left', padx=5)
        
        ttk.Label(filter_frame, text="Subcategory:").pack(side='left')
        bd_subsubcat_sub_combo = ttk.Combobox(filter_frame, textvariable=self.bd_subsubcat_filter_sub, 
                                              state="readonly", width=20)
        bd_subsubcat_sub_combo.pack(side='left', padx=5)
        
        # Cascading Binding
        bd_subsubcat_cat_combo.bind('<<ComboboxSelected>>', 
                                    lambda e: self.update_bd_subsub_filter_subs(bd_subsubcat_sub_combo))
        
        ttk.Button(filter_frame, text="Update", command=self.update_bd_subsubcategories_table).pack(side='left', padx=10)
        
        # 2. Tree Container
        table_frame = ttk.Frame(parent_frame)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        vs = ttk.Scrollbar(table_frame, orient="vertical")
        hs = ttk.Scrollbar(table_frame, orient="horizontal")
        
        self.bd_subsubcat_tree_view = ttk.Treeview(table_frame, show='headings', height=18,
                                                   yscrollcommand=vs.set, xscrollcommand=hs.set)
        
        vs.config(command=self.bd_subsubcat_tree_view.yview)
        hs.config(command=self.bd_subsubcat_tree_view.xview)
        
        # --- PACKING ORDER ---
        vs.pack(side='right', fill='y')
        hs.pack(side='bottom', fill='x')
        self.bd_subsubcat_tree_view.pack(side='left', fill='both', expand=True)

    # Add this helper method
    def update_bd_subsub_filter_subs(self, combo_widget):
        """Update subcategory options based on selected category in BD Sub-Sub Tab"""
        cat = self.bd_subsubcat_filter_cat.get() # Matches __init__
        if cat in self.subcategories:
            subs = list(self.subcategories[cat].keys())
            combo_widget['values'] = subs
            if subs: 
                self.bd_subsubcat_filter_sub.set(subs[0])
            else:
                self.bd_subsubcat_filter_sub.set('')
   
    # --- BD Helper Create/Update Functions ---
    def update_bd_rate(self):
        try:
            new_rate = float(self.bd_rate_var.get())
            if new_rate <= 0: raise ValueError
            self.bd_conversion_rate = new_rate
            self.save_data()
            self.update_bd_display()
            messagebox.showinfo("Success", "Rate updated successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive number for rate.")

    def update_bd_display(self):
        self.bd_taka_label.config(text=f"Balance: {self.bd_balance:.2f} Taka")
        euro_eq = self.bd_balance / self.bd_conversion_rate if self.bd_conversion_rate else 0
        self.bd_euro_label.config(text=f"({euro_eq:.2f} Euro)")

    def add_bd_from_euro(self):
        try:
            euro = float(self.bd_euro_amount.get())
            rate = float(self.bd_calc_rate.get())
            if euro <= 0 or rate <= 0: raise ValueError
            taka = euro * rate
            self.bd_balance += taka
            self.bd_conversion_rate = rate
            self.bd_rate_var.set(rate)
            self.save_data()
            self.update_bd_display()
            self.bd_euro_amount.delete(0, 'end')
            messagebox.showinfo("Success", f"Added {taka:.2f} Taka to balance.")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid amounts.")

    def add_bd_taka(self):
        try:
            taka = float(self.bd_taka_amount.get())
            if taka <= 0: raise ValueError
            self.bd_balance += taka
            self.save_data()
            self.update_bd_display()
            self.bd_taka_amount.delete(0, 'end')
        except ValueError:
            messagebox.showerror("Error", "Please enter valid amount.")

    def update_bd_category_combos(self):
        self.bd_exp_cat_combo['values'] = self.categories
        if self.categories:
            self.bd_exp_cat_var.set(self.categories[0])
            self.bd_update_subcategory_combo()
            
    def bd_update_subcategory_combo(self, event=None):
        cat = self.bd_exp_cat_var.get()
        cat_data = self.subcategories.get(cat, {})
        
        if isinstance(cat_data, dict):
            subs = list(cat_data.keys())
        elif isinstance(cat_data, list):
            subs = cat_data
        else:
            subs = []
            
        self.bd_exp_subcat_combo['values'] = subs
        self.bd_exp_subcat_var.set('')
        self.bd_update_subsubcategory_combo()
            
    def bd_update_subsubcategory_combo(self, event=None):
        cat = self.bd_exp_cat_var.get()
        sub = self.bd_exp_subcat_var.get()
        
        sub_data = self.subcategories.get(cat, {}).get(sub, [])
        
        if isinstance(sub_data, list):
            pass
        else:
            sub_data = []
            
        self.bd_exp_subsubcat_combo['values'] = sub_data
        self.bd_exp_subsubcat_var.set('')
        
    def add_bd_expenditure(self):
        try:
            category = self.bd_exp_cat_var.get()
            subcategory = self.bd_exp_subcat_var.get()
            subsubcategory = self.bd_exp_subsubcat_var.get()
            amount = float(self.bd_exp_amount.get())
            date = self.bd_exp_date.get_date().strftime('%d/%m/%Y')
            
            if not category: return
            
            self.bd_transactions.append({
                'category': category,
                'subcategory': subcategory,
                'subsubcategory': subsubcategory,
                'amount': amount,
                'date': date
            })
            
            self.bd_balance -= amount
            
            self.save_data()
            self.refresh_bd_tree()
            # Update all BD views
            self.update_bd_categories_view()
            self.update_bd_subcategories_view()
            self.update_bd_subsubcategories_view()
            self.refresh_bd_summary_matrix()
            
            self.bd_exp_amount.delete(0, 'end')
            messagebox.showinfo("Success", "Expenditure added and balance updated!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid amount.")

    def refresh_bd_tree(self):
        for item in self.bd_tree.get_children():
            self.bd_tree.delete(item)
        for trans in reversed(self.bd_transactions):
            self.bd_tree.insert('', 'end', values=(
                trans['date'],
                trans['category'],
                trans['subcategory'],
                trans.get('subsubcategory', ''), 
                f"{trans['amount']:.2f}"
            ))

    # --- New BD Views Creation ---
    def create_bd_categories_view(self, parent):
        """BD Category View: Filter by Year only."""
        filter_frame = ttk.Frame(parent, padding=10)
        filter_frame.pack(fill='x')
        
        ttk.Label(filter_frame, text="Select Year:").pack(side='left', padx=5)
        self.bd_db_year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Combobox(filter_frame, textvariable=self.bd_db_year_var, values=[str(y) for y in range(2020, 2031)], width=10).pack(side='left')
        
        ttk.Button(filter_frame, text="Refresh Category Table", command=self.update_bd_cat_table).pack(side='left', padx=10)

        self.bd_cat_tree = self._setup_tree_with_scroll(parent)

   
    def _setup_tree_with_scroll(self, parent):
        """Helper to create a Treeview with a horizontal scrollbar attached."""
        container = ttk.Frame(parent)
        container.pack(fill='both', expand=True, padx=10, pady=5)
        
        tree = ttk.Treeview(container, show='headings', height=18)
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(xscrollcommand=h_scroll.set)
        
        tree.pack(side='top', fill='both', expand=True)
        h_scroll.pack(side='bottom', fill='x')
        return tree
    
   

    def update_bd_categories_table(self, parent_frame):
        """Similar to DB Category Table: Rows=Months, Cols=Categories"""
        tree = self.bd_cat_tree_view
        for item in tree.get_children():
            tree.delete(item)
            
        if not self.categories:
            tree.insert('', 'end', values=('No Data',))
            return
            
        year = self.bd_cat_year_var.get()
        month_filter = self.bd_cat_month_var.get()
        
        monthly_data = defaultdict(lambda: defaultdict(float))
        
        for trans in self.bd_transactions:
            # Filter
            if trans['date'].endswith(year):
                m = trans['date'].split('/')[1]
                category = trans['category']
                monthly_data[m][category] += trans['amount']
        
        columns = ['Month'] + self.categories + ['Total']
        tree['columns'] = columns
        tree['show'] = 'headings'
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=110, anchor='center')
            
        # Populate
        cat_totals = defaultdict(float)
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        
        for i, m_name in enumerate(month_names):
            m_num = i + 1
            row_data = [m_name]
            row_total = 0
            for cat in self.categories:
                val = monthly_data[m_num].get(cat, 0)
                row_data.append(f"{val:.0f}")
                row_total += val
                cat_totals[cat] += val
            row_data.append(f"{row_total:.0f}")
            tree.insert('', 'end', values=row_data)
            
        total_row = ['TOTAL']
        grand_total = 0
        for cat in self.categories:
            total_row.append(f"{cat_totals[cat]:.0f}")
            grand_total += cat_totals[cat]
        total_row.append(f"{grand_total:.0f}")
        tree.insert('', 'end', values=total_row, tags=('total',))
        
        # Average
        avg_row = ['AVERAGE']
        for cat in self.categories:
            avg_row.append(f"{cat_totals[cat]/12:.2f}")
        avg_row.append(f"{grand_total/12:.2f}")
        tree.insert('', 'end', values=avg_row, tags=('avg',))
        
        tree.tag_configure('total', background='#d0e0ff', font=('Arial', 9, 'bold'))
        tree.tag_configure('avg', background='#C5E1A5', font=('Arial', 9, 'bold'))

    def update_bd_subcategories_table(self, parent_frame=None):
        """BD Subcategory Matrix: Ensures data ONLY appears in the correct month row"""
        year = self.bd_db_year_var.get() # Get year from the BD Section selector
        cat = self.bd_subcat_filter_cat.get()
        tree = self.bd_subcat_tree_view
        
        if not cat: return

        # Get subcategories for the selected category
        subs = list(self.subcategories.get(cat, {}).keys())
        
        # Initialize matrix: matrix[month_integer][subcategory_name]
        matrix = defaultdict(lambda: defaultdict(float))
        
        for t in self.bd_transactions:
            d_parts = t.get('date', '').split('/')
            if len(d_parts) == 3:
                t_day, t_month, t_year = d_parts
                
                # Check if transaction matches the selected YEAR and CATEGORY
                if t_year == year and t.get('category') == cat:
                    try:
                        m_idx = int(t_month) # Convert "05" to 5
                        sub_name = t.get('subcategory')
                        if sub_name in subs:
                            # Aggregate amount ONLY for this specific month
                            matrix[m_idx][sub_name] += float(t.get('amount', 0))
                    except ValueError: continue
        
        # Call the universal renderer to draw the 12 month rows
        self._render_database_rows(tree, subs, matrix)
        
    def update_bd_subcategories_table2(self, parent_frame):
        """Similar to DB Subcategory Table: Filter by Cat, Rows=Months, Cols=Subs"""
        tree = self.bd_subcat_tree_view
        for item in tree.get_children():
            tree.delete(item)
            
        cat = self.bd_subcat_filter_cat.get()
        if not cat: return
        
        cat_data = self.subcategories.get(cat, {})
        subs = list(cat_data.keys()) if isinstance(cat_data, dict) else []
        
        if not subs:
            tree.insert('', 'end', values=('No Data',))
            return
            
        columns = ['Month'] + subs + ['Total']
        tree['columns'] = columns
        tree['show'] = 'headings'
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=110, anchor='center')
            
        sub_totals = defaultdict(float)
        
        for m in range(1, 13):
            row_data = [datetime(2023, m, 1).strftime('%B')]
            row_total = 0
            for sub in subs:
                amount = 0
                for t in self.bd_transactions:
                    if t['date'].endswith(str(datetime.now().year)): # Using current year
                        if t['category'] == cat and t['subcategory'] == sub:
                            amount += t['amount']
                row_data.append(f"{amount:.0f}")
                row_total += amount
                sub_totals[sub] += amount
            row_data.append(f"{row_total:.0f}")
            tree.insert('', 'end', values=row_data)
            
        total_row = ['TOTAL']
        grand_total = 0
        for sub in subs:
            total_row.append(f"{sub_totals[sub]:.0f}")
            grand_total += sub_totals[sub]
        total_row.append(f"{grand_total:.0f}")
        tree.insert('', 'end', values=total_row, tags=('total',))
        
        # Average
        avg_row = ['AVERAGE']
        for sub in subs:
            avg_row.append(f"{sub_totals[sub]/12:.2f}")
        avg_row.append(f"{grand_total/12:.2f}")
        tree.insert('', 'end', values=avg_row, tags=('avg',))
        tree.tag_configure('total', background='#d0e0ff', font=('Arial', 9, 'bold'))
        tree.tag_configure('avg', background='#C5E1A5', font=('Arial', 9, 'bold'))
    
    def update_bd_subcat_filter_sub(self, event, var_sub):
        cat = var_sub.get()
        if cat in self.subcategories:
            subs = list(self.subcategories.get(cat, {}).keys())
            var_sub['values'] = subs
            if subs: var_sub.current(0)

    
    def update_bd_subsubcategories_table(self, parent_frame=None):
        """BD Sub-Subcategory Matrix: Corrected Month-Specific Filtering"""
        year = self.bd_db_year_var.get()
        cat = self.bd_subsubcat_filter_cat.get()
        sub = self.bd_subsubcat_filter_sub.get()
        tree = self.bd_subsubcat_tree_view
        
        if not cat or not sub: return

        # Get list of items (e.g., Aldi, Lidl)
        ss_list = self.subcategories.get(cat, {}).get(sub, [])
        
        matrix = defaultdict(lambda: defaultdict(float))
        
        for t in self.bd_transactions:
            d_parts = t.get('date', '').split('/')
            if len(d_parts) == 3:
                t_day, t_month, t_year = d_parts
                
                # Match YEAR, CATEGORY, and SUBCATEGORY
                if t_year == year and t.get('category') == cat and t.get('subcategory') == sub:
                    try:
                        m_idx = int(t_month) # Key month identifier
                        ss_name = t.get('subsubcategory')
                        if ss_name in ss_list:
                            # Add amount ONLY to the specific month's bucket
                            matrix[m_idx][ss_name] += float(t.get('amount', 0))
                    except ValueError: continue

        self._render_database_rows(tree, ss_list, matrix)
        
    def update_bd_subsubcategories_table2(self, parent_frame):
        """Similar to DB Sub-subcategory Table: Filter by Cat+Sub, Rows=Months, Cols=SubSubs"""
        tree = self.bd_subsubcat_tree_view
        for item in tree.get_children():
            tree.delete(item)
            
        cat = self.bd_subsubcat_filter_cat.get()
        sub = self.bd_subsubcat_filter_sub.get()
        
        if not cat or not sub: return
        
        subs_dict = self.subcategories.get(cat, {}).get(sub, [])
        subsubs = subs_dict if isinstance(subs_dict, list) else []
        
        if not subsubs:
            tree.insert('', 'end', values=('No Data',))
            return
            
        columns = ['Month'] + subsubs + ['Total']
        tree['columns'] = columns
        tree['show'] = 'headings'
        
        num_cols = len(columns)
        col_w = 100 if num_cols > 5 else 140
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=col_w, anchor='center')
        
        subsub_totals = defaultdict(float)
        
        for m in range(1, 13):
            row_data = [datetime(2023, m, 1).strftime('%B')]
            row_total = 0
            
            for subsub in subsubs:
                amount = 0
                for t in self.bd_transactions:
                    if t['date'].endswith(str(datetime.now().year)):
                        if t['category'] == cat and t['subcategory'] == sub and t.get('subsubcategory', '') == subsub:
                            amount += t['amount']
                row_data.append(f"{amount:.0f}")
                row_total += amount
                subsub_totals[subsub] += amount
            
            row_data.append(f"{row_total:.0f}")
            tree.insert('', 'end', values=row_data)
            
        total_row = ['TOTAL']
        grand_total = 0
        for subsub in subsubs:
            total_row.append(f"{subsub_totals[subsub]:.0f}")
            grand_total += subsub_totals[subsub]
        total_row.append(f"{grand_total:.0f}")
        tree.insert('', 'end', values=total_row, tags=('total',))
        
        # Average
        avg_row = ['AVERAGE']
        for subsub in subsubs:
            avg_row.append(f"{subsub_totals[subsub]/12:.2f}")
        avg_row.append(f"{grand_total/12:.2f}")
        tree.insert('', 'end', values=avg_row, tags=('avg',))
        tree.tag_configure('total', background='#d0e0ff', font=('Arial', 9, 'bold'))
        tree.tag_configure('avg', background='#C5E1A5', font=('Arial', 9, 'bold'))

                
    def sync_bd_db_ss_filters(self, event=None):
        """Updates the Subcategory dropdown specifically for the BD Sub-Sub Tab."""
        cat = self.bd_db_ss_cat_var.get()
        if cat in self.subcategories:
            subs = list(self.subcategories[cat].keys())
            self.bd_db_ss_sub_combo['values'] = subs
            self.bd_db_ss_sub_var.set('')

    def update_bd_cat_table(self):
        year = self.bd_db_year_var.get()
        matrix = defaultdict(lambda: defaultdict(float))
        for t in self.bd_transactions:
            if t.get('date', '').endswith(year):
                try:
                    m_idx = int(t['date'].split('/')[1])
                    matrix[m_idx][t['category']] += float(t['amount'])
                except: continue
        self._render_bd_matrix(self.bd_cat_tree, self.categories, matrix)

    def update_bd_subcat_table(self):
        year = self.bd_db_year_var.get()
        cat = self.bd_db_sub_cat_var.get()
        if not cat: return
        subs = list(self.subcategories.get(cat, {}).keys())
        matrix = defaultdict(lambda: defaultdict(float))
        for t in self.bd_transactions:
            if t.get('date', '').endswith(year) and t.get('category') == cat:
                try:
                    m_idx = int(t['date'].split('/')[1])
                    matrix[m_idx][t['subcategory']] += float(t['amount'])
                except: continue
        self._render_bd_matrix(self.bd_subcat_tree, subs, matrix)

    def update_bd_subsub_table(self):
        year = self.bd_db_year_var.get()
        cat = self.bd_db_ss_cat_var.get()
        sub = self.bd_db_ss_sub_var.get()
        if not cat or not sub: return
        ss_list = self.subcategories.get(cat, {}).get(sub, [])
        matrix = defaultdict(lambda: defaultdict(float))
        for t in self.bd_transactions:
            if t.get('date', '').endswith(year) and t.get('category') == cat and t.get('subcategory') == sub:
                try:
                    m_idx = int(t['date'].split('/')[1])
                    matrix[m_idx][t.get('subsubcategory', '')] += float(t['amount'])
                except: continue
        self._render_bd_matrix(self.bd_subsub_tree, ss_list, matrix)  
           
    def _render_bd_matrix(self, tree, col_items, matrix):
        """Standardized matrix renderer for BD Section tables."""
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        
        # 1. Reset Columns
        full_cols = ['Month'] + list(col_items) + ['Total']
        tree['columns'] = full_cols
        tree['displaycolumns'] = full_cols # Critical for visibility
        
        for c in full_cols:
            tree.heading(c, text=c)
            # stretch=False forces the horizontal scrollbar to become active
            tree.column(c, width=120, anchor='center', stretch=False)

        # 2. Clear Table
        for item in tree.get_children():
            tree.delete(item)

        # 3. Calculate and Insert Month Rows
        grand_total = 0
        col_sums = defaultdict(float)

        for m_idx in range(1, 13):
            row = [month_names[m_idx-1]]
            row_sum = 0
            for item in col_items:
                val = matrix[m_idx][item]
                row.append(f"{val:.0f}") # BD usually uses whole numbers (Taka)
                row_sum += val
                col_sums[item] += val
            row.append(f"{row_sum:.0f}")
            grand_total += row_sum
            tree.insert('', 'end', values=row)

        # 4. Insert Footer Rows (Total & Average)
        t_row = ["TOTAL"]
        a_row = ["AVERAGE"]
        for item in col_items:
            t_row.append(f"{col_sums[item]:.0f}")
            a_row.append(f"{(col_sums[item]/12):.1f}")
        
        t_row.append(f"{grand_total:.0f}")
        a_row.append(f"{(grand_total/12):.1f}")
        
        tree.insert('', 'end', values=t_row, tags=('bold',))
        tree.insert('', 'end', values=a_row, tags=('bold',))
        tree.tag_configure('bold', background='#f0f0f0', font=('Arial', 10, 'bold'))
   

    def refresh_bd_summary_matrix(self):
        """Generates Pivot Table based on 'Group By' selection"""
        tree = self.bd_matrix_tree
        for item in tree.get_children():
            tree.delete(item)
        
        year = datetime.now().year 
        group_by = self.bd_group_var.get()
        
        # 1. Determine Columns based on Group By
        cols = []
        
        if group_by == "Category":
            # Show all "Subcategories" (e.g., "Food", "Cloth")
            for cat, sub_dict in self.subcategories.items():
                for sub_name in sub_dict.keys():
                    cols.append(f"{cat} > {sub_name}")
        elif group_by == "Subcategory":
            # Show all "Sub-subcategories" (e.g., "Aldi", "Lidl")
            for cat, sub_dict in self.subcategories.items():
                for sub_name, sub_list in sub_dict.items():
                    if isinstance(sub_list, list):
                        for subsub in sub_list:
                            cols.append(f"{sub_name} > {subsub}")
        elif group_by == "Subsubcategory":
            # Show all sub-subcategories (Max Detail)
            for cat, sub_dict in self.subcategories.items():
                for sub_name, sub_list in sub_dict.items():
                    if isinstance(sub_list, list):
                        for subsub in sub_list:
                            cols.append(f"{sub_name} > {subsub}")
        else:
            cols = []

        if not cols:
            tree.insert('', 'end', values=('No Data',))
            return

        # 2. Setup Columns: Month + Selected Groups + Total + Average
        columns = ['Month'] + cols + ['Total']
        tree['columns'] = columns
        tree['show'] = 'headings'
        
        # Adjust widths dynamically
        num_cols = len(columns)
        if num_cols > 5:
            col_width = 80
        else:
            col_width = 120
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=col_width, anchor='center')

        # 3. Calculate Data
        month_data = defaultdict(lambda: defaultdict(float))
        
        for trans in self.bd_transactions:
            # Filter by current year (assumed for this view)
            if trans['date'].endswith(str(year)):
                m = trans['date'].split('/')[1]
                col_name = ""
                
                if group_by == "Category":
                    # Construct Col Name
                    col_name = f"{trans['category']} > {trans.get('subcategory', '')}"
                    month_data[m][col_name] += trans['amount']
                    
                elif group_by == "Subcategory":
                    # Construct Col Name
                    col_name = f"{trans.get('subcategory', '')} > {trans.get('subsubcategory', 'General')}"
                    month_data[m][col_name] += trans['amount']
                    
                elif group_by == "Subsubcategory":
                    # Just use subsubcategory as column
                    col_name = trans.get('subsubcategory', 'General')
                    month_data[m][col_name] += trans['amount']

        # 4. Populate Tree
        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        
        col_totals = defaultdict(float)
        
        for i, m_name in enumerate(month_names):
            m_num = i + 1
            row_data = [m_name]
            row_total = 0
            for col in cols:
                if col == 'Total': continue
                val = month_data[m_num].get(col, 0)
                row_data.append(f"{val:.0f}")
                row_total += val
                col_totals[col] += val
            row_data.append(f"{row_total:.0f}")
            tree.insert('', 'end', values=row_data, tags=('row',))
            
        # 5. Total Row
        total_row = ['TOTAL']
        grand_total = 0
        for col in cols:
            if col == 'Total': continue
            total_row.append(f"{col_totals[col]:.0f}")
            grand_total += col_totals[col]
        total_row.append(f"{grand_total:.0f}")
        tree.insert('', 'end', values=total_row, tags=('total',))
        
        # 6. Average Row
        avg_row = ['AVERAGE']
        for col in cols:
            if col == 'Total': continue
            avg_row.append(f"{col_totals[col]/12:.2f}")
        avg_row.append(f"{grand_total/12:.2f}")
        tree.insert('', 'end', values=avg_row, tags=('avg',))
        
        # 7. Zebra Styling
        items = tree.get_children()
        for idx, item in enumerate(items):
            tag = 'row'
            if idx % 2 == 0:
                tag = 'row_odd'
            else:
                tag = 'row_even'
            tree.item(item, tags=(tag,))
            
        tree.tag_configure('row_odd', background='#ffffff')
        tree.tag_configure('row_even', background='#f2f2f2')
        tree.tag_configure('total', background='#d0e0ff', font=('Arial', 9, 'bold'))
        tree.tag_configure('avg', background='#C5E1A5', font=('Arial', 9, 'bold'))

    # --- Investment Section ---
    def create_investment_tab(self):
        input_frame = ttk.LabelFrame(self.investment_tab, text="Investment Management", padding=10)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        invest_frame = ttk.LabelFrame(input_frame, text="Add Investment", padding=10)
        invest_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        ttk.Label(invest_frame, text="Category:").grid(row=0, column=0, sticky='w', pady=2)
        self.invest_category = ttk.Entry(invest_frame, width=25)
        self.invest_category.grid(row=0, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(invest_frame, text="Amount (€):").grid(row=1, column=0, sticky='w', pady=2)
        self.invest_amount = ttk.Entry(invest_frame, width=25)
        self.invest_amount.grid(row=1, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(invest_frame, text="Date:").grid(row=2, column=0, sticky='w', pady=2)
        self.invest_date = DateEntry(invest_frame, date_pattern='dd/mm/yyyy', width=23)
        self.invest_date.grid(row=2, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(invest_frame, text="Description:").grid(row=3, column=0, sticky='w', pady=2)
        self.invest_desc = ttk.Entry(invest_frame, width=25)
        self.invest_desc.grid(row=3, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Button(invest_frame, text="Add Investment", command=self.add_investment).grid(row=4, column=0, columnspan=2, pady=10)
        
        return_frame = ttk.LabelFrame(input_frame, text="Add Return/Profit", padding=10)
        return_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        
        ttk.Label(return_frame, text="Investment Category:").grid(row=0, column=0, sticky='w', pady=2)
        self.return_category_var = tk.StringVar()
        self.return_category_combo = ttk.Combobox(return_frame, textvariable=self.return_category_var,
                                                  width=23, state="readonly")
        self.return_category_combo.grid(row=0, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(return_frame, text="Return Amount (€):").grid(row=1, column=0, sticky='w', pady=2)
        self.return_amount = ttk.Entry(return_frame, width=25)
        self.return_amount.grid(row=1, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(return_frame, text="Date:").grid(row=2, column=0, sticky='w', pady=2)
        self.return_date = DateEntry(return_frame, date_pattern='dd/mm/yyyy', width=23)
        self.return_date.grid(row=2, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Label(return_frame, text="Type:").grid(row=3, column=0, sticky='w', pady=2)
        self.return_type_var = tk.StringVar(value="Profit")
        return_type_combo = ttk.Combobox(return_frame, textvariable=self.return_type_var,
                                        values=["Profit", "Return"], width=23, state="readonly")
        return_type_combo.grid(row=3, column=1, sticky='ew', pady=2, padx=5)
        
        ttk.Button(return_frame, text="Add Return/Profit", command=self.add_return).grid(row=4, column=0, columnspan=2, pady=10)
        
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)
        
        summary_frame = ttk.LabelFrame(self.investment_tab, text="Investment Summary", padding=10)
        summary_frame.pack(fill='x', padx=10, pady=5)
        
        self.total_invested_label = ttk.Label(summary_frame, text="Total Invested: €0.00", 
                                             font=('Arial', 11, 'bold'), foreground='blue')
        self.total_invested_label.pack(side='left', padx=20)
        
        self.total_returns_label = ttk.Label(summary_frame, text="Total Returns: €0.00", 
                                            font=('Arial', 11, 'bold'), foreground='green')
        self.total_returns_label.pack(side='left', padx=20)
        
        self.net_profit_label = ttk.Label(summary_frame, text="Net Profit: €0.00", 
                                         font=('Arial', 11, 'bold'), foreground='darkgreen')
        self.net_profit_label.pack(side='left', padx=20)
        
        display_frame = ttk.LabelFrame(self.investment_tab, text="Investment Details", padding=5)
        display_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        invest_notebook = ttk.Notebook(display_frame)
        invest_notebook.pack(fill='both', expand=True)
        
        investments_tab = ttk.Frame(invest_notebook)
        invest_notebook.add(investments_tab, text="Investments")
        
        invest_table_frame = ttk.Frame(investments_tab)
        invest_table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        invest_scroll = ttk.Scrollbar(invest_table_frame, orient='vertical')
        self.invest_tree = ttk.Treeview(invest_table_frame, yscrollcommand=invest_scroll.set,
                                       columns=('Date', 'Category', 'Amount', 'Description'), show='headings')
        invest_scroll.config(command=self.invest_tree.yview)
        
        self.invest_tree.heading('Date', text='Date')
        self.invest_tree.heading('Category', text='Category')
        self.invest_tree.heading('Amount', text='Amount')
        self.invest_tree.heading('Description', text='Description')
        
        self.invest_tree.column('Date', width=100, anchor='center')
        self.invest_tree.column('Category', width=150, anchor='center')
        self.invest_tree.column('Amount', width=100, anchor='center')
        self.invest_tree.column('Description', width=200, anchor='center')
        
        invest_scroll.pack(side='right', fill='y')
        self.invest_tree.pack(side='left', fill='both', expand=True)
        
        returns_tab = ttk.Frame(invest_notebook)
        invest_notebook.add(returns_tab, text="Returns/Profits")
        
        return_table_frame = ttk.Frame(returns_tab)
        return_table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        return_scroll = ttk.Scrollbar(return_table_frame, orient='vertical')
        self.return_tree = ttk.Treeview(return_table_frame, yscrollcommand=return_scroll.set,
                                       columns=('Date', 'Category', 'Amount', 'Type'), show='headings')
        return_scroll.config(command=self.return_tree.yview)
        
        self.return_tree.heading('Date', text='Date')
        self.return_tree.heading('Category', text='Category')
        self.return_tree.heading('Amount', text='Amount')
        self.return_tree.heading('Type', text='Type')
        
        self.return_tree.column('Date', width=100, anchor='center')
        self.return_tree.column('Category', width=150, anchor='center')
        self.return_tree.column('Amount', width=100, anchor='center')
        self.return_tree.column('Type', width=150, anchor='center')
        
        return_scroll.pack(side='right', fill='y')
        self.return_tree.pack(side='left', fill='both', expand=True)
        
        self.update_investment_display()
    
    def update_investment_display(self):
        for item in self.invest_tree.get_children():
            self.invest_tree.delete(item)
        for item in self.return_tree.get_children():
            self.return_tree.delete(item)
        
        total_invested = 0
        for inv in self.investments:
            self.invest_tree.insert('', 'end', values=(
                inv['date'],
                inv['category'],
                f"€{inv['amount']:.2f}",
                inv['description']
            ))
            total_invested += inv['amount']
        
        total_returns = 0
        for ret in self.investment_returns:
            self.return_tree.insert('', 'end', values=(
                ret['date'],
                ret['category'],
                f"€{ret['amount']:.2f}",
                ret['type']
            ))
            total_returns += ret['amount']
        
        net_profit = total_returns - total_invested
        self.total_invested_label.config(text=f"Total Invested: €{total_invested:.2f}")
        self.total_returns_label.config(text=f"Total Returns: €{total_returns:.2f}")
        
        if net_profit >= 0:
            self.net_profit_label.config(text=f"Net Profit: €{net_profit:.2f}", foreground='darkgreen')
        else:
            self.net_profit_label.config(text=f"Net Loss: €{abs(net_profit):.2f}", foreground='red')
    
    def add_investment(self):
        try:
            category = self.invest_category.get().strip()
            amount = float(self.invest_amount.get())
            date = self.invest_date.get_date().strftime('%d/%m/%Y')
            description = self.invest_desc.get().strip()
            
            if not category:
                messagebox.showwarning("Warning", "Please enter a category!")
                return
            
            self.investments.append({
                'category': category,
                'amount': amount,
                'date': date,
                'description': description
            })
            
            if category not in self.investment_categories:
                self.investment_categories.append(category)
                self.update_investment_category_combo()
            
            self.invest_category.delete(0, 'end')
            self.invest_amount.delete(0, 'end')
            self.invest_desc.delete(0, 'end')
            
            self.save_data()
            self.update_investment_display()
            messagebox.showinfo("Success", "Investment added successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount!")
            
    def add_return(self):
        try:
            category = self.return_category_var.get()
            amount = float(self.return_amount.get())
            date = self.return_date.get_date().strftime('%d/%m/%Y')
            return_type = self.return_type_var.get()
            
            if not category:
                messagebox.showwarning("Warning", "Please select an investment category!")
                return
            
            self.investment_returns.append({
                'category': category,
                'amount': amount,
                'date': date,
                'type': return_type
            })
            
            self.return_amount.delete(0, 'end')
            
            self.save_data()
            self.update_investment_display()
            messagebox.showinfo("Success", "Return/Profit added successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount!")
    
    def update_investment_category_combo(self):
        self.return_category_combo['values'] = sorted(self.investment_categories)
        if self.investment_categories and not self.return_category_var.get():
            self.return_category_var.set(self.investment_categories[0])
            
    # --- Analysis Section (RESTORED) ---
    
    def create_detailed_analysis_tab(self):
        # Filter Frame
        filter_frame = ttk.LabelFrame(self.detailed_analysis_tab, text="Hierarchy Analysis Filters", padding=10)
        filter_frame.pack(fill='x', padx=10, pady=5)

        # 1. Year
        ttk.Label(filter_frame, text="Year:").grid(row=0, column=0, padx=5)
        self.det_year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Combobox(filter_frame, textvariable=self.det_year_var, values=[str(y) for y in range(2020, 2031)], width=8).grid(row=0, column=1, padx=5)

        # 2. Month (with "Whole Year" option)
        ttk.Label(filter_frame, text="Month:").grid(row=0, column=2, padx=5)
        self.det_month_var = tk.StringVar(value="Whole Year")
        month_options = ["Whole Year"] + [datetime(2000, m, 1).strftime('%B') for m in range(1, 13)]
        ttk.Combobox(filter_frame, textvariable=self.det_month_var, values=month_options, width=12).grid(row=0, column=3, padx=5)

        # 3. Category
        ttk.Label(filter_frame, text="Category:").grid(row=0, column=4, padx=5)
        self.det_cat_var = tk.StringVar()
        self.det_cat_combo = ttk.Combobox(filter_frame, textvariable=self.det_cat_var, values=self.categories, width=15)
        self.det_cat_combo.grid(row=0, column=5, padx=5)
        self.det_cat_combo.bind('<<ComboboxSelected>>', self.sync_detailed_analysis_subs)

        # 4. Subcategory
        ttk.Label(filter_frame, text="Subcategory:").grid(row=0, column=6, padx=5)
        self.det_sub_var = tk.StringVar()
        self.det_sub_combo = ttk.Combobox(filter_frame, textvariable=self.det_sub_var, width=15)
        self.det_sub_combo.grid(row=0, column=7, padx=5)

        # Update Button
        ttk.Button(filter_frame, text="Generate Pie Chart", command=self.update_detailed_charts).grid(row=0, column=8, padx=15)

        # Chart Frame
        self.det_chart_frame = ttk.Frame(self.detailed_analysis_tab)
        self.det_chart_frame.pack(fill='both', expand=True, padx=10, pady=10)

    def sync_detailed_analysis_subs(self, event=None):
        """Updates the subcategory dropdown based on selected category in Detailed Analysis"""
        cat = self.det_cat_var.get()
        if cat in self.subcategories:
            subs = list(self.subcategories[cat].keys())
            self.det_sub_combo['values'] = ["All Subcategories"] + subs
            self.det_sub_var.set("All Subcategories")
        else:
            self.det_sub_combo['values'] = []
            self.det_sub_var.set("")


        
   
   
    
    def create_analysis_tab(self):
        # We use a Canvas with a Scrollbar to ensure all sections fit
        ana_canvas = tk.Canvas(self.analysis_tab)
        v_scroll = ttk.Scrollbar(self.analysis_tab, orient="vertical", command=ana_canvas.yview)
        self.ana_scroll_frame = ttk.Frame(ana_canvas)

        self.ana_scroll_frame.bind("<Configure>", lambda e: ana_canvas.configure(scrollregion=ana_canvas.bbox("all")))
        ana_canvas.create_window((0, 0), window=self.ana_scroll_frame, anchor="nw")
        ana_canvas.configure(yscrollcommand=v_scroll.set)

        v_scroll.pack(side="right", fill="y")
        ana_canvas.pack(side="left", fill="both", expand=True)

        # ---------------------------------------------------------
        # SECTION 1: YEARLY OVERVIEW (BAR PLOT)
        # ---------------------------------------------------------
        sec1 = ttk.LabelFrame(self.ana_scroll_frame, text="Section 1: Yearly Income vs Expense Overview", padding=10)
        sec1.pack(fill='x', padx=10, pady=10)

        s1_filter = ttk.Frame(sec1)
        s1_filter.pack(fill='x', pady=5)
        
        ttk.Label(s1_filter, text="Select Year:").pack(side='left', padx=5)
        self.ana_bar_year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Combobox(s1_filter, textvariable=self.ana_bar_year_var, values=[str(y) for y in range(2020, 2031)], width=10).pack(side='left', padx=5)
        ttk.Button(s1_filter, text="Refresh Bar Chart", command=self.update_bar_chart).pack(side='left', padx=10)

        self.bar_chart_container = ttk.Frame(sec1)
        self.bar_chart_container.pack(fill='x', pady=5)

        # ---------------------------------------------------------
        # SECTION 2: DETAILED PIE CHART ANALYSIS
        # ---------------------------------------------------------
        sec2 = ttk.LabelFrame(self.ana_scroll_frame, text="Section 2: Detailed Pie Chart Analysis", padding=10)
        sec2.pack(fill='x', padx=10, pady=10)

        s2_filter = ttk.Frame(sec2)
        s2_filter.pack(fill='x', pady=5)

        # Time Filters
        ttk.Label(s2_filter, text="Year:").grid(row=0, column=0, padx=5, sticky='w')
        self.ana_pie_year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Combobox(s2_filter, textvariable=self.ana_pie_year_var, values=[str(y) for y in range(2020, 2031)], width=8).grid(row=0, column=1, padx=5)

        ttk.Label(s2_filter, text="Month:").grid(row=0, column=2, padx=5, sticky='w')
        self.ana_pie_month_var = tk.StringVar(value="Whole Year")
        months = ["Whole Year"] + [datetime(2000, m, 1).strftime('%B') for m in range(1, 13)]
        ttk.Combobox(s2_filter, textvariable=self.ana_pie_month_var, values=months, width=12).grid(row=0, column=3, padx=5)

        # Hierarchy Type
        ttk.Label(s2_filter, text="Plot Level:").grid(row=0, column=4, padx=5, sticky='w')
        self.ana_pie_level_var = tk.StringVar(value="Category")
        ttk.Combobox(s2_filter, textvariable=self.ana_pie_level_var, values=["Category", "Subcategory", "Sub-subcategory"], width=15).grid(row=0, column=5, padx=5)

        # Category/Subcat Selectors
        ttk.Label(s2_filter, text="If Sub/Sub-Sub, Select Cat:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.ana_pie_cat_var = tk.StringVar()
        self.ana_pie_cat_combo = ttk.Combobox(s2_filter, textvariable=self.ana_pie_cat_var, values=self.categories, width=15)
        self.ana_pie_cat_combo.grid(row=1, column=1, padx=5)
        self.ana_pie_cat_combo.bind('<<ComboboxSelected>>', self.sync_ana_pie_subs)

        ttk.Label(s2_filter, text="If Sub-Sub, Select Subcat:").grid(row=1, column=2, padx=5, sticky='w')
        self.ana_pie_sub_var = tk.StringVar()
        self.ana_pie_sub_combo = ttk.Combobox(s2_filter, textvariable=self.ana_pie_sub_var, width=15)
        self.ana_pie_sub_combo.grid(row=1, column=3, padx=5)

        ttk.Button(s2_filter, text="Update Pie Chart", command=self.update_pie_chart).grid(row=1, column=5, padx=10)

        self.pie_chart_container = ttk.Frame(sec2)
        self.pie_chart_container.pack(fill='x', pady=5)

        # Initial plot
        self.update_bar_chart()

    def sync_ana_pie_subs(self, event=None):
        cat = self.ana_pie_cat_var.get()
        if cat in self.subcategories:
            subs = list(self.subcategories[cat].keys())
            self.ana_pie_sub_combo['values'] = subs
            self.ana_pie_sub_var.set('')

    def update_bar_chart(self):
        """Logic for Section 1: Bar Plot"""
        for widget in self.bar_chart_container.winfo_children():
            widget.destroy()
        
        year = self.ana_bar_year_var.get()
        monthly_income = defaultdict(float)
        monthly_expense = defaultdict(float)

        for inc in self.income_sources:
            if inc['date'].endswith(year):
                m = int(inc['date'].split('/')[1])
                monthly_income[m] += inc['amount']
        
        for t in self.transactions:
            if t['date'].endswith(year):
                m = int(t['date'].split('/')[1])
                monthly_expense[m] += t['amount']

        fig = Figure(figsize=(12, 4), dpi=100)
        ax = fig.add_subplot(111)
        x = range(1, 13)
        width = 0.35
        
        ax.bar([i - width/2 for i in x], [monthly_income[i] for i in x], width, label='Income', color='#4CAF50')
        ax.bar([i + width/2 for i in x], [monthly_expense[i] for i in x], width, label='Expense', color='#F44336')
        
        ax.set_title(f"Yearly Overview: Income vs Expense ({year})", fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([datetime(2000, m, 1).strftime('%b') for m in x])
        ax.legend()
        
        canvas = FigureCanvasTkAgg(fig, master=self.bar_chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='x')

    def update_pie_chart(self):
        """Logic for Section 2: Dynamic Pie Chart"""
        for widget in self.pie_chart_container.winfo_children():
            widget.destroy()

        year = self.ana_pie_year_var.get()
        month_name = self.ana_pie_month_var.get()
        level = self.ana_pie_level_var.get()
        sel_cat = self.ana_pie_cat_var.get()
        sel_sub = self.ana_pie_sub_var.get()

        target_month = None if month_name == "Whole Year" else datetime.strptime(month_name, '%B').month
        
        data = defaultdict(float)
        
        # Determine filtering and grouping based on level
        for t in self.transactions:
            try:
                t_parts = t['date'].split('/')
                if t_parts[2] != year: continue
                if target_month and int(t_parts[1]) != target_month: continue
                
                if level == "Category":
                    data[t['category']] += t['amount']
                elif level == "Subcategory":
                    if t['category'] == sel_cat:
                        data[t['subcategory']] += t['amount']
                elif level == "Sub-subcategory":
                    if t['category'] == sel_cat and t['subcategory'] == sel_sub:
                        ss = t.get('subsubcategory', 'General')
                        data[ss] += t['amount']
            except: continue

        fig = Figure(figsize=(8, 5), dpi=100)
        ax = fig.add_subplot(111)

        if data:
            ax.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', startangle=140)
            ax.set_title(f"{level} Breakdown ({month_name} {year})", fontweight='bold')
        else:
            ax.text(0.5, 0.5, "No Data Found for Selection", ha='center', va='center')

        canvas = FigureCanvasTkAgg(fig, master=self.pie_chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='x')
        
    def sync_analysis_subs(self, event=None):
        """Updates the Subcategory filter based on selected Category"""
        cat = self.analysis_cat_var.get()
        if cat in self.subcategories:
            subs = list(self.subcategories[cat].keys())
            self.analysis_sub_combo['values'] = subs
            if subs: self.analysis_sub_var.set(subs[0])
        else:
            self.analysis_sub_combo['values'] = []
            self.analysis_sub_var.set("")

    def on_chart_resize(self, event):
        self.update_analysis_charts()
        
    def update_analysis_charts(self):
        for widget in self.charts_frame.winfo_children():
            widget.destroy()
        
        year = self.analysis_year_var.get()
        month_val = self.analysis_month_var.get()
        target_cat = self.analysis_cat_var.get()
        target_sub = self.analysis_sub_var.get()
        
        w = self.charts_frame.winfo_width()
        h = self.charts_frame.winfo_height()
        if w < 100: w = 1500 
        if h < 100: h = 1200 # Increased height for more charts
        fig_w, fig_h = w / 50, h / 50
        
        fig = Figure(figsize=(fig_w, fig_h), dpi=100)
        
        # --- 1. Income vs Expense Bar Chart ---
        ax1 = fig.add_subplot(4, 2, (1, 2))
        monthly_income = defaultdict(float)
        monthly_expense = defaultdict(float)
        for inc in self.income_sources:
            if inc['date'].endswith(year):
                m = int(inc['date'].split('/')[1])
                monthly_income[m] += inc['amount']
        for trans in self.transactions:
            if trans['date'].endswith(year):
                m = int(trans['date'].split('/')[1])
                monthly_expense[m] += trans['amount']
        
        x = range(1, 13)
        width = 0.35
        ax1.bar([i - width/2 for i in x], [monthly_income[i] for i in x], width, label='Income', color='green', alpha=0.7)
        ax1.bar([i + width/2 for i in x], [monthly_expense[i] for i in x], width, label='Expense', color='red', alpha=0.7)
        ax1.set_title(f'Income vs Expense - {year}', fontweight='bold')
        ax1.set_xticks(x)
        ax1.legend()

        # --- 2. Monthly Category Pie ---
        ax2 = fig.add_subplot(4, 2, 3)
        m_pie_data = defaultdict(float)
        m_filter = month_val.zfill(2) if month_val != "Whole Year" else None
        
        for t in self.transactions:
            t_parts = t['date'].split('/')
            if t_parts[2] == year:
                if m_filter is None or t_parts[1] == m_filter:
                    m_pie_data[t['category']] += t['amount']
        
        self._safe_pie(ax2, m_pie_data, f"Category Mix ({month_val}/{year})")

        # --- 3. Yearly Category Pie ---
        ax3 = fig.add_subplot(4, 2, 4)
        y_pie_data = defaultdict(float)
        for t in self.transactions:
            if t['date'].endswith(year):
                y_pie_data[t['category']] += t['amount']
        self._safe_pie(ax3, y_pie_data, f"Yearly Category Mix ({year})")

        # --- 4. BD Expenses Pie ---
        ax4 = fig.add_subplot(4, 2, 5)
        bd_data = defaultdict(float)
        for t in self.bd_transactions:
            t_parts = t['date'].split('/')
            if t_parts[2] == year:
                if m_filter is None or t_parts[1] == m_filter:
                    bd_data[t['category']] += t['amount']
        self._safe_pie(ax4, bd_data, f"BD Expenses ({month_val}/{year})")

        # --- 5. NEW: Subcategory Pie (Filtered by Category) ---
        ax5 = fig.add_subplot(4, 2, 6)
        sub_pie_data = defaultdict(float)
        if target_cat:
            for t in self.transactions:
                t_parts = t['date'].split('/')
                if t_parts[2] == year and t['category'] == target_cat:
                    if m_filter is None or t_parts[1] == m_filter:
                        sub_pie_data[t['subcategory']] += t['amount']
            self._safe_pie(ax5, sub_pie_data, f"Subcats of {target_cat}\n({month_val})")
        else:
            ax5.text(0.5, 0.5, "Select Category", ha='center')

        # --- 6. NEW: Sub-Subcategory Pie (Filtered by Subcategory) ---
        ax6 = fig.add_subplot(4, 2, 7)
        ss_pie_data = defaultdict(float)
        if target_cat and target_sub:
            for t in self.transactions:
                t_parts = t['date'].split('/')
                if t_parts[2] == year and t['category'] == target_cat and t['subcategory'] == target_sub:
                    if m_filter is None or t_parts[1] == m_filter:
                        ss_item = t.get('subsubcategory', 'Other')
                        ss_pie_data[ss_item] += t['amount']
            self._safe_pie(ax6, ss_pie_data, f"Items in {target_sub}\n({month_val})")
        else:
            ax6.text(0.5, 0.5, "Select Subcategory", ha='center')

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def _safe_pie(self, ax, data, title):
        """Helper to plot pie chart or 'No Data' message"""
        if data:
            labels = list(data.keys())
            sizes = list(data.values())
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
            ax.set_title(title, fontweight='bold', fontsize=10)
        else:
            ax.text(0.5, 0.5, f"No Data for\n{title}", ha='center', va='center')
            ax.set_title(title, fontweight='bold', fontsize=10)
            
   

def main():
    root = tk.Tk()
    app = FinanceManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
