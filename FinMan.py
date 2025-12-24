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
        
        # Categories with Nested Sub-Subcategories
        self.categories = [
            "Household cost", "Car", "Health/Medicine", "Sadaka", "Fixed/contract",
            "Extra", "Entertainment", "Family Education", "Savings cost"
        ]
        
        # Target Structure: Category -> { Subcategory: [Sub-subcategories] }
        self.subcategories = {
            "Household cost": {
                "Food": ["Aldi", "Lidl", "Local Market"],
                "Cloth": ["Zara", "H&M", "Local"],
                "House materials": ["IKEA", "Leroy Merlin"],
                "Office Cost": ["Paper", "Ink", "Electricity"],
                "Haircut": ["Salon", "Barber"]
            },
            "Car": {
                "Fuel": ["Shell", "Aral"],
                "Service": ["Oil Change", "Wash"]
            },
            "Health/Medicine": {
                "Consultation": ["Dr. A", "Dr. B"],
                "Health Ins": ["AXA", "Allianz"],
                "Envivas Ins": ["BUPA", "Cigna"],
                "Dental": ["Dentist 1", "Dentist 2"],
                "Medicine": ["Pharmacy 1", "Pharmacy 2"],
                "Blood Test": ["Lab 1", "Lab 2"],
                "Supp/ Med": ["Vitamin", "Supplements"],
                "Others": ["General"]
            },
            "Sadaka": {
                "DIB": ["Org A", "Org B"],
                "BD Madrasa": ["Madrasa 1", "Madrasa 2"],
                "Sadaka group": ["Group A", "Group B"],
                "Parents": ["Father", "Mother"],
                "BD Project": ["Project A", "Project B"],
                "Fitr": ["Zakat Fitr 1", "Zakat Fitr 2"],
                "Food Program": ["Program A", "Program B"],
                "CCR25": ["CCR25 Part 1", "CCR25 Part 2"],
                "DIB/ Madrasa": ["Madrasa A", "Madrasa B"],
                "Quran Project": ["Project X", "Project Y"]
            },
            "Fixed/contract": {
                "House Rent": ["Jan", "Feb", "Mar"],
                "Electricity": ["Bill 1", "Bill 2"],
                "Internet": ["Provider 1", "Provider 2"],
                "ARD/ ZDF": ["ARD", "ZDF"],
                "Public Transport": ["Bus", "Train"],
                "Mobile Contract": ["Vodafone", "Telekom"],
                "Sports": ["Gym", "Club"],
                "BAnk": ["Bank 1", "Bank 2"]
            },
            "Family Education": {
                "Quran Lesson": ["Teacher 1", "Teacher 2"],
                "School": ["Tuition", "Books"]
            },
            "Savings cost": {
                "Qurbani": ["Cow 1", "Cow 2"],
                "Zakat": ["Zakat A", "Zakat B"],
                "Tax Payment": ["Tax 1", "Tax 2"],
                "Tax Mishu": ["Penalty 1", "Penalty 2"],
                "Hajj": ["Package A", "Package B"],
                "Investment": ["Stocks", "Crypto"],
                "BD tour": ["Trip 1", "Trip 2"]
            },
            "Entertainment": {
                "Car Rent": ["Days A", "Days B"],
                "Car Oil": ["Station 1", "Station 2"],
                "Room Rent": ["Studio", "1 Bedroom"],
                "Food": ["Dinner", "Party"],
                "Amusements": ["Cinema", "Park"],
                "Fish/ pond": ["Fishing 1", "Fishing 2"],
                "Tickets": ["Event A", "Event B"],
                "Equipments": ["Gear 1", "Gear 2"],
                "Foreign Tax": ["Visa Fee", "Duty"]
            },
            "Extra": {
                "Gifts/Invitation": ["Wedding", "Birthday"],
                "Holiday": ["Summer", "Winter"],
                "Invest": ["Stocks", "Bonds"],
                "Tax Apply": ["Filing", "Accountant"],
                "Visa/Residence/Pass": ["Application", "Renewal"],
                "Umrah": ["Package 1", "Package 2"],
                "Language": ["Course 1", "Course 2"],
                "Passport": ["New", "Renewal"]
            }
        }
        
        self.transactions = [] 
        self.income_sources = []
        self.investments = []
        self.investment_returns = []
        self.investment_categories = []
        
        # BD Section Data
        self.bd_balance = 0.0
        self.bd_conversion_rate = 100.0
        self.bd_transactions = [] 

        # BD Filter Variables (Must be instance variables to fix NameError)
        self.bd_cat_year_var = None
        self.bd_cat_month_var = None
        self.bd_subcat_filter_cat = None
        self.bd_subcat_filter_sub = None
        self.bd_subsubcat_filter_cat = None
        self.bd_subsubcat_filter_sub = None

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
                    self.bd_conversion_rate = data.get('bd_conversion_rate', 100.0)
                    self.bd_transactions = data.get('bd_transactions', [])
                    
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
            'categories': self.categories,
            'subcategories': self.subcategories,
            'transactions': self.transactions,
            'income_sources': self.income_sources,
            'investments': self.investments,
            'investment_returns': self.investment_returns,
            'investment_categories': self.investment_categories,
            'bd_balance': self.bd_balance,
            'bd_conversion_rate': self.bd_conversion_rate,
            'bd_transactions': self.bd_transactions 
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.update_input_summary_table()
        self.update_bd_display()
    
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
        
        columns = ('month', 'income', 'expense', 'investment', 'bd_expense', 'balance')
        self.summary_tree = ttk.Treeview(summary_frame, columns=columns, show='headings', height=8)
        
        self.summary_tree.heading('month', text='Month')
        self.summary_tree.heading('income', text='Income (€)')
        self.summary_tree.heading('expense', text='Expense (€)')
        self.summary_tree.heading('investment', text='Investment (€)')
        self.summary_tree.heading('bd_expense', text='BD Exp (Tk)')
        self.summary_tree.heading('balance', text='Balance (€)')
        
        self.summary_tree.column('month', width=100, anchor='center')
        self.summary_tree.column('income', width=100, anchor='center')
        self.summary_tree.column('expense', width=100, anchor='center')
        self.summary_tree.column('investment', width=100, anchor='center')
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
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        
        euro_eq = self.bd_balance / self.bd_conversion_rate if self.bd_conversion_rate else 0
        self.current_bd_balance_label.config(
            text=f"BD Current Balance: {self.bd_balance:.2f} Taka (≈{euro_eq:.2f} €)"
        )

        months_data = defaultdict(lambda: {
            'income': 0.0,
            'expense': 0.0, 
            'investment': 0.0,
            'bd_expense': 0.0
        })
        
        current_year = datetime.now().year
        
        def get_month_key(date_str):
            try:
                parts = date_str.split('/')
                d = datetime.strptime(date_str, '%d/%m/%Y')
                return d.month
            except:
                return None

        for inc in self.income_sources:
            m = get_month_key(inc['date'])
            if m:
                months_data[m]['income'] += inc['amount']
        
        for exp in self.transactions:
            if exp.get('category') == "Savings cost":
                continue
            m = get_month_key(exp['date'])
            if m:
                months_data[m]['expense'] += exp['amount']
                
        for inv in self.investments:
            m = get_month_key(inv['date'])
            if m:
                months_data[m]['investment'] += inv['amount']
                
        for bd_exp in self.bd_transactions:
            m = get_month_key(bd_exp['date'])
            if m:
                months_data[m]['bd_expense'] += bd_exp['amount']

        month_names = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        
        grand_totals = {'income': 0, 'expense': 0, 'investment': 0, 'bd_expense': 0, 'balance': 0}
        active_months_count = 0
        
        for i, m_name in enumerate(month_names):
            m_num = i + 1
            data = months_data[m_num]
            
            income = data['income']
            expense = data['expense']
            invest = data['investment']
            bd_exp = data['bd_expense']
            
            balance = income - expense - invest
            
            if income > 0 or expense > 0 or invest > 0 or bd_exp > 0:
                active_months_count += 1
            
            tag = 'even' if i % 2 == 0 else 'odd'
            
            self.summary_tree.insert('', 'end', values=(
                m_name,
                f"{income:.2f}",
                f"{expense:.2f}",
                f"{invest:.2f}",
                f"{bd_exp:.2f}",
                f"{balance:.2f}"
            ), tags=(tag,))
            
            grand_totals['income'] += income
            grand_totals['expense'] += expense
            grand_totals['investment'] += invest
            grand_totals['bd_expense'] += bd_exp
            grand_totals['balance'] += balance
        
        self.summary_tree.insert('', 'end', values=(
            "TOTAL",
            f"{grand_totals['income']:.2f}",
            f"{grand_totals['expense']:.2f}",
            f"{grand_totals['investment']:.2f}",
            f"{grand_totals['bd_expense']:.2f}",
            f"{grand_totals['balance']:.2f}"
        ), tags=('total',))

        if active_months_count == 0: active_months_count = 1
        self.summary_tree.insert('', 'end', values=(
            "AVERAGE",
            f"{grand_totals['income']/active_months_count:.2f}",
            f"{grand_totals['expense']/active_months_count:.2f}",
            f"{grand_totals['investment']/active_months_count:.2f}",
            f"{grand_totals['bd_expense']/active_months_count:.2f}",
            f"{grand_totals['balance']/active_months_count:.2f}"
        ), tags=('average',))

    # --- Helper Methods (Input) ---
    def manage_subcategories(self):
        """Dialog to manage 3 levels: Cat -> Sub -> SubSub"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manage Sub-Subcategories")
        dialog.geometry("800x600")
        
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        select_frame = ttk.LabelFrame(main_frame, text="Selection", padding=5)
        select_frame.pack(side='left', fill='y', padx=5)
        
        ttk.Label(select_frame, text="Select Category:").pack(anchor='w', pady=2)
        self.cat_sel_var = tk.StringVar()
        self.cat_sel_combo = ttk.Combobox(select_frame, textvariable=self.cat_sel_var, values=self.categories, state="readonly")
        self.cat_sel_combo.pack(fill='x', pady=2)
        self.cat_sel_combo.bind("<<ComboboxSelected>>", self.refresh_subsub_subcat_list)
        
        ttk.Label(select_frame, text="Select Subcategory:").pack(anchor='w', pady=2)
        self.sub_sel_var = tk.StringVar()
        self.sub_sel_combo = ttk.Combobox(select_frame, textvariable=self.sub_sel_var, state="readonly")
        self.sub_sel_combo.pack(fill='x', pady=2)
        self.sub_sel_combo.bind("<<ComboboxSelected>>", self.refresh_subsub_subcat_list)
        
        list_frame = ttk.LabelFrame(main_frame, text="Sub-Subcategories", padding=5)
        list_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        add_frame = ttk.Frame(list_frame)
        add_frame.pack(fill='x', pady=5)
        ttk.Label(add_frame, text="Add Sub-subcategory:").pack(side='left')
        self.new_subsub_entry = ttk.Entry(add_frame, width=30)
        self.new_subsub_entry.pack(side='left', padx=5)
        ttk.Button(add_frame, text="Add", command=self.add_sub_subcategory).pack(side='left', padx=5)
        
        self.subsub_tree = ttk.Treeview(list_frame, columns=('name',), show='headings', height=15)
        self.subsub_tree.heading('name', text='Name')
        self.subsub_tree.column('name', width=200, anchor='w')
        
        vs = ttk.Scrollbar(list_frame, orient="vertical", command=self.subsub_tree.yview)
        self.subsub_tree.configure(yscrollcommand=vs.set)
        self.subsub_tree.pack(side='left', fill='both', expand=True)
        vs.pack(side='right', fill='y')
        
        self.refresh_subsub_subcat_list()

    def refresh_subsub_subcat_list(self, event=None):
        cat = self.cat_sel_var.get()
        sub = self.sub_sel_var.get()
        
        for item in self.subsub_tree.get_children():
            self.subsub_tree.delete(item)
            
        if not cat: return
        
        subs = self.subcategories.get(cat, {})
        if sub:
            items = subs.get(sub, [])
            for i in items:
                self.subsub_tree.insert('', 'end', values=(i,))
        elif subs: 
            for k, v in subs.items():
                self.subsub_tree.insert('', 'end', values=(f"{k} (Category)",))

    def add_sub_subcategory(self):
        cat = self.cat_sel_var.get()
        sub = self.sub_sel_var.get()
        val = self.new_subsub_entry.get().strip()
        
        if not cat or not sub or not val:
            messagebox.showwarning("Warning", "Please select Category and Subcategory")
            return
            
        if cat not in self.subcategories: self.subcategories[cat] = {}
        if sub not in self.subcategories[cat]: self.subcategories[cat][sub] = []
        
        if val in self.subcategories[cat][sub]:
            messagebox.showwarning("Warning", "Already exists")
            return
            
        self.subcategories[cat][sub].append(val)
        self.save_data()
        self.refresh_subsub_subcat_list()
        self.new_subsub_entry.delete(0, 'end')
        
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
        main_container = ttk.Frame(self.database_tab)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        top_section = ttk.LabelFrame(main_container, text="Categories View", padding=5)
        top_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        top_filter_frame = ttk.Frame(top_section)
        top_filter_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(top_filter_frame, text="Year:").pack(side='left', padx=5)
        self.db_year_var = tk.StringVar(value=str(datetime.now().year))
        years = [str(y) for y in range(2020, 2031)]
        ttk.Combobox(top_filter_frame, textvariable=self.db_year_var, values=years, width=10).pack(side='left', padx=5)
        
        ttk.Label(top_filter_frame, text="Month:").pack(side='left', padx=5)
        self.db_month_var = tk.StringVar(value="All")
        months = ["All"] + [str(i) for i in range(1, 13)]
        ttk.Combobox(top_filter_frame, textvariable=self.db_month_var, values=months, width=10).pack(side='left', padx=5)
        
        ttk.Button(top_filter_frame, text="Update", command=self.update_category_table).pack(side='left', padx=10)
        ttk.Button(top_filter_frame, text="Export CSV", command=self.export_csv).pack(side='left', padx=5)
        ttk.Button(top_filter_frame, text="Import CSV", command=self.import_csv).pack(side='left', padx=5)
        
        cat_table_frame = ttk.Frame(top_section)
        cat_table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        cat_v_scroll = ttk.Scrollbar(cat_table_frame, orient='vertical')
        cat_h_scroll = ttk.Scrollbar(cat_table_frame, orient='horizontal')
        
        self.cat_tree = ttk.Treeview(cat_table_frame, yscrollcommand=cat_v_scroll.set, 
                                     xscrollcommand=cat_h_scroll.set, height=6)
        cat_v_scroll.config(command=self.cat_tree.yview)
        cat_h_scroll.config(command=self.cat_tree.xview)
        
        cat_v_scroll.pack(side='right', fill='y')
        cat_h_scroll.pack(side='bottom', fill='x')
        self.cat_tree.pack(side='left', fill='both', expand=True)
        
        mid_section = ttk.LabelFrame(main_container, text="Subcategories View", padding=5)
        mid_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        mid_filter_frame = ttk.Frame(mid_section)
        mid_filter_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(mid_filter_frame, text="Category:").pack(side='left', padx=5)
        self.subcat_filter_cat_var = tk.StringVar()
        self.subcat_filter_cat_combo = ttk.Combobox(mid_filter_frame, textvariable=self.subcat_filter_cat_var,
                                                   values=self.categories, width=20)
        self.subcat_filter_cat_combo.pack(side='left', padx=5)
        
        ttk.Button(mid_filter_frame, text="Update", command=self.update_subcategory_table).pack(side='left', padx=10)
        
        subcat_table_frame = ttk.Frame(mid_section)
        subcat_table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        subcat_v_scroll = ttk.Scrollbar(subcat_table_frame, orient='vertical')
        subcat_h_scroll = ttk.Scrollbar(subcat_table_frame, orient='horizontal')
        
        self.subcat_tree = ttk.Treeview(subcat_table_frame, yscrollcommand=subcat_v_scroll.set,
                                        xscrollcommand=subcat_h_scroll.set, height=6)
        subcat_v_scroll.config(command=self.subcat_tree.yview)
        subcat_h_scroll.config(command=self.subcat_tree.xview)
        
        subcat_v_scroll.pack(side='right', fill='y')
        subcat_h_scroll.pack(side='bottom', fill='x')
        self.subcat_tree.pack(side='left', fill='both', expand=True)
        
        bot_section = ttk.LabelFrame(main_container, text="Sub-Subcategories View", padding=5)
        bot_section.pack(fill='both', expand=True, padx=5, pady=5)
        
        bot_filter_frame = ttk.Frame(bot_section)
        bot_filter_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(bot_filter_frame, text="Category:").pack(side='left', padx=5)
        self.subsub_filter_cat_var = tk.StringVar()
        self.subsub_filter_cat_combo = ttk.Combobox(bot_filter_frame, textvariable=self.subsub_filter_cat_var,
                                                   values=self.categories, width=20)
        self.subsub_filter_cat_combo.pack(side='left', padx=5)
        
        ttk.Label(bot_filter_frame, text="Subcategory:").pack(side='left', padx=5)
        self.subsub_filter_sub_var = tk.StringVar()
        self.subsub_filter_sub_combo = ttk.Combobox(bot_filter_frame, textvariable=self.subsub_filter_sub_var,
                                                   state="readonly", width=20) 
        self.subsub_filter_cat_combo.bind('<<ComboboxSelected>>', self.update_subsub_filter_sub_combo)
        
        ttk.Button(bot_filter_frame, text="Update", command=self.update_subsubcategory_table).pack(side='left', padx=10)
        
        subsub_table_frame = ttk.Frame(bot_section)
        subsub_table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        subsub_v_scroll = ttk.Scrollbar(subsub_table_frame, orient='vertical')
        subsub_h_scroll = ttk.Scrollbar(subsub_table_frame, orient='horizontal')
        
        self.subsub_tree = ttk.Treeview(subsub_table_frame, yscrollcommand=subsub_v_scroll.set,
                                        xscrollcommand=subsub_h_scroll.set, height=6)
        subsub_v_scroll.config(command=self.subsub_tree.yview)
        subsub_h_scroll.config(command=self.subsub_tree.xview)
        
        subsub_v_scroll.pack(side='right', fill='y')
        subsub_h_scroll.pack(side='bottom', fill='x')
        self.subsub_tree.pack(side='left', fill='both', expand=True)

        self.update_category_table()

    def update_subsub_filter_sub_combo(self, event=None):
        cat = self.subsub_filter_cat_var.get()
        if cat in self.subcategories:
            self.subsub_filter_sub_combo['values'] = list(self.subcategories[cat].keys())
            if self.subsub_filter_sub_combo['values']:
                self.subsub_filter_sub_var.current(0)
        
    # --- Database Update Functions ---
    def update_category_table(self):
        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)
        
        # Check if categories exist
        if not self.categories:
            self.cat_tree.insert('', 'end', values=('No Data',))
            return

        year = self.db_year_var.get()
        month_filter = self.db_month_var.get()
        
        monthly_data = defaultdict(lambda: defaultdict(float))
        
        for trans in self.transactions:
            trans_date = trans['date']
            parts = trans_date.split('/')
            trans_month = parts[1]
            trans_year = parts[2]
            
            if trans_year != year:
                continue
            if month_filter != "All" and trans_month != month_filter.zfill(2):
                continue
            
            month_key = f"{trans_month}/{trans_year}"
            category = trans['category']
            monthly_data[month_key][category] += trans['amount']
        
        columns = ['Month'] + self.categories + ['Total']
        self.cat_tree['columns'] = columns
        self.cat_tree['show'] = 'headings'
        
        for col in columns:
            self.cat_tree.heading(col, text=col)
            self.cat_tree.column(col, width=110, anchor='center')
        
        category_totals = defaultdict(float)
        
        for month in sorted(monthly_data.keys(), key=lambda x: datetime.strptime(x, '%m/%Y')):
            row_data = [month]
            row_total = 0
            for cat in self.categories:
                amount = monthly_data[month][cat]
                row_data.append(f"€{amount:.2f}")
                row_total += amount
                category_totals[cat] += amount
            row_data.append(f"€{row_total:.2f}")
            self.cat_tree.insert('', 'end', values=row_data)
        
        total_row = ['TOTAL']
        grand_total = 0
        for cat in self.categories:
            total_row.append(f"€{category_totals[cat]:.2f}")
            grand_total += category_totals[cat]
        total_row.append(f"€{grand_total:.2f}")
        self.cat_tree.insert('', 'end', values=total_row, tags=('total',))
        
        # Average
        avg_row = ['AVERAGE']
        for cat in self.categories:
            avg_row.append(f"€{category_totals[cat]/12:.2f}") 
        avg_row.append(f"€{grand_total/12:.2f}")
        self.cat_tree.insert('', 'end', values=avg_row, tags=('avg',))
        self.cat_tree.tag_configure('total', background='#EF9A9A', font=('Arial', 9, 'bold'))
        self.cat_tree.tag_configure('avg', background='#C5E1A5', font=('Arial', 9, 'bold'))

    def update_subcategory_table(self):
        for item in self.subcat_tree.get_children():
            self.subcat_tree.delete(item)
        
        cat = self.subcat_filter_cat_var.get()
        year = self.db_year_var.get()
        month_filter = self.db_month_var.get()
        
        if not cat: return
        
        subs = self.subcategories.get(cat, {})
        if isinstance(subs, dict):
            subs_list = list(subs.keys())
        elif isinstance(subs, list):
            subs_list = subs
        else:
            subs_list = []
            
        # Check if subs are empty
        if not subs_list:
            self.subcat_tree.insert('', 'end', values=('No Data',))
            return
            
        columns = ['Month'] + subs_list + ['Total']
        self.subcat_tree['columns'] = columns
        self.subcat_tree['show'] = 'headings'
        
        for col in columns:
            self.subcat_tree.heading(col, text=col)
            self.subcat_tree.column(col, width=110, anchor='center')
        
        subcat_totals = defaultdict(float)
        
        for m in range(1, 13):
            if month_filter != "All" and str(m) != month_filter: continue
            
            row_data = [datetime(2023, m, 1).strftime('%B')]
            row_total = 0
            
            for sub in subs_list:
                amount = 0
                for t in self.transactions:
                    d_parts = t['date'].split('/')
                    t_year = int(d_parts[2])
                    t_mo = int(d_parts[1])
                    
                    if t_year != int(year): continue
                    if month_filter != "All" and str(t_mo) != month_filter: continue
                    
                    if t['category'] == cat and t['subcategory'] == sub:
                        amount += t['amount']
                        
                row_data.append(f"{amount:.2f}")
                row_total += amount
                subcat_totals[sub] += amount
            
            row_data.append(f"{row_total:.2f}")
            self.subcat_tree.insert('', 'end', values=row_data)
            
        total_row = ['TOTAL']
        grand_total = 0
        for sub in subs_list:
            total_row.append(f"{subcat_totals[sub]:.2f}")
            grand_total += subcat_totals[sub]
        total_row.append(f"{grand_total:.2f}")
        self.subcat_tree.insert('', 'end', values=total_row, tags=('total',))
        
        # Average
        num_months = 12 if month_filter == "All" else 1
        avg_row = ['AVERAGE']
        for sub in subs_list:
            avg_row.append(f"{subcat_totals[sub]/num_months:.2f}")
        avg_row.append(f"{grand_total/num_months:.2f}")
        self.subcat_tree.insert('', 'end', values=avg_row, tags=('avg',))
        
        self.subcat_tree.tag_configure('total', background='#EF9A9A', font=('Arial', 9, 'bold'))
        self.subcat_tree.tag_configure('avg', background='#C5E1A5', font=('Arial', 9, 'bold'))

    def update_subsubcategory_table(self):
        """Shows Sub-subcategories along column and months along row"""
        for item in self.subsub_tree.get_children():
            self.subsub_tree.delete(item)
        
        cat = self.subsub_filter_cat_var.get()
        sub = self.subsub_filter_sub_var.get()
        year = self.db_year_var.get()
        month_filter = self.db_month_var.get()
        
        if not cat or not sub: return
        
        subs = self.subcategories.get(cat, {}).get(sub, [])
        if isinstance(subs, list):
            pass
        else:
            subs = []
            
        # Check if subs are empty
        if not subs:
            self.subsub_tree.insert('', 'end', values=('No Data',))
            return
        
        columns = ['Month'] + subs + ['Total']
        self.subsub_tree['columns'] = columns
        self.subsub_tree['show'] = 'headings'
        
        # Dynamic column widths based on count
        num_cols = len(columns)
        col_w = 100 if num_cols > 5 else 140
        for col in columns:
            self.subsub_tree.heading(col, text=col)
            self.subsub_tree.column(col, width=col_w, anchor='center')
        
        subsub_totals = defaultdict(float)
        
        for m in range(1, 13):
            if month_filter != "All" and str(m) != month_filter: continue
            
            row_data = [datetime(2023, m, 1).strftime('%B')]
            row_total = 0
            
            for subsub in subs:
                amount = 0
                for t in self.transactions:
                    d_parts = t['date'].split('/')
                    t_year = int(d_parts[2])
                    t_mo = int(d_parts[1])
                    
                    if t_year != int(year): continue
                    if month_filter != "All" and str(t_mo) != month_filter: continue
                    
                    if t['category'] == cat and t['subcategory'] == sub and t.get('subsubcategory', '') == subsub:
                        amount += t['amount']
                
                row_data.append(f"{amount:.2f}")
                row_total += amount
                subsub_totals[subsub] += amount
            
            row_data.append(f"{row_total:.2f}")
            self.subsub_tree.insert('', 'end', values=row_data)
            
        total_row = ['TOTAL']
        grand_total = 0
        for subsub in subs:
            total_row.append(f"{subsub_totals[subsub]:.2f}")
            grand_total += subsub_totals[subsub]
        total_row.append(f"{grand_total:.2f}")
        self.subsub_tree.insert('', 'end', values=total_row, tags=('total',))
        
        # Average
        num_months = 12 if month_filter == "All" else 1
        avg_row = ['AVERAGE']
        for subsub in subs:
            avg_row.append(f"{subsub_totals[subsub]/num_months:.2f}")
        avg_row.append(f"{grand_total/num_months:.2f}")
        self.subsub_tree.insert('', 'end', values=avg_row, tags=('avg',))
        
        self.subsub_tree.tag_configure('total', background='#d0e0ff', font=('Arial', 9, 'bold'))
        self.subsub_tree.tag_configure('avg', background='#C5E1A5', font=('Arial', 9, 'bold'))

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
        
        # REMOVED: Matrix Summary Tab
        # REMOVED: Transaction Log

        self.update_bd_category_combos()

    # Fix for create_bd_subcategories_view method
    def create_bd_subcategories_view(self, parent_frame):
        # Filter
        filter_frame = ttk.LabelFrame(parent_frame, text="Filters", padding=5)
        filter_frame.pack(fill='x', pady=5)
        
        ttk.Label(filter_frame, text="Category:").pack(side='left')
        self.bd_subcat_filter_cat = tk.StringVar()
        bd_subcat_combo = ttk.Combobox(filter_frame, textvariable=self.bd_subcat_filter_cat, values=self.categories, width=20)
        bd_subcat_combo.pack(side='left', padx=5)
        bd_subcat_combo.bind('<<ComboboxSelected>>', lambda e: self.update_bd_subcategories_table(parent_frame))
        
        ttk.Button(filter_frame, text="Update", command=lambda: self.update_bd_subcategories_table(parent_frame)).pack(side='left', padx=10)
        
        # Tree
        table_frame = ttk.Frame(parent_frame)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.bd_subcat_tree_view = ttk.Treeview(table_frame, height=8)
        self.bd_subcat_tree_view.pack(fill='both', expand=True)
        vs = ttk.Scrollbar(table_frame, orient="vertical", command=self.bd_subcat_tree_view.yview)
        self.bd_subcat_tree_view.configure(yscrollcommand=vs.set)
        vs.pack(side='right', fill='y')
        self.bd_subcat_tree_view.pack(side='left', fill='both', expand=True)
        
        self.update_bd_subcategories_table(parent_frame)

    # Fix for create_bd_subsubcategories_view method (around line 1560)
    def create_bd_subsubcategories_view(self, parent_frame):
        # Filter
        filter_frame = ttk.LabelFrame(parent_frame, text="Filters", padding=5)
        filter_frame.pack(fill='x', pady=5)
        
        ttk.Label(filter_frame, text="Category:").pack(side='left')
        self.bd_subsubcat_filter_cat = tk.StringVar() # Instance variable
        bd_subsubcat_cat_combo = ttk.Combobox(filter_frame, textvariable=self.bd_subsubcat_filter_cat, values=self.categories, width=20)
        bd_subsubcat_cat_combo.pack(side='left', padx=5)
        
        ttk.Label(filter_frame, text="Subcategory:").pack(side='left')
        self.bd_subsubcat_filter_sub = tk.StringVar() # Instance variable
        bd_subsubcat_sub_combo = ttk.Combobox(filter_frame, textvariable=self.bd_subsubcat_filter_sub, state="readonly", width=20)
        bd_subsubcat_sub_combo.pack(side='left', padx=5)
        
        # Fix: Bind to combo widget to update subcategory options
        bd_subsubcat_cat_combo.bind('<<ComboboxSelected>>', 
                                    lambda e: self.update_bd_subsub_filter_subs(bd_subsubcat_sub_combo))
        
        ttk.Button(filter_frame, text="Update", command=lambda: self.update_bd_subsubcategories_table(parent_frame)).pack(side='left', padx=10)
        
        # Tree
        table_frame = ttk.Frame(parent_frame)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.bd_subsubcat_tree_view = ttk.Treeview(table_frame, height=8)
        self.bd_subsubcat_tree_view.pack(fill='both', expand=True)
        vs = ttk.Scrollbar(table_frame, orient="vertical", command=self.bd_subsubcat_tree_view.yview)
        self.bd_subsubcat_tree_view.configure(yscrollcommand=vs.set)
        vs.pack(side='right', fill='y')
        self.bd_subsubcat_tree_view.pack(side='left', fill='both', expand=True)
        
        self.update_bd_subsubcategories_table(parent_frame)

    # Add this helper method
    def update_bd_subsub_filter_subs(self, combo_widget):
        """Update subcategory options based on selected category"""
        cat = self.bd_subsubcat_filter_cat.get()
        if cat in self.subcategories:
            subs = list(self.subcategories.get(cat, {}).keys())
            combo_widget['values'] = subs
            if subs: 
                self.bd_subsubcat_filter_sub.set(subs[0])
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
    def create_bd_categories_view(self, parent_frame):
        # Filter
        filter_frame = ttk.LabelFrame(parent_frame, text="Filters", padding=5)
        filter_frame.pack(fill='x', pady=5)
        
        ttk.Label(filter_frame, text="Year:").pack(side='left')
        self.bd_cat_year_var = tk.StringVar(value=str(datetime.now().year))
        ttk.Combobox(filter_frame, textvariable=self.bd_cat_year_var, values=[str(y) for y in range(2020, 2031)], width=10).pack(side='left', padx=5)
        
        ttk.Label(filter_frame, text="Month:").pack(side='left')
        self.bd_cat_month_var = tk.StringVar(value="All")
        ttk.Combobox(filter_frame, textvariable=self.bd_cat_month_var, values=["All"]+[str(i) for i in range(1, 13)], width=10).pack(side='left', padx=5)
        
        ttk.Button(filter_frame, text="Update", command=lambda: self.update_bd_categories_table(parent_frame)).pack(side='left', padx=10)
        
        # Tree
        table_frame = ttk.Frame(parent_frame)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.bd_cat_tree_view = ttk.Treeview(table_frame, height=8)
        self.bd_cat_tree_view.pack(fill='both', expand=True)
        vs = ttk.Scrollbar(table_frame, orient="vertical", command=self.bd_cat_tree_view.yview)
        self.bd_cat_tree_view.configure(yscrollcommand=vs.set)
        vs.pack(side='right', fill='y')
        self.bd_cat_tree_view.pack(side='left', fill='both', expand=True)
        
        self.update_bd_categories_table(parent_frame)

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

    
    def update_bd_subcategories_table(self, parent_frame):
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

    

    def update_bd_subsubcategories_table(self, parent_frame):
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

    def update_bd_subsub_filter_subs(self, combo_widget):
        """Update subcategory options based on selected category"""
        cat = self.bd_subsubcat_filter_cat.get()
        if cat in self.subcategories:
            subs = list(self.subcategories.get(cat, {}).keys())
            combo_widget['values'] = subs
            if subs: 
                self.bd_subsubcat_filter_sub.set(subs[0])
                


    # def create_bd_matrix_view(self, parent_frame):
    #     """The previous Group By logic"""
    #     # Filter for Matrix
    #     filter_mat = ttk.LabelFrame(parent_frame, text="Matrix Settings", padding=10)
    #     filter_mat.pack(fill='x', pady=5)
        
    #     ttk.Label(filter_mat, text="Group By:").pack(side='left')
    #     self.bd_group_var = tk.StringVar(value="Category")
    #     self.bd_group_combo = ttk.Combobox(filter_mat, textvariable=self.bd_group_var, 
    #                                      values=["Category", "Subcategory", "Subsubcategory"], width=15)
    #     self.bd_group_combo.pack(side='left', padx=5)
    #     self.bd_group_combo.bind('<<ComboboxSelected>>', self.refresh_bd_summary_matrix)
        
    #     matrix_table_frame = ttk.Frame(parent_frame)
    #     matrix_table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
    #     self.bd_matrix_tree = ttk.Treeview(matrix_table_frame, height=8)
    #     self.bd_matrix_tree.pack(fill='both', expand=True, padx=5)
        
    #     vs_mat = ttk.Scrollbar(matrix_table_frame, orient="vertical", command=self.bd_matrix_tree.yview)
    #     self.bd_matrix_tree.configure(yscrollcommand=vs_mat.set)
    #     vs_mat.pack(side='right', fill='y')
        
    #     self.refresh_bd_summary_matrix()

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
                                        values=["Profit", "Dividend", "Capital Gain"], width=23, state="readonly")
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
    def create_analysis_tab(self):
        filter_frame = ttk.LabelFrame(self.analysis_tab, text="Filters", padding=10)
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Year:").grid(row=0, column=0, padx=5)
        self.analysis_year_var = tk.StringVar(value=str(datetime.now().year))
        years = [str(y) for y in range(2020, 2031)]
        ttk.Combobox(filter_frame, textvariable=self.analysis_year_var, values=years, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(filter_frame, text="Month (for Euro pie):").grid(row=0, column=2, padx=5)
        self.analysis_month_var = tk.StringVar(value=str(datetime.now().month))
        months = [str(i) for i in range(1, 13)]
        ttk.Combobox(filter_frame, textvariable=self.analysis_month_var, values=months, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Button(filter_frame, text="Update Charts", command=self.update_analysis_charts).grid(row=0, column=4, padx=10)
        
        self.charts_frame = ttk.Frame(self.analysis_tab)
        self.charts_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.charts_frame.bind('<Configure>', self.on_chart_resize)
        self.update_analysis_charts()
    
    def on_chart_resize(self, event):
        self.update_analysis_charts()
        
    def update_analysis_charts(self):
        for widget in self.charts_frame.winfo_children():
            widget.destroy()
        
        year = self.analysis_year_var.get()
        month = self.analysis_month_var.get().zfill(2)
        
        w = self.charts_frame.winfo_width()
        h = self.charts_frame.winfo_height()
        
        if w < 100: w = 1500 
        if h < 100: h = 900
        fig_w, fig_h = w / 100, h / 100
        
        fig = Figure(figsize=(fig_w, fig_h), dpi=90)
        
        # 1. Income vs Expense Bar Chart
        ax1 = fig.add_subplot(3, 2, (1, 2))
        monthly_income = defaultdict(float)
        monthly_expense = defaultdict(float)
        
        for income in self.income_sources:
            if income['date'].endswith(year):
                m = income['date'].split('/')[1]
                monthly_income[int(m)] += income['amount']
        
        for trans in self.transactions:
            if trans['date'].endswith(year):
                m = trans['date'].split('/')[1]
                monthly_expense[int(m)] += trans['amount']
        
        months_list = list(range(1, 13))
        income_vals = [monthly_income[m] for m in months_list]
        expense_vals = [monthly_expense[m] for m in months_list]
        
        x = range(1, 13)
        width = 0.35
        bars1 = ax1.bar([i - width/2 for i in x], income_vals, width, label='Income', color='green', alpha=0.7)
        bars2 = ax1.bar([i + width/2 for i in x], expense_vals, width, label='Expense', color='red', alpha=0.7)
        
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'€{height:.0f}',
                            ha='center', va='bottom', fontsize=8)
        
        ax1.set_xlabel('Month')
        ax1.set_ylabel('Amount (€)')
        ax1.set_title(f'Income vs Expense - {year}', fontweight='bold')
        ax1.set_xticks(x)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # 2. Monthly Euro Expenses Pie Chart
        ax2 = fig.add_subplot(3, 2, 3)
        monthly_cat_expense = defaultdict(float)
        
        for trans in self.transactions:
            if trans['date'].endswith(f"{month}/{year}"):
                monthly_cat_expense[trans['category']] += trans['amount']
        
        if monthly_cat_expense:
            labels = list(monthly_cat_expense.keys())
            sizes = list(monthly_cat_expense.values())
            colors = plt.cm.Set2(range(len(labels)))
            
            wedges, texts, autotexts = ax2.pie(sizes, labels=labels, autopct='%1.1f%%',
                                                colors=colors, startangle=90)
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontweight('bold')
            ax2.set_title(f'Expenses by Category - {month}/{year}', fontweight='bold')
        else:
            ax2.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title(f'Expenses by Category - {month}/{year}', fontweight='bold')
        
        # 3. Yearly Euro Expenses Pie Chart
        ax3 = fig.add_subplot(3, 2, 4)
        yearly_cat_expense = defaultdict(float)
        
        for trans in self.transactions:
            if trans['date'].endswith(year):
                yearly_cat_expense[trans['category']] += trans['amount']
        
        if yearly_cat_expense:
            labels = list(yearly_cat_expense.keys())
            sizes = list(yearly_cat_expense.values())
            colors = plt.cm.Paired(range(len(labels)))
            
            wedges, texts, autotexts = ax3.pie(sizes, labels=labels, autopct='%1.1f%%',
                                                colors=colors, startangle=90)
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontweight('bold')
            ax3.set_title(f'Yearly Expenses by Category - {year}', fontweight='bold')
        else:
            ax3.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title(f'Yearly Expenses by Category - {year}', fontweight='bold')

        # 4. BD Expenses Pie Chart (Bottom)
        ax4 = fig.add_subplot(3, 2, (5, 6))
        bd_cat_expense = defaultdict(float)
        
        for trans in self.bd_transactions:
            if trans['date'].endswith(year):
                bd_cat_expense[trans['category']] += trans['amount']
        
        if bd_cat_expense:
            labels = list(bd_cat_expense.keys())
            sizes = list(bd_cat_expense.values())
            colors = plt.cm.Pastel1(range(len(labels)))
            
            wedges, texts, autotexts = ax4.pie(sizes, labels=labels, autopct='%1.1f%%',
                                                colors=colors, startangle=90)
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontweight('bold')
            ax4.set_title(f'BD Expenses by Category - {year} (Taka)', fontweight='bold', fontsize=14)
        else:
            ax4.text(0.5, 0.5, 'No BD Data', ha='center', va='center', transform=ax4.transAxes, fontsize=14)
            ax4.set_title(f'BD Expenses by Category - {year}', fontweight='bold', fontsize=14)
        
        fig.tight_layout(pad=3.0)
        canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

def main():
    root = tk.Tk()
    app = FinanceManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
