import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ==========================================
# Data Manager & Backend Logic
# ==========================================

class DataManager:
    def __init__(self):
        self.filename = "finance_data.json"
        # CSV File saved in the same folder as script
        self.csv_filename = "finance_data.csv"
        # Default rate 100
        self.DEFAULT_RATE = 140.0
        
        self.defaults = {
            "initial_balance_eur": 0.0,
            "current_balance_eur": 0.0,
            "current_balance_bd": 0.0,
            "categories": {
                "GER": {"Food": {"Groceries": {}, "Restaurant": {}}, "Transport": {"Fuel": {}, "Ticket": {}}},
                "BD": {"Food": {"Bazar": {}, "Outside": {}}, "Transport": {"Rickshaw": {}, "CNG": {}}}
            },
            "income": [],
            "expenses": [],
            "investments": [],
            "conversion_rates": {}
        }
        
        self.data = self.defaults.copy()
        # Load data order: 1. Load JSON (Primary), 2. Load CSV (Conditional to prevent loop)
        self.load_data()
        self.load_data_csv_conditional() 

    def save_data(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.data, f, indent=4, default=str)
        except Exception as e:
            print(f"Error saving JSON data: {e}")

    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    loaded_data = json.load(f)
                
                if not isinstance(loaded_data, dict):
                    self.data = self.defaults
                    return

                for key, value in self.defaults.items():
                    if key not in loaded_data:
                        loaded_data[key] = value
                
                if not isinstance(loaded_data.get("categories", {}), dict):
                    loaded_data["categories"] = self.defaults["categories"]
                
                for region in ["GER", "BD"]:
                    if region not in loaded_data["categories"]:
                        loaded_data["categories"][region] = {}

                self.data = loaded_data
            except Exception as e:
                print(f"Error loading JSON, using defaults: {e}")
                self.data = self.defaults
        else:
            self.data = self.defaults

    # --- CSV Load / Save Functions ---
    def save_data_csv(self):
        # Save everything to ONE file: finance_data.csv
        rows = []
        
        # 1. Process Income
        for item in self.data["income"]:
            rows.append({
                "Record Type": "Income",
                "Date": item["date"],
                "Region": "",
                "Category": "",
                "Subcategory": "",
                "Sub Subcategory": "",
                "Amount Local": 0,
                "Amount EUR": item["amount"],
                "Rate": 1.0,
                "Source": item["source"],
                "Type": "",
                "Description": "",
                "Name": "",
                "Address": ""
            })
            
        # 2. Process Expenses
        for item in self.data["expenses"]:
            rows.append({
                "Record Type": "Expense",
                "Date": item["date"],
                "Region": item["region"],
                "Category": item["category"],
                "Subcategory": item["subcategory"],
                "Sub Subcategory": item["subsubcategory"],
                "Amount Local": item["amount_local"],
                "Amount EUR": item["amount_eur"],
                "Rate": item["rate"],
                "Source": "",
                "Type": "",
                "Description": "",
                "Name": "",
                "Address": ""
            })
            
        # 3. Process Investments
        for item in self.data["investments"]:
            rows.append({
                "Record Type": "Investment",
                "Date": item["date"],
                "Region": "",
                "Category": item["category"],
                "Subcategory": "",
                "Sub Subcategory": "",
                "Amount Local": 0,
                "Amount EUR": item["amount"],
                "Rate": 1.0,
                "Source": "",
                "Type": item["type"], # Investment vs Return
                "Description": item["description"],
                "Name": item["name"] if "name" in item else "",
                "Address": item["address"] if "address" in item else ""
            })
            
        df = pd.DataFrame(rows)
        
        try:
            # Overwrite mode ('w') ensures we don't keep adding duplicates on repeated saves
            df.to_csv(self.csv_filename, mode='w', index=False)
        except Exception as e:
            print(f"Error saving CSV: {e}")

    def load_data_csv_conditional(self):
        # FIX: Only load CSV if JSON does not exist.
        # This prevents the "Loop of Death" where CSV loads -> JSON saves -> Restart repeats.
        if not os.path.exists(self.filename):
            files_exist = False
            
            # Read CSV
            if os.path.exists(self.csv_filename):
                try:
                    df = pd.read_csv(self.csv_filename)
                    
                    # Reconstruct JSON structure
                    inc = []
                    exp = []
                    inv = []
                    
                    for _, row in df.iterrows():
                        r_type = row["Record Type"]
                        if r_type == "Income":
                            inc.append({
                                "source": row["Source"],
                                "amount": row["Amount EUR"],
                                "date": row["Date"]
                            })
                        elif r_type == "Expense":
                            exp.append({
                                "region": row["Region"],
                                "category": row["Category"],
                                "subcategory": row["Subcategory"],
                                "subsubcategory": row["Sub Subcategory"],
                                "amount_local": row["Amount Local"],
                                "rate": row["Rate"],
                                "amount_eur": row["Amount EUR"],
                                "date": row["Date"]
                            })
                        elif r_type == "Investment":
                            inv.append({
                                "type": row["Type"], # Investment/Return
                                "category": row["Category"],
                                "amount": row["Amount EUR"],
                                "date": row["Date"],
                                "description": row["Description"],
                                "name": row["Name"] if pd.notnull(row["Name"]) else "",
                                "address": row["Address"] if pd.notnull(row["Address"]) else ""
                            })
                    
                    self.data["income"] = inc
                    self.data["expenses"] = exp
                    self.data["investments"] = inv
                    files_exist = True
                    
                except Exception as e:
                    print(f"Error reading CSV: {e}")
            
            if files_exist:
                self.save_data()

    def get_categories(self, region):
        return self.data["categories"].get(region, {})

    def update_category_structure(self, region, new_structure):
        self.data["categories"][region] = new_structure
        self.save_data()
        self.save_data_csv()

    def set_initial_balance(self, amount_eur):
        self.data["initial_balance_eur"] = float(amount_eur)
        self.save_data()
        self.save_data_csv()

    def add_income(self, source, amount, date, type="EUR"):
        entry = {"source": source, "amount": float(amount), "date": date, "type": type}
        self.data["income"].append(entry)
        self.data["current_balance_eur"] += float(amount)
        self.save_data()
        self.save_data_csv()

    def add_bd_deposit(self, amount_tk):
        self.data["current_balance_bd"] += amount_tk
        self.save_data()
        self.save_data_csv()

    def add_expense(self, region, cat, sub, subsub, amount_local, rate, date):
        amount_local = float(amount_local)
        
        if region == "GER":
            rate = 1.0
            amount_eur = amount_local
        else:
            if not rate or float(rate) == 0:
                rate = self.DEFAULT_RATE
            else:
                rate = float(rate)
            amount_eur = amount_local / rate if rate > 0 else 0
        
        entry = {
            "region": region,
            "category": cat,
            "subcategory": sub,
            "subsubcategory": subsub,
            "amount_local": amount_local,
            "rate": rate,
            "amount_eur": amount_eur,
            "date": date
        }
        self.data["expenses"].append(entry)
        
        if region == "BD":
            self.data["current_balance_bd"] -= amount_local
        else:
            self.data["current_balance_eur"] -= amount_local
        self.save_data()
        self.save_data_csv()

    def add_investment(self, inv_type, category, amount, date, description, name=None, address=None):
        entry = {
            "type": inv_type, 
            "category": category,
            "amount": float(amount),
            "date": date,
            "description": description,
            "name": name,
            "address": address
        }
        self.data["investments"].append(entry)
        self.data["current_balance_eur"] -= float(amount)
        self.save_data()
        self.save_data_csv()

    def get_summary_df(self):
        # These are just helpers for the Analysis tab
        inc_df = pd.DataFrame(self.data["income"])
        if not inc_df.empty:
            inc_df["month_dt"] = pd.to_datetime(inc_df["date"])
            inc_df["month"] = inc_df["month_dt"].dt.to_period("M")
            inc_grp = inc_df.groupby("month")["amount"].sum().reset_index()
        else:
            inc_grp = pd.DataFrame(columns=["month", "amount"])

        exp_df = pd.DataFrame(self.data["expenses"])
        if not exp_df.empty:
            exp_df["month_dt"] = pd.to_datetime(exp_df["date"])
            exp_df["month"] = exp_df["month_dt"].dt.to_period("M")
            exp_df["amount_eur"] = pd.to_numeric(exp_df["amount_eur"], errors='coerce').fillna(0)
            
            exp_grp_eur = exp_df[exp_df["region"] == "GER"].groupby("month")["amount_eur"].sum().reset_index()
            exp_grp_bd_local = exp_df[exp_df["region"] == "BD"].groupby("month")["amount_local"].sum().reset_index()
            exp_grp_bd_eur = exp_df[exp_df["region"] == "BD"].groupby("month")["amount_local"].sum().reset_index()
            exp_grp_bd_eur["amount_eur"] = exp_grp_bd_eur["amount_local"] / self.DEFAULT_RATE
        else:
            exp_grp_eur = pd.DataFrame(columns=["month", "amount_eur"])
            exp_grp_bd_local = pd.DataFrame(columns=["month", "amount_local"])
            exp_grp_bd_eur = pd.DataFrame(columns=["month", "amount_eur"])
            
        inv_df = pd.DataFrame(self.data["investments"])
        if not inv_df.empty:
            inv_df["month_dt"] = pd.to_datetime(inv_df["date"])
            inv_df["month"] = inv_df["month_dt"].dt.to_period("M")
            inv_grp = inv_df[inv_df["type"] == "Investment"].groupby("month")["amount"].sum().reset_index()
            ret_grp = inv_df[inv_df["type"] == "Return"].groupby("month")["amount"].sum().reset_index()
        else:
            inv_grp = pd.DataFrame(columns=["month", "amount"])
            ret_grp = pd.DataFrame(columns=["month", "amount"])

        return inc_grp, exp_grp_eur, exp_grp_bd_local, exp_grp_bd_eur, inv_grp, ret_grp

    def get_kh_details(self):
        kh_list = []
        kh_df = pd.DataFrame(self.data["investments"])
        kh_df = kh_df[kh_df["category"] == "Karje hasana"]
        
        groups = kh_df.groupby("name")
        for name, group in groups:
            total_inv = group[group["type"] == "Investment"]["amount"].sum()
            total_ret = group[group["type"] == "Return"]["amount"].sum()
            if len(group) > 0:
                row = group.iloc[0]
                kh_list.append({
                    "Date": row["date"],
                    "Name/Org": name,
                    "Address": row.get("address", ""),
                    "Amount (Given)": total_inv,
                    "Return": total_ret,
                    "To Be Return": total_inv - total_ret
                })
        return kh_list

# ==========================================
# GUI Application
# ==========================================

class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Management System")
        self.root.geometry("1450x950")
        
        # DataManager Backend
        self.dm = DataManager()
        
        # Styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Bold.TLabel", font=("Helvetica", 10, "bold"))
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))
        style.configure("Highlight.TLabel", font=("Helvetica", 12, "bold"), foreground="blue", background="#e6f7ff")
        style.configure("Summary.Treeview", font=("Arial", 9))

        # Tabs
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)
        
        self.tab1 = ttk.Frame(self.tabs)
        self.tab2 = ttk.Frame(self.tabs)
        self.tab3 = ttk.Frame(self.tabs)
        
        self.tabs.add(self.tab1, text="Input")
        self.tabs.add(self.tab2, text="Database")
        self.tabs.add(self.tab3, text="Analysis")
        
        # Bind tab change
        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        # Setup UI
        self.setup_tab1()
        self.setup_tab2()
        self.setup_tab3()
        self.update_clock()
        # Initial summary population
        self.update_summary()

    def on_tab_change(self, event):
        selected_tab = self.tabs.index(self.tabs.select())
        # Auto-refresh when switching
        if selected_tab == 1: 
            self.generate_db_tables()
        elif selected_tab == 2:
            self.plot_trend()
            self.plot_pie()

    def refresh_all_tabs(self):
        """Helper to refresh Summary, Database, and Analysis tabs"""
        self.update_summary()
        if self.tabs.index(self.tabs.select()) == 1:
            self.generate_db_tables()
        elif self.tabs.index(self.tabs.select()) == 2:
             self.generate_db_tables()
        elif self.tabs.index(self.tabs.select()) == 3:
             self.plot_trend()
             self.plot_pie()

    def update_clock(self):
        now = datetime.now()
        if hasattr(self, 'clock_label'):
            self.clock_label.config(text=now.strftime("%H:%M:%S"))
        if hasattr(self, 'date_label'):
            self.date_label.config(text=now.strftime("%A, %d %B %Y"))
        self.root.after(1000, self.update_clock)

    # ==========================================
    # TAB 1: INPUT
    # ==========================================
    def setup_tab1(self):
        # --- Top Section ---
        top_frame = ttk.LabelFrame(self.tab1, text="Welcome")
        top_frame.pack(fill="x", padx=10, pady=5)
        
        canvas = tk.Canvas(top_frame, width=400, height=100, bg="skyblue")
        canvas.pack(side="left", padx=10)
        canvas.create_rectangle(150, 40, 250, 90, outline="white", width=3)
        canvas.create_line(200, 40, 200, 90, fill="white", width=3)
        canvas.create_line(150, 65, 250, 65, fill="white", width=3)
        canvas.create_oval(20, 10, 50, 40, fill="yellow", outline="orange")
        canvas.create_rectangle(50, 50, 70, 90, fill="brown") 
        canvas.create_oval(30, 20, 90, 60, fill="green") 
        
        lbl_frame = ttk.Frame(top_frame)
        lbl_frame.pack(side="left", fill="x", expand=True, padx=20)
        ttk.Label(lbl_frame, text="Bismillah hir rahmanir Rahim", font=("Times New Roman", 16, "italic")).pack(anchor="w")
        self.clock_label = ttk.Label(lbl_frame, font=("Arial", 14))
        self.clock_label.pack(anchor="w")
        self.date_label = ttk.Label(lbl_frame, font=("Arial", 12))
        self.date_label.pack(anchor="w")

        # Highlighted Balances
        ttk.Separator(lbl_frame, orient="horizontal").pack(fill="x", pady=5)
        self.lbl_total_bal_top = ttk.Label(lbl_frame, text="Total Balance: 0.00 EUR", style="Highlight.TLabel")
        self.lbl_total_bal_top.pack(anchor="w", pady=2)
        
        self.lbl_bd_bal_top = ttk.Label(lbl_frame, text="BD Balance: 0.00 Tk (0.00 EUR)", style="Highlight.TLabel", foreground="green")
        self.lbl_bd_bal_top.pack(anchor="w", pady=2)
        ttk.Separator(lbl_frame, orient="horizontal").pack(fill="x", pady=5)

        # --- Middle Section ---
        mid_frame = ttk.Frame(self.tab1)
        mid_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left: Income & Initial
        left_frame = ttk.LabelFrame(mid_frame, text="Income & Initial")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        
        # Income Form
        ttk.Label(left_frame, text="Source:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.inc_src = ttk.Combobox(left_frame, values=["Salary", "Profit", "Return", "Other"])
        self.inc_src.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(left_frame, text="Amount (EUR):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.inc_amt = ttk.Entry(left_frame)
        self.inc_amt.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(left_frame, text="Date:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        today = datetime.now().strftime("%Y-%m-%d")
        self.inc_date = ttk.Entry(left_frame)
        self.inc_date.insert(0, today)
        self.inc_date.grid(row=2, column=1, padx=5, pady=2)
        ttk.Button(left_frame, text="Add Income", command=self.add_income_action).grid(row=3, column=0, columnspan=2, pady=5)
        
        ttk.Separator(left_frame, orient="horizontal").grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)
        
        # Independent Initial Balance
        ttk.Label(left_frame, text="Initial Balance (EUR):").grid(row=5, column=0, sticky="w", padx=5)
        self.init_bal_entry = ttk.Entry(left_frame)
        self.init_bal_entry.insert(0, str(self.dm.data['initial_balance_eur']))
        self.init_bal_entry.grid(row=5, column=1, padx=5, pady=2)
        ttk.Button(left_frame, text="Update Initial", command=self.update_initial_bal).grid(row=6, column=0, columnspan=2, pady=2)
        
        ttk.Separator(left_frame, orient="horizontal").grid(row=7, column=0, columnspan=3, sticky="ew", pady=10)

        # Add Money to BD Section
        ttk.Label(left_frame, text="Add Money (BD Tk):").grid(row=8, column=0, sticky="w", padx=5)
        self.bd_deposit_amt = ttk.Entry(left_frame)
        self.bd_deposit_amt.grid(row=8, column=1, padx=5, pady=2)
        
        ttk.Label(left_frame, text="Rate (1 EUR = ? Tk):").grid(row=9, column=0, sticky="w", padx=5)
        self.bd_deposit_rate = ttk.Entry(left_frame)
        self.bd_deposit_rate.insert(0, str(int(self.dm.DEFAULT_RATE))) # Show 100
        self.bd_deposit_rate.grid(row=9, column=1, padx=5, pady=2)
        
        ttk.Button(left_frame, text="Deposit to BD", command=self.add_bd_deposit_action).grid(row=10, column=0, columnspan=2, pady=5)

        # Category Management (Left Bottom)
        cat_mgmt_frame = ttk.LabelFrame(left_frame, text="Category Management")
        cat_mgmt_frame.grid(row=11, column=0, columnspan=3, sticky="nsew", padx=5, pady=10)
        
        self.cat_region = ttk.Combobox(cat_mgmt_frame, values=["GER", "BD"], state="readonly")
        self.cat_region.current(0)
        self.cat_region.grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(cat_mgmt_frame, text="Manage Categories", command=self.open_category_manager).grid(row=0, column=1, padx=5)

        # Center: Expenditure
        center_frame = ttk.LabelFrame(mid_frame, text="Add Expenditure")
        center_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        ttk.Label(center_frame, text="Region:").grid(row=0, column=0, sticky="w", padx=5)
        self.exp_region = ttk.Combobox(center_frame, values=["GER", "BD"], state="readonly")
        self.exp_region.current(0)
        self.exp_region.grid(row=0, column=1, sticky="ew", padx=5)
        self.exp_region.bind("<<ComboboxSelected>>", self.populate_exp_cats)
        
        ttk.Label(center_frame, text="Category:").grid(row=1, column=0, sticky="w", padx=5)
        self.exp_cat = ttk.Combobox(center_frame, state="readonly")
        self.exp_cat.grid(row=1, column=1, sticky="ew", padx=5)
        self.exp_cat.bind("<<ComboboxSelected>>", self.populate_exp_sub)
        
        ttk.Label(center_frame, text="Subcategory:").grid(row=2, column=0, sticky="w", padx=5)
        self.exp_sub = ttk.Combobox(center_frame, state="readonly")
        self.exp_sub.grid(row=2, column=1, sticky="ew", padx=5)
        self.exp_sub.bind("<<ComboboxSelected>>", self.populate_exp_subsub)
        
        ttk.Label(center_frame, text="Sub-Subcategory:").grid(row=3, column=0, sticky="w", padx=5)
        self.exp_subsub = ttk.Combobox(center_frame, state="readonly")
        self.exp_subsub.grid(row=3, column=1, sticky="ew", padx=5)
        
        self.exp_amt_frame = ttk.Frame(center_frame)
        self.exp_amt_frame.grid(row=4, column=0, columnspan=2, pady=5)
        ttk.Label(self.exp_amt_frame, text="Amount:").pack(side="left")
        self.exp_amt = ttk.Entry(self.exp_amt_frame, width=10)
        self.exp_amt.pack(side="left", padx=5)
        
        self.exp_rate_frame = ttk.Frame(center_frame)
        self.exp_rate_frame.grid(row=5, column=0, columnspan=2, pady=5)
        self.lbl_exp_rate = ttk.Label(self.exp_rate_frame, text="Rate (1 EUR = ? Tk):")
        self.lbl_exp_rate.pack(side="left")
        self.exp_rate = ttk.Entry(self.exp_rate_frame, width=10)
        self.exp_rate.insert(0, str(int(self.dm.DEFAULT_RATE))) # Show 100
        self.exp_rate.pack(side="left", padx=5)
        
        ttk.Label(center_frame, text="Date:").grid(row=7, column=0, sticky="w", padx=5)
        self.exp_date = ttk.Entry(center_frame)
        self.exp_date.insert(0, today)
        self.exp_date.grid(row=7, column=1, sticky="ew", padx=5)
        
        ttk.Button(center_frame, text="Save Expense", command=self.add_expense_action).grid(row=8, column=0, columnspan=2, pady=10)

        # Right: Investment
        right_frame = ttk.LabelFrame(mid_frame, text="Investment / Return")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=5)
        
        self.inv_type = tk.StringVar(value="Investment")
        ttk.Radiobutton(right_frame, text="Add Investment", variable=self.inv_type, value="Investment", command=self.toggle_inv_fields).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(right_frame, text="Add Return", variable=self.inv_type, value="Return", command=self.toggle_inv_fields).grid(row=0, column=1, sticky="w")
        
        ttk.Label(right_frame, text="Category:").grid(row=1, column=0, sticky="w", padx=5)
        self.inv_cat = ttk.Combobox(right_frame, values=["Karje hasana", "Stocks", "Property", "Business", "Other"])
        self.inv_cat.current(0)
        self.inv_cat.grid(row=1, column=1, sticky="ew", padx=5)
        self.inv_cat.bind("<<ComboboxSelected>>", self.toggle_kh_fields)
        
        self.kh_name_frame = ttk.Frame(right_frame)
        ttk.Label(self.kh_name_frame, text="Name:").grid(row=0, column=0)
        self.kh_name = ttk.Entry(self.kh_name_frame, width=15)
        self.kh_name.grid(row=0, column=1)
        
        self.kh_addr_frame = ttk.Frame(right_frame)
        ttk.Label(self.kh_addr_frame, text="Address:").grid(row=0, column=0)
        self.kh_addr = ttk.Entry(self.kh_addr_frame, width=15)
        self.kh_addr.grid(row=0, column=1)
        
        ttk.Label(right_frame, text="Amount (EUR):").grid(row=4, column=0, sticky="w", padx=5)
        self.inv_amt = ttk.Entry(right_frame)
        self.inv_amt.grid(row=4, column=1, padx=5)
        
        ttk.Label(right_frame, text="Date:").grid(row=5, column=0, sticky="w", padx=5)
        self.inv_date = ttk.Entry(right_frame)
        self.inv_date.insert(0, today)
        self.inv_date.grid(row=5, column=1, padx=5)
        
        ttk.Label(right_frame, text="Description:").grid(row=6, column=0, sticky="nw", padx=5)
        self.inv_desc = tk.Text(right_frame, height=3, width=20)
        self.inv_desc.grid(row=6, column=1, padx=5)
        
        ttk.Button(right_frame, text="Save Transaction", command=self.add_investment_action).grid(row=7, column=0, columnspan=2, pady=10)
        
        # Initial UI Updates
        self.populate_exp_cats()
        self.toggle_kh_fields()
        self.toggle_inv_fields()

        mid_frame.columnconfigure(0, weight=1)
        mid_frame.columnconfigure(1, weight=1)
        mid_frame.columnconfigure(2, weight=1)
        mid_frame.rowconfigure(0, weight=1)

        # --- Bottom Section: Summary ---
        bot_frame = ttk.LabelFrame(self.tab1, text="Financial Summary")
        bot_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # --- NEW: Summary Year Filter Control ---
        sum_ctrl_frame = ttk.Frame(bot_frame)
        sum_ctrl_frame.pack(side="left", padx=5, pady=5)
        ttk.Label(sum_ctrl_frame, text="Year:").pack(side="left")
        self.summary_year_filter = ttk.Combobox(sum_ctrl_frame, values=["All"] + list(range(2020, 2030)), width=6, state="readonly")
        self.summary_year_filter.current(0)
        self.summary_year_filter.pack(side="left", padx=5)
        # Bind change to update summary immediately
        self.summary_year_filter.bind("<<ComboboxSelected>>", lambda e: self.update_summary())
        
        # Apply style for smaller font
        self.summary_tree = ttk.Treeview(bot_frame, style="Summary.Treeview", show="headings")
        self.summary_tree.pack(fill="both", expand=True)

    # --- Tab 1 Logic Helpers ---
    def update_initial_bal(self):
        try:
            val = float(self.init_bal_entry.get())
            self.dm.set_initial_balance(val)
            self.update_summary()
            self.refresh_all_tabs()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount")

    def add_bd_deposit_action(self):
        try:
            amt_tk = float(self.bd_deposit_amt.get())
            rate = float(self.bd_deposit_rate.get())
            
            self.dm.add_bd_deposit(amt_tk)
            self.update_summary()
            self.refresh_all_tabs()
            self.bd_deposit_amt.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid inputs")

    def add_income_action(self):
        source = self.inc_src.get()
        amt = self.inc_amt.get()
        date = self.inc_date.get()
        if not amt or not date: return messagebox.showerror("Error", "Missing Info")
        self.dm.add_income(source, amt, date)
        self.update_summary()
        self.refresh_all_tabs()

    def open_category_manager(self):
        win = tk.Toplevel(self.root)
        win.title("Category Manager")
        win.geometry("500x400")
        
        region = self.cat_region.get()
        cat_data = self.dm.get_categories(region).copy()
        
        tree = ttk.Treeview(win)
        tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        def populate_tree(parent, d):
            if not isinstance(d, dict): return
            for k, v in sorted(d.items()):
                node = tree.insert(parent, "end", text=k, values=(k,))
                populate_tree(node, v)
        
        def refresh():
            tree.delete(*tree.get_children())
            populate_tree("", cat_data)
            
        refresh()
        
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        def on_add():
            sel = tree.focus()
            name = simpledialog.askstring("Add", "Name:")
            if not name: return
            
            if not sel:
                cat_data[name] = {}
            else:
                path = []
                curr = sel
                while curr:
                    path.insert(0, tree.item(curr, "values")[0])
                    curr = tree.parent(curr)
                
                d_target = cat_data
                for p in path:
                    if p in d_target: d_target = d_target[p]
                d_target[name] = {}
            refresh()

        def on_edit():
            sel = tree.focus()
            if not sel: return
            old_name = tree.item(sel, "values")[0]
            new_name = simpledialog.askstring("Edit", "New name:", initialvalue=old_name)
            if not new_name: return
            
            path = []
            curr = sel
            while curr:
                path.insert(0, tree.item(curr, "values")[0])
                curr = tree.parent(curr)
            
            d_target = cat_data
            for p in path[:-1]:
                if p in d_target: d_target = d_target[p]
            
            d_target[new_name] = d_target.pop(old_name)
            refresh()

        def on_delete():
            sel = tree.focus()
            if not sel: return
            name = tree.item(sel, "values")[0]
            if not messagebox.askyesno("Confirm", f"Delete {name}?"): return
            
            path = []
            curr = sel
            while curr:
                path.insert(0, tree.item(curr, "values")[0])
                curr = tree.parent(curr)
                
            d_target = cat_data
            for p in path[:-1]:
                if p in d_target: d_target = d_target[p]
            
            del d_target[path[-1]]
            refresh()

        def on_save():
            self.dm.update_category_structure(region, cat_data)
            self.populate_exp_cats()
            messagebox.showinfo("Success", "Categories Saved!")
            win.destroy()

        ttk.Button(btn_frame, text="Add Sub", command=on_add).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Edit Name", command=on_edit).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Delete", command=on_delete).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Save & Close", command=on_save).pack(side="right", padx=2)

    def populate_exp_cats(self, event=None):
        region = self.exp_region.get()
        cats = list(self.dm.get_categories(region).keys())
        self.exp_cat['values'] = cats
        if cats: self.exp_cat.current(0)
        self.populate_exp_sub()
        
        if region == "BD":
            self.exp_rate_frame.grid(row=5, column=0, columnspan=2, pady=5, sticky="w")
            self.lbl_exp_rate.config(text="Rate (1 EUR = ? Tk):")
            self.exp_rate.config(state="normal")
            self.exp_rate.delete(0, tk.END)
            self.exp_rate.insert(0, str(int(self.dm.DEFAULT_RATE)))
            self.exp_amt_frame.children['!label'].config(text="Amount (BD Tk):")
        else:
            self.exp_rate_frame.grid_forget()
            self.exp_amt_frame.children['!label'].config(text="Amount (EUR):")

    def populate_exp_sub(self, event=None):
        region = self.exp_region.get()
        cat = self.exp_cat.get()
        if cat:
            subs = list(self.dm.get_categories(region).get(cat, {}).keys())
            self.exp_sub['values'] = subs
            if subs: self.exp_sub.current(0)
            else: self.exp_sub.set('')
        self.populate_exp_subsub()
        
        if region == "BD":
            self.exp_rate.config(state="normal")

    def populate_exp_subsub(self, event=None):
        region = self.exp_region.get()
        cat = self.exp_cat.get()
        sub = self.exp_sub.get()
        if cat and sub:
            subsubs = list(self.dm.get_categories(region).get(cat, {}).get(sub, {}).keys())
            self.exp_subsub['values'] = subsubs
            if subsubs: self.exp_subsub.current(0)
            else: self.exp_subsub.set('')

    def add_expense_action(self):
        region = self.exp_region.get()
        cat = self.exp_cat.get()
        sub = self.exp_sub.get()
        subsub = self.exp_subsub.get()
        amt = self.exp_amt.get()
        rate = self.exp_rate.get()
        date = self.exp_date.get()
        
        if not all([cat, amt, date]): return messagebox.showerror("Error", "Missing fields")
        if region == "BD" and not rate: 
            rate = 0 
            
        self.dm.add_expense(region, cat, sub, subsub, amt, rate, date)
        self.update_summary()
        self.refresh_all_tabs()

    def toggle_kh_fields(self, event=None):
        cat = self.inv_cat.get()
        if cat == "Karje hasana":
            self.kh_name_frame.grid(row=2, column=0, columnspan=2, pady=2)
            self.kh_addr_frame.grid(row=3, column=0, columnspan=2, pady=2)
        else:
            self.kh_name_frame.grid_forget()
            self.kh_addr_frame.grid_forget()

    def toggle_inv_fields(self):
        pass

    def add_investment_action(self):
        itype = self.inv_type.get()
        cat = self.inv_cat.get()
        amt = self.inv_amt.get()
        date = self.inv_date.get()
        desc = self.inv_desc.get("1.0", tk.END).strip()
        
        name = self.kh_name.get() if cat == "Karje hasana" else None
        addr = self.kh_addr.get() if cat == "Karje hasana" else None
        
        if not amt or not date: return messagebox.showerror("Error", "Missing Amount/Date")
        
        self.dm.add_investment(itype, cat, amt, date, desc, name, addr)
        self.update_summary()
        self.refresh_all_tabs()

    def update_summary(self):
        # 1. Get Filter
        try:
            year_val = self.summary_year_filter.get()
        except:
            year_val = "All"

        # 2. Prepare Dataframes (Load all, then filter)
        inc_df = pd.DataFrame(self.dm.data["income"])
        exp_df = pd.DataFrame(self.dm.data["expenses"])
        inv_df = pd.DataFrame(self.dm.data["investments"])
        
        if not inc_df.empty:
            inc_df["month_dt"] = pd.to_datetime(inc_df["date"])
            inc_df["month"] = inc_df["month_dt"].dt.to_period("M")
            inc_df["year"] = inc_df["month_dt"].dt.year
            
        if not exp_df.empty:
            exp_df["month_dt"] = pd.to_datetime(exp_df["date"])
            exp_df["month"] = exp_df["month_dt"].dt.to_period("M")
            exp_df["year"] = exp_df["month_dt"].dt.year
            exp_df["amount_eur"] = pd.to_numeric(exp_df["amount_eur"], errors='coerce').fillna(0)
            
        if not inv_df.empty:
            inv_df["month_dt"] = pd.to_datetime(inv_df["date"])
            inv_df["month"] = inv_df["month_dt"].dt.to_period("M")
            inv_df["year"] = inv_df["month_dt"].dt.year

        # 3. Apply Year Filter
        if year_val != "All":
            target_year = int(year_val)
            if not inc_df.empty: inc_df = inc_df[inc_df["year"] == target_year]
            if not exp_df.empty: exp_df = exp_df[exp_df["year"] == target_year]
            if not inv_df.empty: inv_df = inv_df[inv_df["year"] == target_year]

        # 4. Group Data
        inc_grp = inc_df.groupby("month")["amount"].sum().reset_index() if not inc_df.empty else pd.DataFrame(columns=["month", "amount"])
        
        exp_grp_eur = exp_df[exp_df["region"] == "GER"].groupby("month")["amount_eur"].sum().reset_index() if not exp_df.empty else pd.DataFrame(columns=["month", "amount_eur"])
        exp_grp_bd_local = exp_df[exp_df["region"] == "BD"].groupby("month")["amount_local"].sum().reset_index() if not exp_df.empty else pd.DataFrame(columns=["month", "amount_local"])
        # Note: Recalculate BD EUR using filtered DF
        if not exp_df.empty:
            exp_grp_bd_eur = exp_df[exp_df["region"] == "BD"].groupby("month")["amount_local"].sum().reset_index()
            exp_grp_bd_eur["amount_eur"] = exp_grp_bd_eur["amount_local"] / self.dm.DEFAULT_RATE
        else:
            exp_grp_bd_eur = pd.DataFrame(columns=["month", "amount_eur"])
            
        inv_grp = inv_df[inv_df["type"] == "Investment"].groupby("month")["amount"].sum().reset_index() if not inv_df.empty else pd.DataFrame(columns=["month", "amount"])
        ret_grp = inv_df[inv_df["type"] == "Return"].groupby("month")["amount"].sum().reset_index() if not inv_df.empty else pd.DataFrame(columns=["month", "amount"])

        # 5. Populate Tree
        self.summary_tree.delete(*self.summary_tree.get_children())
        
        cols = ["Month", "Income", "GER Exp", "BD Exp", "Net Inv", "Balance"]
        self.summary_tree["columns"] = cols
        col_widths = [140, 100, 100, 100, 100, 100]
        for col, width in zip(cols, col_widths):
            self.summary_tree.heading(col, text=col)
            self.summary_tree.column(col, width=width, minwidth=width, anchor="center", stretch=False)
        
        totals = {k: 0.0 for k in cols[1:]}
        
        # Determine months from filtered data
        months = set()
        if not inc_grp.empty: months.update(inc_grp["month"].tolist())
        if not exp_grp_eur.empty: months.update(exp_grp_eur["month"].tolist())
        if not exp_grp_bd_local.empty: months.update(exp_grp_bd_local["month"].tolist())
        if not inv_grp.empty: months.update(inv_grp["month"].tolist())
        if not ret_grp.empty: months.update(ret_grp["month"].tolist())
        months = sorted(list(months))
        
        for m in months:
            inc = inc_grp[inc_grp["month"] == m]["amount"].sum() if not inc_grp.empty else 0
            ret = ret_grp[ret_grp["month"] == m]["amount"].sum() if not ret_grp.empty else 0
            exp_e = exp_grp_eur[exp_grp_eur["month"] == m]["amount_eur"].sum() if not exp_grp_eur.empty else 0
            exp_b_tk = exp_grp_bd_local[exp_grp_bd_local["month"] == m]["amount_local"].sum() if not exp_grp_bd_local.empty else 0
            exp_b_eur = exp_grp_bd_eur[exp_grp_bd_eur["month"] == m]["amount_eur"].sum() if not exp_grp_bd_eur.empty else 0
            inv = inv_grp[inv_grp["month"] == m]["amount"].sum() if not inv_grp.empty else 0
            
            net_inv = ret - inv
            bal = inc - exp_e - exp_b_eur + net_inv
            
            month_str = m.strftime('%B %Y') if hasattr(m, 'strftime') else str(m)
            self.summary_tree.insert("", "end", values=(month_str, f"{inc:.2f}", f"{exp_e:.2f}", f"{exp_b_tk:.2f}", f"{net_inv:.2f}", f"{bal:.2f}"))
            
            totals["Income"] += inc
            totals["GER Exp"] += exp_e
            totals["BD Exp"] += exp_b_tk
            totals["Net Inv"] += net_inv
            totals["Balance"] += bal
            
        # Total Row
        self.summary_tree.insert("", "end", values=("TOTAL", *[f"{v:.2f}" for v in totals.values()]), tags=("total",))
        
        # Average Row
        count = len(months)
        if count > 0:
            avgs = {k: v/count for k, v in totals.items()}
            self.summary_tree.insert("", "end", values=("AVERAGE", *[f"{v:.2f}" for v in avgs.values()]), tags=("total",))
            
        self.summary_tree.tag_configure("total", background="#e0e0e0", font=("Arial", 10, "bold"))
        
        # Update Top Labels
        init_bal = float(self.init_bal_entry.get())
        net_flow = totals["Balance"]
        total_disp = init_bal + net_flow
        
        self.lbl_total_bal_top.config(text=f"Total Balance: {total_disp:.2f} EUR")
        
        bd_tk = self.dm.data["current_balance_bd"]
        rate = float(self.bd_deposit_rate.get())
        bd_eur = bd_tk / rate if rate > 0 else 0
        self.lbl_bd_bal_top.config(text=f"BD Balance: {bd_tk:.2f} Tk ({bd_eur:.2f} EUR)")

    # ==========================================
    # TAB 2: DATABASE
    # ==========================================
    def setup_tab2(self):
        # Top Control Frame (Year and Region)
        ctrl_frame = ttk.Frame(self.tab2)
        ctrl_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(ctrl_frame, text="Year:").pack(side="left")
        self.db_year = ttk.Combobox(ctrl_frame, values=["All"] + list(range(2020, 2030)), width=5, state="readonly")
        self.db_year.current(0)
        self.db_year.pack(side="left", padx=5)
        
        ttk.Label(ctrl_frame, text="Region:").pack(side="left", padx=10)
        self.db_filter = ttk.Combobox(ctrl_frame, values=["All", "GER", "BD"], state="readonly")
        self.db_filter.current(0)
        self.db_filter.pack(side="left", padx=5)
        
        ttk.Button(ctrl_frame, text="Generate Tables", command=self.generate_db_tables).pack(side="left", padx=20)
        
        # Middle Frame (Expense Tables)
        self.db_top_frame = ttk.LabelFrame(self.tab2, text="Expense Database")
        self.db_top_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.db_tabs_exp = ttk.Notebook(self.db_top_frame)
        self.db_tabs_exp.pack(fill="both", expand=True)
        
        self.db_tab1 = ttk.Frame(self.db_tabs_exp) 
        self.db_tab2 = ttk.Frame(self.db_tabs_exp) 
        self.db_tab3 = ttk.Frame(self.db_tabs_exp) 
        
        self.db_tabs_exp.add(self.db_tab1, text="Table 1")
        self.db_tabs_exp.add(self.db_tab2, text="Table 2")
        self.db_tabs_exp.add(self.db_tab3, text="Table 3")
        
        self.t1_container = ttk.Frame(self.db_tab1)
        self.t1_container.pack(fill="both", expand=True)
        self.t2_container = ttk.Frame(self.db_tab2)
        self.t2_container.pack(fill="both", expand=True)
        self.t3_container = ttk.Frame(self.db_tab3)
        self.t3_container.pack(fill="both", expand=True)

        # Bottom Frame (Investment Section)
        self.db_bot_frame = ttk.LabelFrame(self.tab2, text="Investment Database")
        self.db_bot_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.db_tabs_inv = ttk.Notebook(self.db_bot_frame)
        self.db_tabs_inv.pack(fill="both", expand=True)
        
        self.inv_tab_list = ttk.Frame(self.db_tabs_inv)
        self.inv_tab_ret = ttk.Frame(self.db_tabs_inv)
        self.inv_tab_kh = ttk.Frame(self.db_tabs_inv)
        self.inv_tab_pivot = ttk.Frame(self.db_tabs_inv)
        
        self.db_tabs_inv.add(self.inv_tab_list, text="Investments")
        self.db_tabs_inv.add(self.inv_tab_ret, text="Return")
        self.db_tabs_inv.add(self.inv_tab_kh, text="Karje Hasana")
        self.db_tabs_inv.add(self.inv_tab_pivot, text="Inv/Ret Pivot")
        
        self.setup_investment_section()

    def setup_investment_section(self):
        # Create Investment Trees
        self.tree_inv = ttk.Treeview(self.inv_tab_list, columns=("Month", "Category", "Amount", "Desc"), show="headings")
        self.tree_inv.pack(fill="both", expand=True)
        for c in self.tree_inv["columns"]: self.tree_inv.heading(c, text=c)
        
        self.tree_ret = ttk.Treeview(self.inv_tab_ret, columns=("Month", "Category", "Amount", "Desc"), show="headings")
        self.tree_ret.pack(fill="both", expand=True)
        for c in self.tree_ret["columns"]: self.tree_ret.heading(c, text=c)
        
        self.tree_kh = ttk.Treeview(self.inv_tab_kh, columns=("Date", "Name/Org", "Address", "Amount", "Return", "To Be Return"), show="headings")
        self.tree_kh.pack(fill="both", expand=True)
        for c in self.tree_kh["columns"]: self.tree_kh.heading(c, text=c)
        
        # --- Inv/Ret Pivot Controls and Table ---
        self.pivot_ctrl_frame = ttk.Frame(self.inv_tab_pivot)
        self.pivot_ctrl_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(self.pivot_ctrl_frame, text="Year:").pack(side="left")
        self.pivot_year = ttk.Combobox(self.pivot_ctrl_frame, values=["All"] + list(range(2020, 2030)), width=5, state="readonly")
        self.pivot_year.current(0)
        self.pivot_year.pack(side="left", padx=5)
        self.pivot_year.bind("<<ComboboxSelected>>", self.generate_db_tables)
        
        ttk.Label(self.pivot_ctrl_frame, text="Type:").pack(side="left", padx=10)
        self.pivot_filter = ttk.Combobox(self.pivot_ctrl_frame, values=["All", "Investment", "Return"], state="readonly")
        self.pivot_filter.current(0)
        self.pivot_filter.pack(side="left", padx=5)
        self.pivot_filter.bind("<<ComboboxSelected>>", self.generate_db_tables)
        
        self.tree_inv_pivot = ttk.Treeview(self.inv_tab_pivot, show="headings")
        self.tree_inv_pivot.pack(fill="both", expand=True)

    def generate_db_tables(self, event=None):
        # Clear Expense Tables
        for t in [self.t1_container, self.t2_container, self.t3_container]:
            for widget in t.winfo_children(): widget.destroy()
            
        # Clear Investment Lists
        if hasattr(self, 'tree_inv') and hasattr(self.tree_inv, 'delete'):
            self.tree_inv.delete(*self.tree_inv.get_children())
        if hasattr(self, 'tree_ret') and hasattr(self.tree_ret, 'delete'):
            self.tree_ret.delete(*self.tree_ret.get_children())
        if hasattr(self, 'tree_kh') and hasattr(self.tree_kh, 'delete'):
            self.tree_kh.delete(*self.tree_kh.get_children())
            
        # Clear Pivot Table
        if hasattr(self.tree_inv_pivot, 'delete'):
            self.tree_inv_pivot.delete(*self.tree_inv_pivot.get_children())
            
        # --- Generate Expense Tables ---
        year = self.db_year.get()
        filter_type = self.db_filter.get()
        
        df = pd.DataFrame(self.dm.data["expenses"])
        if df.empty: 
            ttk.Label(self.t1_container, text="No Data").pack()
            return
        
        df["month"] = pd.to_datetime(df["date"]).dt.to_period("M")
        df["year"] = pd.to_datetime(df["date"]).dt.year
        df = df.sort_values("month")
        
        if year != "All":
            df = df[df["year"] == int(year)]
            
        if filter_type in ["GER", "BD"]:
            df = df[df["region"] == filter_type]
        
        if df.empty:
            ttk.Label(self.t1_container, text="No Data for Filter").pack()
            return

        def make_table(parent, df_pivot):
            frame = ttk.Frame(parent)
            frame.pack(fill="both", expand=True)
            
            canvas = tk.Canvas(frame)
            scrollbar_v = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            scrollbar_h = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar_v.pack(side="right", fill="y")
            scrollbar_h.pack(side="bottom", fill="x")

            tree = ttk.Treeview(scrollable_frame, show="headings")
            tree.pack(fill="both", expand=True)
            
            cols = list(df_pivot.columns)
            cols = sorted(cols)
            final_cols = ["Month"] + cols + ["Total"]
            
            tree["columns"] = final_cols
            tree.column("#0", width=0, stretch=0)
            for col in final_cols:
                tree.heading(col, text=col)
                tree.column(col, width=120, minwidth=120, anchor="e", stretch=False)
                
            for idx, row in df_pivot.iterrows():
                month_name = idx.strftime('%B %Y') if hasattr(idx, 'strftime') else str(idx)
                vals = [month_name] + [f"{row[c]:.2f}" if pd.notnull(row[c]) else "0.00" for c in cols] + [f"{row.sum():.2f}"]
                tree.insert("", "end", values=vals)
            
            totals = [f"{df_pivot[c].sum():.2f}" for c in cols]
            tree.insert("", "end", values=("Total",) + tuple(totals) + (f"{df_pivot.sum().sum():.2f}",), tags=("total",))
            tree.tag_configure("total", background="#ccc")

        val_col = "amount_local" if filter_type == "BD" else "amount_eur"
        unit = " (Tk)" if filter_type == "BD" else " (Eur)"

        t1 = df.pivot_table(index="month", columns="category", values=val_col, aggfunc="sum", fill_value=0)
        make_table(self.t1_container, t1)
        
        t2_ctrl = ttk.Frame(self.t2_container)
        t2_ctrl.pack(fill="x")
        sel_cat = ttk.Combobox(t2_ctrl, values=list(df["category"].unique()), state="readonly")
        sel_cat.pack(side="left", padx=5)
        if not df.empty: sel_cat.current(0)
        
        t2_tree_area = ttk.Frame(self.t2_container)
        t2_tree_area.pack(fill="both", expand=True)
        
        def update_t2(event):
            c = sel_cat.get()
            sub_df = df[df["category"] == c]
            if not sub_df.empty:
                t2 = sub_df.pivot_table(index="month", columns="subcategory", values=val_col, aggfunc="sum", fill_value=0)
                for w in t2_tree_area.winfo_children(): w.destroy()
                make_table(t2_tree_area, t2)
        
        sel_cat.bind("<<ComboboxSelected>>", update_t2)
        update_t2(None) 
        
        t3_ctrl = ttk.Frame(self.t3_container)
        t3_ctrl.pack(fill="x")
        sel_cat3 = ttk.Combobox(t3_ctrl, values=list(df["category"].unique()), state="readonly")
        sel_cat3.pack(side="left", padx=5)
        sel_sub3 = ttk.Combobox(t3_ctrl, state="readonly")
        sel_sub3.pack(side="left", padx=5)
        
        t3_tree_area = ttk.Frame(self.t3_container)
        t3_tree_area.pack(fill="both", expand=True)
        
        def update_cat3(event):
            c = sel_cat3.get()
            subs = df[df["category"] == c]["subcategory"].unique().tolist()
            sel_sub3['values'] = subs
            if subs: sel_sub3.current(0)
            update_t3(None)
                
        def update_t3(event):
            c = sel_cat3.get()
            s = sel_sub3.get()
            sub_df = df[(df["category"] == c) & (df["subcategory"] == s)]
            if not sub_df.empty:
                t3 = sub_df.pivot_table(index="month", columns="subsubcategory", values=val_col, aggfunc="sum", fill_value=0)
                for w in t3_tree_area.winfo_children(): w.destroy()
                make_table(t3_tree_area, t3)
        
        sel_cat3.bind("<<ComboboxSelected>>", update_cat3)
        sel_sub3.bind("<<ComboboxSelected>>", update_t3)
        if not df.empty:
            sel_cat3.current(0)
            update_cat3(None)

        # --- Generate Investment Lists ---
        inv_df = pd.DataFrame(self.dm.data["investments"])
        if not inv_df.empty:
            inv_df["month"] = pd.to_datetime(inv_df["date"]).dt.to_period("M")
            
            df_inv = inv_df[inv_df["type"] == "Investment"]
            self.tree_inv.delete(*self.tree_inv.get_children())
            for _, row in df_inv.iterrows():
                self.tree_inv.insert("", "end", values=(row["month"], row["category"], row["amount"], row["description"]))
                
            df_ret = inv_df[inv_df["type"] == "Return"]
            self.tree_ret.delete(*self.tree_ret.get_children())
            for _, row in df_ret.iterrows():
                self.tree_ret.insert("", "end", values=(row["month"], row["category"], row["amount"], row["description"]))
                
            kh_data = self.dm.get_kh_details()
            self.tree_kh.delete(*self.tree_kh.get_children())
            for item in kh_data:
                self.tree_kh.insert("", "end", values=(item["Date"], item["Name/Org"], item["Address"], item["Amount (Given)"], item["Return"], item["To Be Return"]))
            
            # --- Generate Pivot Table ---
            self.generate_pivot_table()

    def generate_pivot_table(self, event=None):
        year = self.pivot_year.get()
        filter_piv = self.pivot_filter.get()
        
        inv_df = pd.DataFrame(self.dm.data["investments"])
        
        # Clear Pivot Tree Safely
        if hasattr(self.tree_inv_pivot, 'delete'):
            self.tree_inv_pivot.delete(*self.tree_inv_pivot.get_children())
        
        if not inv_df.empty:
            inv_df["month"] = pd.to_datetime(inv_df["date"]).dt.to_period("M")
            inv_df["year"] = pd.to_datetime(inv_df["date"]).dt.year
            
            # Apply Year Filter
            if year != "All":
                inv_df = inv_df[inv_df["year"] == int(year)]
                
            # Apply Type Filter (Investment/Return/All)
            if filter_piv != "All":
                inv_df = inv_df[inv_df["type"] == filter_piv]
            
            if not inv_df.empty:
                pivot = inv_df.pivot_table(index="month", columns="category", values="amount", aggfunc="sum", fill_value=0)
                
                cols_p = list(pivot.columns)
                cols_p = sorted(cols_p)
                cols_final = ["Month"] + cols_p + ["Total"]
                
                self.tree_inv_pivot["columns"] = cols_final
                self.tree_inv_pivot.column("#0", width=0)
                for c in cols_final:
                    self.tree_inv_pivot.heading(c, text=c)
                    self.tree_inv_pivot.column(c, width=120, minwidth=120, anchor="e", stretch=False)
                
                for idx, row in pivot.iterrows():
                    month_p = idx.strftime('%B %Y') if hasattr(idx, 'strftime') else str(idx)
                    # Calculate row total for display
                    row_sum = row.sum()
                    vals = [month_p] + [f"{v:.2f}" for v in row.values] + [f"{row_sum:.2f}"]
                    self.tree_inv_pivot.insert("", "end", values=vals)
            else:
                # Insert placeholder if no data
                self.tree_inv_pivot.insert("", "end", values=("No Data for Filter", ""))

    # ==========================================
    # TAB 3: ANALYSIS
    # ==========================================
    def setup_tab3(self):
        top_frame = ttk.LabelFrame(self.tab3, text="Income vs Expense Analysis")
        top_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctrl_top = ttk.Frame(top_frame)
        ctrl_top.pack(fill="x")
        ttk.Label(ctrl_top, text="Select Year:").pack(side="left", padx=5)
        self.ana_year = ttk.Combobox(ctrl_top, values=["All"] + list(range(2020, 2030)), state="readonly")
        self.ana_year.current(0)
        self.ana_year.pack(side="left", padx=5)
        ttk.Button(ctrl_top, text="Plot Trend", command=self.plot_trend).pack(side="left", padx=10)
        
        self.fig_top = plt.Figure(figsize=(5, 3), dpi=100)
        self.ax_top = self.fig_top.add_subplot(111)
        self.canvas_top = FigureCanvasTkAgg(self.fig_top, top_frame)
        self.canvas_top.get_tk_widget().pack(fill="both", expand=True)
        
        bot_frame = ttk.LabelFrame(self.tab3, text="Detailed Pie Chart Analysis")
        bot_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctrl_bot = ttk.Frame(bot_frame)
        ctrl_bot.pack(fill="x")
        
        ttk.Label(ctrl_bot, text="Year:").pack(side="left", padx=5)
        self.pie_year = ttk.Combobox(ctrl_bot, values=["All"] + list(range(2020, 2030)), state="readonly")
        self.pie_year.current(0)
        self.pie_year.pack(side="left", padx=5)
        
        ttk.Label(ctrl_bot, text="Type:").pack(side="left", padx=5)
        self.pie_type = ttk.Combobox(ctrl_bot, values=["GER", "BD", "All", "Investment"], state="readonly")
        self.pie_type.current(0)
        self.pie_type.pack(side="left", padx=5)
        self.pie_type.bind("<<ComboboxSelected>>", self.toggle_pie_level)
        
        self.pie_level_frame = ttk.Frame(ctrl_bot)
        self.pie_level_frame.pack(side="left", padx=5)
        ttk.Label(self.pie_level_frame, text="Level:").pack(side="left")
        self.pie_level = ttk.Combobox(self.pie_level_frame, values=["Category", "Subcategory", "SubSubcategory"], state="readonly")
        self.pie_level.current(0)
        self.pie_level.pack(side="left", padx=5)
        
        ttk.Button(ctrl_bot, text="Plot Pie", command=self.plot_pie).pack(side="left", padx=10)
        
        self.fig_bot = plt.Figure(figsize=(5, 4), dpi=100)
        self.ax_bot = self.fig_bot.add_subplot(111)
        self.canvas_bot = FigureCanvasTkAgg(self.fig_bot, bot_frame)
        self.canvas_bot.get_tk_widget().pack(fill="both", expand=True)

    def toggle_pie_level(self, event=None):
        if self.pie_type.get() == "Investment":
            self.pie_level_frame.pack_forget()
        else:
            self.pie_level_frame.pack(side="left", padx=5)

    def plot_trend(self):
        year = self.ana_year.get()
        # Use the helper function in DataManager (Note: this returns DataFrames, not aggregated)
        inc_df, exp_eur, _, exp_bd_eur, inv_df, ret_df = self.dm.get_summary_df()
        
        df = pd.DataFrame({"Income": inc_df.set_index("month")["amount"]})
        df = df.join(exp_eur.set_index("month")["amount_eur"].rename("GER_Exp"))
        df = df.join(exp_bd_eur.set_index("month")["amount_eur"].rename("BD_Exp"))
        df = df.join(inv_df.set_index("month")["amount"].rename("Investment"))
        df = df.join(ret_df.set_index("month")["amount"].rename("Return"))
        
        if year != "All":
            # Note: We filter the index because the helper returns DataFrames that might not be filtered yet.
            # But actually, the helper returns DataFrames based on the internal data.
            # So we filter here to respect the UI Year.
            df = df[df.index.year == int(year)]
            
        self.ax_top.clear()
        if not df.empty:
            df.plot(kind="bar", ax=self.ax_top)
            self.ax_top.set_title(f"Income vs Expense ({year})")
            self.ax_top.set_ylabel("Amount (EUR)")
            self.ax_top.legend()
        else:
            self.ax_top.text(0.5, 0.5, "No Data", ha="center")
        
        self.canvas_top.draw()

    def plot_pie(self):
        year = self.pie_year.get()
        ptype = self.pie_type.get()
        level = self.pie_level.get().lower()
        
        self.ax_bot.clear()
        
        if ptype == "Investment":
            df = pd.DataFrame(self.dm.data["investments"])
            if df.empty: return
            df["year"] = pd.to_datetime(df["date"]).dt.year
            if year != "All": df = df[df["year"] == int(year)]
            
            if df.empty:
                self.canvas_bot.draw()
                return
            
            counts = df[df["type"] == "Investment"].groupby("category")["amount"].sum()
            counts.plot(kind="pie", ax=self.ax_bot, autopct='%1.1f%%')
            self.ax_bot.set_ylabel("")
            self.ax_bot.set_title("Investment Distribution")
            
        else:
            df = pd.DataFrame(self.dm.data["expenses"])
            if df.empty: return
            df["year"] = pd.to_datetime(df["date"]).dt.year
            if year != "All": df = df[df["year"] == int(year)]
            
            if ptype in ["GER", "BD"]:
                df = df[df["region"] == ptype]
            
            if df.empty:
                self.canvas_bot.draw()
                return
            
            col = "category"
            if "sub" in level: col = "subcategory"
            if "subsub" in level: col = "subsubcategory"
            
            counts = df.groupby(col)["amount_eur"].sum()
            counts.plot(kind="pie", ax=self.ax_bot, autopct='%1.1f%%')
            self.ax_bot.set_ylabel("")
            self.ax_bot.set_title(f"Expense Breakdown: {level} ({ptype})")
            
        self.canvas_bot.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()
