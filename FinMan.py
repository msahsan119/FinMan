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

        # ==========================================
    # UPDATED Data Manager Methods (Flat File Structure)
    # ==========================================

    def __init__(self):
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
        
        # Start with defaults
        self.data = self.defaults.copy()
        
        # Load existing data from current directory
        self.load_data()
    
    def migrate_old_file(self, filepath):
        try:
            if not os.path.exists(filepath):
                return False, "File not found."
    
            extension = os.path.splitext(filepath)[1].lower()
            count = 0
    
            if extension == ".json":
                with open(filepath, 'r') as f:
                    old_data = json.load(f)
    
                # Merge Income
                old_income = old_data.get("income", [])
                self.data["income"].extend(old_income)
                count += len(old_income)
    
                # Merge Expenses
                old_expenses = old_data.get("expenses", [])
                self.data["expenses"].extend(old_expenses)
                count += len(old_expenses)
    
                # Merge Investments
                old_investments = old_data.get("investments", [])
                self.data["investments"].extend(old_investments)
                count += len(old_investments)
    
                # Merge Categories (Update existing structure)
                if "categories" in old_data:
                    for region in old_data["categories"]:
                        if region not in self.data["categories"]:
                            self.data["categories"][region] = {}
                        self.data["categories"][region].update(old_data["categories"][region])
                
                # Update Initial Balance if present
                if "initial_balance_eur" in old_data:
                    self.data["initial_balance_eur"] = old_data["initial_balance_eur"]
                
                # --- ADD THIS: Update Current Balances ---
                if "current_balance_bd" in old_data:
                    self.data["current_balance_bd"] = old_data["current_balance_bd"]
                if "current_balance_eur" in old_data:
                    self.data["current_balance_eur"] = old_data["current_balance_eur"]
                # ---------------------------------------
    
            elif extension == ".csv":
                df = pd.read_csv(filepath)
    
                # Process Expenses
                exp_df = df[df["Record Type"] == "Expense"]
                for _, row in exp_df.iterrows():
                    self.data["expenses"].append({
                        "region": row["Region"],
                        "category": row["Category"],
                        "subcategory": row["Subcategory"],
                        "subsubcategory": row["Sub Subcategory"],
                        "amount_local": row["Amount Local"],
                        "rate": row["Rate"],
                        "amount_eur": row["Amount EUR"],
                        "date": row["Date"]
                    })
                count += len(exp_df)
    
                # Process Income
                inc_df = df[df["Record Type"] == "Income"]
                for _, row in inc_df.iterrows():
                    self.data["income"].append({
                        "source": row["Source"],
                        "amount": row["Amount EUR"],
                        "date": row["Date"],
                        "type": "EUR"
                    })
                count += len(inc_df)
    
                # Process Investments
                inv_df = df[df["Record Type"] == "Investment"]
                for _, row in inv_df.iterrows():
                    self.data["investments"].append({
                        "type": row["Type"],
                        "category": row["Category"],
                        "amount": row["Amount EUR"],
                        "date": row["Date"],
                        "description": row["Description"],
                        "name": row["Name"] if pd.notnull(row["Name"]) else "",
                        "address": row["Address"] if pd.notnull(row["Address"]) else ""
                    })
                count += len(inv_df)
    
            # After merging data into memory, call save_data() to split by year
            self.save_data()
            return True, f"Successfully migrated {count} records. Data split by year and saved."
    
        except Exception as e:
            print(f"Migration error: {e}")
            return False, f"Error during migration: {e}"
    
   
    
    def import_old_data_action(self):
        # Ask user to select the file
        file_path = filedialog.askopenfilename(
            title="Select old finance data file",
            filetypes=[("Data Files", "*.json *.csv"), ("JSON Files", "*.json"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if file_path:
            confirm = messagebox.askyesno("Confirm", "This will merge data from the old file into your current data and re-save it by year. Continue?")
            if confirm:
                success, msg = self.dm.migrate_old_file(file_path)
                if success:
                    messagebox.showinfo("Success", msg)
                    # Refresh the UI to show new data
                    self.update_summary()
                    self.refresh_all_tabs()
                else:
                    messagebox.showerror("Error", msg)
    
    def load_data(self):
        """Loads data from finance_data_YEAR.json or legacy files like finance_data_all.json"""
        # Reset to defaults
        self.data = self.defaults.copy()
        
        # Find files matching the pattern finance_data*.json
        files = []
        for f in os.listdir('.'):
            if f.startswith("finance_data") and f.endswith(".json"):
                files.append(f)
        
        # Sort files so we load chronologically
        files.sort()
        
        loaded_years = []
    
        for filename in files:
            try:
                # Attempt to parse the year from the filename
                if "_" in filename:
                    parts = filename.split('_')
                    last_part = parts[-1].replace('.json', '')
                    
                    if last_part.isdigit():
                        loaded_years.append(int(last_part))
                
                # Load the JSON content
                with open(filename, 'r') as f:
                    loaded_year_data = json.load(f)
    
                # Merge Categories
                if "categories" in loaded_year_data:
                    for region in loaded_year_data["categories"]:
                        if region not in self.data["categories"]:
                            self.data["categories"][region] = {}
                        self.data["categories"][region].update(loaded_year_data["categories"][region])
    
                # Extend Lists
                if "income" in loaded_year_data:
                    self.data["income"].extend(loaded_year_data["income"])
                if "expenses" in loaded_year_data:
                    self.data["expenses"].extend(loaded_year_data["expenses"])
                if "investments" in loaded_year_data:
                    self.data["investments"].extend(loaded_year_data["investments"])
                
                # --- Load Balances ---
                # We overwrite these. Since files are sorted, the last file (latest year)
                # will contain the most up-to-date balance.
                if "initial_balance_eur" in loaded_year_data:
                    self.data["initial_balance_eur"] = loaded_year_data["initial_balance_eur"]
                
                if "current_balance_bd" in loaded_year_data:
                    self.data["current_balance_bd"] = loaded_year_data["current_balance_bd"]
                
                if "current_balance_eur" in loaded_year_data:
                    self.data["current_balance_eur"] = loaded_year_data["current_balance_eur"]
                
            except Exception as e:
                print(f"Skipping file {filename} due to error: {e}")
   

    def save_data(self):
        """Saves data to finance_data_YEAR.json and finance_data_YEAR.csv in current directory"""
        # 1. Determine which years have data
        years = set()
        
        # Helper to extract year safely
        def get_year(date_str):
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").year
            except:
                return None

        for item in self.data["income"]:
            y = get_year(item["date"])
            if y: years.add(y)
            
        for item in self.data["expenses"]:
            y = get_year(item["date"])
            if y: years.add(y)
            
        for item in self.data["investments"]:
            y = get_year(item["date"])
            if y: years.add(y)
            
        # If no transactions exist yet, default to current year
        if not years:
            years.add(datetime.now().year)

        # 2. Loop through years and save
        for year in years:
            # Construct filenames: finance_data_2024.json
            json_filename = f"finance_data_{year}.json"
            csv_filename = f"finance_data_{year}.csv"

            # --- Filter Data for this Year ---
            year_income = [i for i in self.data["income"] if get_year(i["date"]) == year]
            year_expenses = [e for e in self.data["expenses"] if get_year(e["date"]) == year]
            year_investments = [inv for inv in self.data["investments"] if get_year(inv["date"]) == year]

            # --- Prepare JSON Content ---
            year_json_content = {
                "initial_balance_eur": self.data["initial_balance_eur"],
                "current_balance_bd": self.data["current_balance_bd"], # Save BD Balance
                "current_balance_eur": self.data["current_balance_eur"], # Save EUR Balance
                "categories": self.data["categories"], 
                "income": year_income,
                "expenses": year_expenses,
                "investments": year_investments,
                "conversion_rates": self.data.get("conversion_rates", {})
            }

            # --- Save JSON ---
            try:
                with open(json_filename, 'w') as f:
                    json.dump(year_json_content, f, indent=4, default=str)
            except Exception as e:
                print(f"Error saving JSON for year {year}: {e}")

            # --- Save CSV ---
            self._save_csv_content(csv_filename, year_income, year_expenses, year_investments)

    # Keep the helper method from the previous step
    def _save_csv_content(self, filepath, income_list, expense_list, investment_list):
        rows = []
        
        # 1. Process Income
        for item in income_list:
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
        for item in expense_list:
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
        for item in investment_list:
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
                "Type": item["type"], 
                "Description": item["description"],
                "Name": item["name"] if "name" in item else "",
                "Address": item["address"] if "address" in item else ""
            })
            
        df = pd.DataFrame(rows)
        
        try:
            df.to_csv(filepath, mode='w', index=False)
        except Exception as e:
            print(f"Error saving CSV: {e}")
            
    
        
    


    def load_data_csv_conditional(self):
        # FIX: Only load CSV if JSON does not exist.
        # This prevents the "Loop of Death" where CSV loads -> JSON saves -> CSV appends -> Restart repeats.
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
    
    def set_initial_balance(self, amount_eur):
        self.data["initial_balance_eur"] = float(amount_eur)
        self.save_data() 
        # Removed self.save_data_csv()
    
    def update_category_structure(self, region, new_structure):
        self.data["categories"][region] = new_structure
        self.save_data()
        # Removed self.save_data_csv()
    
    def add_income(self, source, amount, date, type="EUR"):
        entry = {"source": source, "amount": float(amount), "date": date, "type": type}
        self.data["income"].append(entry)
        self.data["current_balance_eur"] += float(amount)
        self.save_data()
        # Removed self.save_data_csv()
    
    def add_bd_deposit(self, amount_tk):
        self.data["current_balance_bd"] += amount_tk
        self.save_data()
        # Removed self.save_data_csv()
    
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
        # Removed self.save_data_csv()
    
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
        # Removed self.save_data_csv()
    
    def get_categories(self, region):
        return self.data["categories"].get(region, {})

   

    def get_summary_df(self):
        # Helper for Analysis tab
        inc_df = pd.DataFrame(self.data["income"])
        if not inc_df.empty:
            inc_df["month_dt"] = pd.to_datetime(inc_df["date"])
            inc_df["month"] = inc_df["month_dt"].dt.to_period("M")
            inc_df["year"] = inc_df["month_dt"].dt.year
            inc_grp = inc_df.groupby("month")["amount"].sum().reset_index()
        else:
            inc_grp = pd.DataFrame(columns=["month", "amount"])

        exp_df = pd.DataFrame(self.data["expenses"])
        if not exp_df.empty:
            exp_df["month_dt"] = pd.to_datetime(exp_df["date"])
            exp_df["month"] = exp_df["month_dt"].dt.to_period("M")
            exp_df["year"] = exp_df["month_dt"].dt.year
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
            inv_df["year"] = inv_df["month_dt"].dt.year
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
        
        # --- CHANGE THE LINE BELOW ---
        self.dm = DataManager() 
        
        style = ttk.Style()

        style.theme_use('clam')
        # ... (existing style configs) ...
    
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)
        
        self.tab1 = ttk.Frame(self.tabs)
        self.tab2 = ttk.Frame(self.tabs)
        self.tab3 = ttk.Frame(self.tabs)
        self.tab4 = ttk.Frame(self.tabs) # <--- NEW
    
        self.tabs.add(self.tab1, text="Input")
        self.tabs.add(self.tab4, text="Daily Trans") # <--- NEW
        self.tabs.add(self.tab2, text="Database")
        self.tabs.add(self.tab3, text="Analysis")
        
        
        # Bind tab change
        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        # Setup UI
        self.setup_tab1()
        self.setup_tab4() # <--- NEW
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
        elif selected_tab == 3: # <--- NEW (Index 3 is the 4th tab)
            self.update_daily_trans_view()

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
        
        # --- ADD BUTTON HERE ---
        ttk.Button(lbl_frame, text="Import Old Data (JSON/CSV)", command=self.import_old_data_action).pack(anchor="w", pady=(0, 5))
    
        ttk.Separator(lbl_frame, orient="horizontal").pack(fill="x", pady=5)

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
        self.summary_year_filter.bind("<<ComboboxSelected>>", lambda e: self.update_summary())
        
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
    
    def import_old_data_action(self):
        # Ask user to select the file
        file_path = filedialog.askopenfilename(
            title="Select old finance data file",
            filetypes=[("Data Files", "*.json *.csv"), ("JSON Files", "*.json"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if file_path:
            confirm = messagebox.askyesno("Confirm", "This will merge data from the old file into your current data and re-save it by year. Continue?")
            if confirm:
                success, msg = self.dm.migrate_old_file(file_path)
                if success:
                    messagebox.showinfo("Success", msg)
                    # Refresh the UI to show new data
                    self.update_summary()
                    self.refresh_all_tabs()
                else:
                    messagebox.showerror("Error", msg)

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
            exp_grp_eur = pd.DataFrame(columns=["month", "amount_eur"])
            exp_grp_bd_local = pd.DataFrame(columns=["month", "amount_local"])
            exp_grp_bd_eur = pd.DataFrame(columns=["month", "amount_eur"])
            
        inv_grp = inv_df[inv_df["type"] == "Investment"].groupby("month")["amount"].sum().reset_index() if not inv_df.empty else pd.DataFrame(columns=["month", "amount"])
        ret_grp = inv_df[inv_df["type"] == "Return"].groupby("month")["amount"].sum().reset_index() if not inv_df.empty else pd.DataFrame(columns=["month", "amount"])

        # 5. Populate Tree
        self.summary_tree.delete(*self.summary_tree.get_children())
        
        cols = ["Month", "Income", "GER Exp", "BD Exp", "Net Inv", "Balance"]
        self.summary_tree["columns"] = cols
        # FIX: Apply anchor='center' for all columns
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
        
        # FIX: Corrected Equation Logic
        # Net Inv should be "Investments - Returns".
        # We calculate net_inv as (Returns - Investments).
        # If Returns > Investments, Net Inv is positive (Add to Balance).
        # If Investments > Returns, Net Inv is negative (Subtract from Balance).
        # Equation: Balance = Income - Expenses + Net Inv.
        
        for m in months:
            inc = inc_grp[inc_grp["month"] == m]["amount"].sum() if not inc_grp.empty else 0
            ret = ret_grp[ret_grp["month"] == m]["amount"].sum() if not ret_grp.empty else 0
            exp_e = exp_grp_eur[exp_grp_eur["month"] == m]["amount_eur"].sum() if not exp_grp_eur.empty else 0
            exp_b_tk = exp_grp_bd_local[exp_grp_bd_local["month"] == m]["amount_local"].sum() if not exp_grp_bd_local.empty else 0
            exp_b_eur = exp_grp_bd_eur[exp_grp_bd_eur["month"] == m]["amount_eur"].sum() if not exp_grp_bd_eur.empty else 0
            inv = inv_grp[inv_grp["month"] == m]["amount"].sum() if not inv_grp.empty else 0
            
            # Net Inv = Returns - Investments
            net_inv = ret - inv
            
            # Balance = Income - Expenses + Net Inv
            # If net_inv is positive (Returns > Inv), we add to balance.
            # If net_inv is negative (Inv > Ret), we subtract from balance.
            # This is correct.
            bal = inc - exp_e - exp_b_eur - net_inv
            
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
        self.db_tabs_inv.add(self.inv_tab_ret, text="Returns")
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
        
        self.tree_inv_pivot = ttk.Treeview(self.inv_tab_pivot, show="headings")
        self.tree_inv_pivot.pack(fill="both", expand=True)

        # --- Inv/Ret Pivot Controls ---
        self.pivot_ctrl_frame = ttk.Frame(self.inv_tab_pivot)
        self.pivot_ctrl_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(self.pivot_ctrl_frame, text="Year:").pack(side="left")
        self.pivot_year = ttk.Combobox(self.pivot_ctrl_frame, values=["All"] + list(range(2020, 2030)), width=5, state="readonly")
        self.pivot_year.current(0)
        self.pivot_year.pack(side="left", padx=5)
        self.pivot_year.bind("<<ComboboxSelected>>", self.generate_db_tables)
        
        ttk.Label(self.pivot_ctrl_frame, text="Type:").pack(side="left", padx=10)
        self.pivot_filter = ttk.Combobox(self.pivot_ctrl_frame, values=["All", "Investments", "Returns"], state="readonly")
        self.pivot_filter.current(0)
        self.pivot_filter.pack(side="left", padx=5)
        self.pivot_filter.bind("<<ComboboxSelected>>", self.generate_db_tables)

    # --- Tab 1 Logic Helpers ---
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
            # FIX: Apply anchor='center'
            tree.column("#0", width=0, stretch=0)
            for col in final_cols:
                tree.heading(col, text=col)
                tree.column(col, width=120, minwidth=120, anchor="center", stretch=False)
                
            for idx, row in df_pivot.iterrows():
                month_name = idx.strftime('%B %Y') if hasattr(idx, 'strftime') else str(idx)
                vals = [month_name] + [f"{row[c]:.2f}" if pd.notnull(row[c]) else "0.00" for c in cols] + [f"{row.sum():.2f}"]
                tree.insert("", "end", values=vals)
            
            totals = [f"{df_pivot[c].sum():.2f}" for c in cols]
            tree.insert("", "end", values=("Total",) + tuple(totals) + (f"{df_pivot.sum().sum():.2f}",), tags=("total",))
            tree.tag_configure("total", background="#ccc")

        val_col = "amount_local" if filter_type == "BD" else "amount_eur"

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

    # --- Tab 1 Logic Helpers ---
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
                
            # Apply Type Filter (Investments/Return/All)
            if filter_piv != "All":
                inv_df = inv_df[inv_df["type"] == filter_piv]
            
            if not inv_df.empty:
                pivot = inv_df.pivot_table(index="month", columns="category", values="amount", aggfunc="sum", fill_value=0)
                
                cols_p = list(pivot.columns)
                cols_p = sorted(cols_p)
                
                # Add Total column
                cols_final = ["Month"] + cols_p + ["Total"]
                
                self.tree_inv_pivot["columns"] = cols_final
                
                # Apply anchor='center'
                self.tree_inv_pivot.column("#0", width=0)
                for c in cols_final:
                    self.tree_inv_pivot.heading(c, text=c)
                    self.tree_inv_pivot.column(c, width=120, minwidth=120, anchor="center", stretch=False)
                
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
        self.ana_year = ttk.Combobox(ctrl_top, values=["All"] + list(range(2020, 2030)), width=5, state="readonly")
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
        self.pie_year = ttk.Combobox(ctrl_bot, values=["All"] + list(range(2020, 2030)), width=5, state="readonly")
        self.pie_year.current(0)
        self.pie_year.pack(side="left", padx=5)
        
        ttk.Label(ctrl_bot, text="Type:").pack(side="left", padx=5)
        self.pie_type = ttk.Combobox(ctrl_bot, values=["GER", "BD", "All", "Investment"], state="readonly")
        self.pie_type.current(0)
        self.pie_type.pack(side="left", padx=5)
        self.pie_type.bind("<<ComboboxSelected>>", self.toggle_pie_level)
        
        ttk.Label(ctrl_bot, text="Level:").pack(side="left", padx=5)
        self.pie_level = ttk.Combobox(ctrl_bot, values=["Category", "Subcategory", "SubSubcategory"], state="readonly")
        self.pie_level.current(0)
        self.pie_level.pack(side="left", padx=5)
        self.pie_level.bind("<<ComboboxSelected>>", self.toggle_pie_level)
        
        # --- Dynamic Filters for Pie Chart ---
        # 1. Category Filter
        self.pie_cat_filter_frame = ttk.Frame(ctrl_bot)
        self.pie_cat_filter_frame.pack(side="left", padx=5)
        
        ttk.Label(self.pie_cat_filter_frame, text="Category:").pack(side="left")
        self.pie_cat_filter = ttk.Combobox(self.pie_cat_filter_frame, state="readonly", width=15)
        self.pie_cat_filter.pack(side="left", padx=5)
        self.pie_cat_filter.bind("<<ComboboxSelected>>", self.pie_cat_selected_action)

        # 2. Subcategory Filter
        self.pie_subcat_filter_frame = ttk.Frame(ctrl_bot)
        self.pie_subcat_filter_frame.pack(side="left", padx=5)
        
        ttk.Label(self.pie_subcat_filter_frame, text="Subcategory:").pack(side="left")
        self.pie_subcat_filter = ttk.Combobox(self.pie_subcat_filter_frame, state="readonly", width=15)
        self.pie_subcat_filter.pack(side="left", padx=5)
        self.pie_subcat_filter.bind("<<ComboboxSelected>>", self.plot_pie)
        
        # --- PLOT PIE BUTTON: Moved to right side ---
        ttk.Button(ctrl_bot, text="Plot Pie", command=self.plot_pie).pack(side="right", padx=10)
        
        self.fig_bot = plt.Figure(figsize=(5, 4), dpi=100)
        self.ax_bot = self.fig_bot.add_subplot(111)
        self.canvas_bot = FigureCanvasTkAgg(self.fig_bot, bot_frame)
        self.canvas_bot.get_tk_widget().pack(fill="both", expand=True)

    # --- Tab 3 Logic Helpers ---

    # Logic: When Category is selected, update subcategory list and re-plot
    def pie_cat_selected_action(self, event=None):
        selected_cat = self.pie_cat_filter.get()
        level = self.pie_level.get()
        
        if level == "Subcategory" or level == "SubSubcategory":
            self.populate_pie_subcat_options(selected_cat)
            # Automatically re-plot with new filter settings
            self.plot_pie()
        elif level == "Category":
            # If we are at category level, just plot, subcat filter is irrelevant
            self.plot_pie()

    # Helper: Populate Subcategory dropdown based on selected Category
    def populate_pie_subcat_options(self, selected_cat):
        ptype = self.pie_type.get()
        df = pd.DataFrame(self.dm.data["expenses"])
        
        if df.empty: 
            self.pie_subcat_filter['values'] = []
            self.pie_subcat_filter.set('')
            self.plot_pie()
            return

        # Filter by Year
        year = self.pie_year.get()
        df["year"] = pd.to_datetime(df["date"]).dt.year
        if year != "All": df = df[df["year"] == int(year)]
        
        # Filter by Type
        if ptype in ["GER", "BD"]:
            df = df[df["region"] == ptype]
        
        # Filter by Category
        if selected_cat:
            df = df[df["category"] == selected_cat]
        
        subs = df["subcategory"].unique().tolist()
        self.pie_subcat_filter['values'] = subs
        
        if subs:
            self.pie_subcat_filter.current(0)
        else:
            self.pie_subcat_filter.set('')

    # Helper: Populate Category dropdown
    def populate_pie_cat_options(self, ptype):
        # Modified to handle "All" type for Expense Analysis
        df = pd.DataFrame(self.dm.data["expenses"])
        
        if df.empty: 
            self.pie_cat_filter['values'] = []
            self.pie_cat_filter.set('')
            self.plot_pie()
            return

        # Filter by Year
        year = self.pie_year.get()
        df["year"] = pd.to_datetime(df["date"]).dt.year
        if year != "All": df = df[df["year"] == int(year)]
        
        # Filter by Region
        if ptype in ["GER", "BD"]:
            df = df[df["region"] == ptype]
        # If ptype == "All", we include all regions
        
        cats = list(df["category"].unique())
        self.pie_cat_filter['values'] = cats
        
        if cats:
            self.pie_cat_filter.current(0)
        else:
            self.pie_cat_filter.set('')
            
        # Trigger plot refresh
        self.plot_pie()

    def toggle_pie_level(self, event=None):
        level = self.pie_level.get()
        ptype = self.pie_type.get()

        # 1. Hide all dynamic filters initially
        self.pie_cat_filter_frame.pack_forget()
        self.pie_subcat_filter_frame.pack_forget()

        # 2. Logic: Investment Type
        if ptype == "Investment":
            # Requirement: "do not activate category, subcategory, and subsubcategory"
            # This means we just hide the frames.
            # The chart will handle Investment categories specifically.
            self.pie_cat_filter.set('')
            self.pie_subcat_filter.set('')
            return # Skip other logic
            
        # 3. Logic: Expense Types (GER, BD, All)
        # Requirement: "When type: all is selected then subcategory and subsubcategory pie plot is not functioning, filter options are not displaying"
        # We fix this by allowing the frames to show for "All" types too, 
        # and making populate_pie_cat_options handle the "All" logic.

        # --- Category Level ---
        if level == "Category":
            # Show Category Filter
            self.pie_cat_filter_frame.pack(side="left", padx=5)
            # Populate Categories
            self.populate_pie_cat_options(ptype)
        
        # --- Subcategory Level ---
        elif level == "Subcategory":
            # Show Category Filter (Activated)
            self.pie_cat_filter_frame.pack(side="left", padx=5)
            # Populate Categories
            self.populate_pie_cat_options(ptype)
            # Note: We do NOT auto-populate subcats here. 
            # We let the user select a category, which triggers `pie_cat_selected_action` 
            # to populate subcategory dropdown.
        
        # --- SubSubcategory Level ---
        elif level == "SubSubcategory":
            # Show Category Filter (Activated)
            self.pie_cat_filter_frame.pack(side="left", padx=5)
            # Show Subcategory Filter (Activated)
            self.pie_subcat_filter_frame.pack(side="left", padx=5)
            
            # Populate Categories
            self.populate_pie_cat_options(ptype)
            
            # Note: Similar to above, we rely on the user selecting a category 
            # to populate subcategories.

    # FIX: Updated to use dynamic filters
    def plot_pie(self, event=None):
        year = self.pie_year.get()
        ptype = self.pie_type.get()
        level = self.pie_level.get().lower()
        
        self.ax_bot.clear()
        
        # --- Investment Case ---
        if ptype == "Investment":
            # Requirement: "plot only investment/return categories"
            # If ptype is Investment, we treat it as an expense type internally? 
            # No, self.dm.data["investments"] is separate.
            
            df = pd.DataFrame(self.dm.data["investments"])
            if df.empty: return
            df["year"] = pd.to_datetime(df["date"]).dt.year
            if year != "All": df = df[df["year"] == int(year)]
            
            if df.empty:
                self.canvas_bot.draw()
                return
            
            # Requirement: "do not activate category". 
            # This is implicitly handled by toggle_pie_level (frames are hidden).
            # We just plot Investment distribution.
            counts = df[df["type"] == "Investment"].groupby("category")["amount"].sum()
            counts.plot(kind="pie", ax=self.ax_bot, autopct='%1.1f%%')
            self.ax_bot.set_ylabel("")
            self.ax_bot.set_title("Investment Distribution")
            
            self.canvas_bot.draw()
            return

        # --- Expense Case ---
        df = pd.DataFrame(self.dm.data["expenses"])
        if df.empty: return
        df["year"] = pd.to_datetime(df["date"]).dt.year
        if year != "All": df = df[df["year"] == int(year)]
        
        if ptype in ["GER", "BD", "All"]:
            if ptype != "All":
                df = df[df["region"] == ptype]
        
        if df.empty:
            self.canvas_bot.draw()
            return

        # --- Apply Dynamic Filtering ---
        
        # Get current filter selections
        selected_cat = self.pie_cat_filter.get()
        selected_sub = self.pie_subcat_filter.get()

        # --- Category Level ---
        if level == "category":
            # Show Category breakdown (ignoring filters)
            self.ax_bot.set_title(f"Expense Breakdown: Category ({ptype})")
            col = "category"

        # --- Subcategory Level ---
        elif level == "subcategory":
            # Requirement: "activate filters to select category"
            # Enforce that a category is selected
            if not selected_cat:
                messagebox.showwarning("Filter Required", "Please select a Category to view Subcategories.")
                return

            df = df[df["category"] == selected_cat]
            self.ax_bot.set_title(f"Expense Breakdown: Subcategory ({ptype}) - {selected_cat}")
            col = "subcategory"
            
        # --- SubSubcategory Level ---
        elif level == "subsubcategory":
            # Requirement: "activate filters to select category and subcategory"
            # Enforce selection
            if not selected_cat:
                messagebox.showwarning("Filter Required", "Please select a Category.")
                return
            if not selected_sub:
                 messagebox.showwarning("Filter Required", "Please select a Subcategory.")
                 return

            df = df[df["category"] == selected_cat]
            if selected_sub:
                df = df[df["subcategory"] == selected_sub]
                self.ax_bot.set_title(f"Expense Breakdown: SubSubcategory ({ptype}) - {selected_cat} - {selected_sub}")
            else:
                self.ax_bot.set_title(f"Expense Breakdown: SubSubcategory ({ptype}) - {selected_cat}")
            col = "subsubcategory"
            
        # --- Plot ---
        counts = df.groupby(col)["amount_eur"].sum()
        counts.plot(kind="pie", ax=self.ax_bot, autopct='%1.1f%%')
        self.ax_bot.set_ylabel("")
        self.canvas_bot.draw()
    
    def plot_trend(self):
        year = self.ana_year.get()
        # Use DataManager helper to get data
        inc_df, exp_eur, _, exp_bd_eur, inv_df, ret_df = self.dm.get_summary_df()
        
        df = pd.DataFrame({"Income": inc_df.set_index("month")["amount"]})
        df = df.join(exp_eur.set_index("month")["amount_eur"].rename("GER_Exp"))
        df = df.join(exp_bd_eur.set_index("month")["amount_eur"].rename("BD_Exp"))
        df = df.join(inv_df.set_index("month")["amount"].rename("Investment"))
        df = df.join(ret_df.set_index("month")["amount"].rename("Return"))
        
        if year != "All":
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

    # ==========================================
    # TAB 4: DAILY TRANS
    # ==========================================
    def setup_tab4(self):
        # --- Global Filters (Top of Tab 4) ---
        filter_frame = ttk.LabelFrame(self.tab4, text="Global Filters")
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Region:").pack(side="left", padx=5)
        self.dt_region = ttk.Combobox(filter_frame, values=["All", "GER", "BD"], state="readonly", width=5)
        self.dt_region.current(0)
        self.dt_region.pack(side="left", padx=5)
        self.dt_region.bind("<<ComboboxSelected>>", self.update_daily_trans_view)

        ttk.Label(filter_frame, text="Year:").pack(side="left", padx=10)
        self.dt_year = ttk.Combobox(filter_frame, values=list(range(2020, 2030)), state="readonly", width=5)
        self.dt_year.current(datetime.now().year - 2020) # Select current year
        self.dt_year.pack(side="left", padx=5)
        self.dt_year.bind("<<ComboboxSelected>>", self.update_daily_trans_view)

        ttk.Label(filter_frame, text="Month:").pack(side="left", padx=10)
        months = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        self.dt_month = ttk.Combobox(filter_frame, values=months, state="readonly", width=10)
        self.dt_month.current(datetime.now().month - 1)
        self.dt_month.pack(side="left", padx=5)
        self.dt_month.bind("<<ComboboxSelected>>", self.update_daily_trans_view)

        ttk.Button(filter_frame, text="Refresh View", command=self.update_daily_trans_view).pack(side="left", padx=20)

        # --- Middle Section: NoteBook for Tables ---
        mid_frame = ttk.LabelFrame(self.tab4, text="Daily Breakdown Tables")
        mid_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.daily_nb = ttk.Notebook(mid_frame)
        self.daily_nb.pack(fill="both", expand=True)

        # Tab 4.1: Category Table
        self.dt_tab1 = ttk.Frame(self.daily_nb)
        self.daily_nb.add(self.dt_tab1, text="By Category")
        self.dt_tree1_container = ttk.Frame(self.dt_tab1)
        self.dt_tree1_container.pack(fill="both", expand=True)

        # Tab 4.2: Subcategory Table
        self.dt_tab2 = ttk.Frame(self.daily_nb)
        self.daily_nb.add(self.dt_tab2, text="By Subcategory")
        
        t2_ctrl = ttk.Frame(self.dt_tab2)
        t2_ctrl.pack(fill="x", padx=5, pady=5)
        ttk.Label(t2_ctrl, text="Select Category:").pack(side="left")
        self.dt_t2_cat = ttk.Combobox(t2_ctrl, state="readonly", width=15)
        self.dt_t2_cat.pack(side="left", padx=5)
        self.dt_t2_cat.bind("<<ComboboxSelected>>", lambda e: self.refresh_dt_tables(2))
        
        self.dt_tree2_container = ttk.Frame(self.dt_tab2)
        self.dt_tree2_container.pack(fill="both", expand=True)

        # Tab 4.3: Subsubcategory Table
        self.dt_tab3 = ttk.Frame(self.daily_nb)
        self.daily_nb.add(self.dt_tab3, text="By Sub-Subcat")
        
        t3_ctrl = ttk.Frame(self.dt_tab3)
        t3_ctrl.pack(fill="x", padx=5, pady=5)
        ttk.Label(t3_ctrl, text="Category:").pack(side="left")
        self.dt_t3_cat = ttk.Combobox(t3_ctrl, state="readonly", width=12)
        self.dt_t3_cat.pack(side="left", padx=5)
        self.dt_t3_cat.bind("<<ComboboxSelected>>", self.on_dt_t3_cat_change)

        ttk.Label(t3_ctrl, text="Subcategory:").pack(side="left", padx=(10, 0))
        self.dt_t3_sub = ttk.Combobox(t3_ctrl, state="readonly", width=12)
        self.dt_t3_sub.pack(side="left", padx=5)
        self.dt_t3_sub.bind("<<ComboboxSelected>>", lambda e: self.refresh_dt_tables(3))

        self.dt_tree3_container = ttk.Frame(self.dt_tab3)
        self.dt_tree3_container.pack(fill="both", expand=True)

        # Bind tab switch inside daily notebook to update dropdowns if needed
        self.daily_nb.bind("<<NotebookTabChanged>>", self.on_dt_subtab_change)

        # --- Bottom Section: Plot ---
        bot_frame = ttk.LabelFrame(self.tab4, text="Monthly Trend Analysis")
        bot_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.fig_dt = plt.Figure(figsize=(5, 3), dpi=100)
        self.ax_dt = self.fig_dt.add_subplot(111)
        self.canvas_dt = FigureCanvasTkAgg(self.fig_dt, bot_frame)
        self.canvas_dt.get_tk_widget().pack(fill="both", expand=True)

    # --- Logic Helpers for Daily Trans ---



    def on_dt_t3_cat_change(self, event):
        # Update subcategory dropdown when category changes in Tab 3
        cat = self.dt_t3_cat.get()
        if not cat: return
        
        # Get available subcategories based on current data context (region/year/month)
        # We use a helper to get filtered DF
        df = self.get_filtered_daily_df()
        if not df.empty:
            subs = df[df['category'] == cat]['subcategory'].unique().tolist()
            self.dt_t3_sub['values'] = subs
            if subs: self.dt_t3_sub.current(0)
            else: self.dt_t3_sub.set('')
        
        self.refresh_dt_tables(3)

    def get_filtered_daily_df(self):
        """Helper to get DF based on Global Filters (Region, Year, Month)"""
        df = pd.DataFrame(self.dm.data["expenses"])
        if df.empty: return df

        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day

        region = self.dt_region.get()
        year = int(self.dt_year.get())
        month = self.dt_month.current() + 1 # Combobox is 0-indexed

        if region != "All":
            df = df[df['region'] == region]
        
        df = df[df['year'] == year]
        df = df[df['month'] == month]

        return df
    #----
        # --- Updated Logic Helpers for Daily Trans ---
    
    def update_daily_trans_view(self, event=None):
        # 1. Get Filtered Data based on Global Filters
        df = self.get_filtered_daily_df()
        
        # 2. Update Dropdown options (Categories) for Tab 2 & 3
        cats = []
        if not df.empty:
            cats = sorted(df['category'].unique().tolist())
        
        # Preserve current selections if they are still valid
        old_t2 = self.dt_t2_cat.get()
        old_t3 = self.dt_t3_cat.get()
        
        self.dt_t2_cat['values'] = cats
        self.dt_t3_cat['values'] = cats
        
        # Restore selection
        if cats:
            if old_t2 in cats: self.dt_t2_cat.set(old_t2)
            else: self.dt_t2_cat.current(0)
            
            if old_t3 in cats: self.dt_t3_cat.set(old_t3)
            else: self.dt_t3_cat.current(0)
        else:
            self.dt_t2_cat.set('')
            self.dt_t3_cat.set('')
    
        # 3. Trigger subcategory update for Tab 3
        self.on_dt_t3_cat_change(None)
    
        # 4. Refresh visible table
        idx = self.daily_nb.index(self.daily_nb.select())
        self.refresh_dt_tables(idx)
    
        # 5. Plot Bottom Graph
        self.plot_daily_total(df)
    
    def refresh_dt_tables(self, tab_index):
        # 1. Get the Year and Month from the global filters
        selected_year = self.dt_year.get()
        selected_month = self.dt_month.get()
    
        # 2. Get the filtered data
        df = self.get_filtered_daily_df()
        
        # Helper to clear container
        def clear_container(container):
            for widget in container.winfo_children():
                widget.destroy()
    
        # Tab 1: Category (Index 0)
        if tab_index == 0:
            clear_container(self.dt_tree1_container)
            if not df.empty:
                pivot = df.pivot_table(index='day', columns='category', values='amount_eur', aggfunc='sum', fill_value=0)
                # PASS YEAR AND MONTH HERE
                self.make_daily_table(self.dt_tree1_container, pivot, "Category Breakdown", selected_year, selected_month)
            else:
                ttk.Label(self.dt_tree1_container, text="No data for selected filters").pack(pady=20)
    
        # Tab 2: Subcategory (Index 1)
        elif tab_index == 1:
            clear_container(self.dt_tree2_container)
            cat = self.dt_t2_cat.get()
            if cat and not df.empty:
                sub_df = df[df['category'] == cat]
                if not sub_df.empty:
                    pivot = sub_df.pivot_table(index='day', columns='subcategory', values='amount_eur', aggfunc='sum', fill_value=0)
                    # PASS YEAR AND MONTH HERE
                    self.make_daily_table(self.dt_tree2_container, pivot, f"Subcategory ({cat})", selected_year, selected_month)
                else:
                    ttk.Label(self.dt_tree2_container, text="No data for this category").pack(pady=20)
            else:
                ttk.Label(self.dt_tree2_container, text="Select a Category").pack(pady=20)
    
        # Tab 3: Subsubcategory (Index 2)
        elif tab_index == 2:
            clear_container(self.dt_tree3_container)
            cat = self.dt_t3_cat.get()
            sub = self.dt_t3_sub.get()
            if cat and sub and not df.empty:
                sub_df = df[(df['category'] == cat) & (df['subcategory'] == sub)]
                if not sub_df.empty:
                    pivot = sub_df.pivot_table(index='day', columns='subsubcategory', values='amount_eur', aggfunc='sum', fill_value=0)
                    # PASS YEAR AND MONTH HERE
                    self.make_daily_table(self.dt_tree3_container, pivot, f"Detail ({cat} > {sub})", selected_year, selected_month)
                else:
                    ttk.Label(self.dt_tree3_container, text="No data for this subcategory").pack(pady=20)
            else:
                ttk.Label(self.dt_tree3_container, text="Select Category and Subcategory").pack(pady=20)
    
    # REPLACE THIS METHOD (Ensure it passes the correct index)
    def on_dt_subtab_change(self, event):
        # Get the index of the newly selected tab (0, 1, or 2)
        idx = self.daily_nb.index(self.daily_nb.select())
        
        # Special handling for Tab 2 (Subcategory) to ensure cat dropdowns are ready
        if idx == 1:
             # The dropdowns should have been populated by update_daily_trans_view
             pass
        # Special handling for Tab 3
        elif idx == 2:
            self.on_dt_t3_cat_change(None)
    
        self.refresh_dt_tables(idx)
    
    
    
    def make_daily_table(self, parent, pivot_df, title, year, month):
        # --- FIX: Type Conversion ---
        # Year comes as a string "2024" from combobox, convert to int
        try:
            year_int = int(year)
        except ValueError:
            year_int = 2024 # Default fallback
    
        # Month comes as a string "January", convert to integer 1-12
        month_map = {
            "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
            "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
        }
        month_int = month_map.get(month, 1) # Default to 1 if not found
        # ------------------------------
    
        # Clear existing tree
        for widget in parent.winfo_children(): widget.destroy()
    
        # Setup scrollable frame
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
    
        # Treeview
        cols = list(pivot_df.columns)
        tree_cols = ["Day"] + list(cols) + ["Total"]
        tree = ttk.Treeview(scrollable_frame, columns=tree_cols, show="headings")
    
        for col in tree_cols:
            tree.heading(col, text=col)
            tree.column(col, width=80, minwidth=50, anchor="center", stretch=False)
    
        tree.pack(fill="both", expand=True)
    
        # --- NEW: Configure Tags ---
        # Saturday will be red text
        tree.tag_configure("saturday", foreground="red")
        # Total row config
        tree.tag_configure("total", background="#ccc", font=("Arial", 10, "bold"))
    
        # Days 1 to 31
        all_days = range(1, 32)
        pivot_df = pivot_df.reindex(all_days, fill_value=0)
    
        totals = {c: 0.0 for c in cols}
        grand_total = 0.0
    
        for day in all_days:
            if day not in pivot_df.index: continue
            
            row_vals = []
            row_sum = 0.0
            
            for c in cols:
                val = pivot_df.loc[day, c]
                row_vals.append(f"{val:.2f}")
                row_sum += val
                totals[c] += val
            
            row_vals.append(f"{row_sum:.2f}")
            grand_total += row_sum
            
            d = datetime(year_int, month_int, day)
            
            # --- NEW: Check if Saturday (weekday() 5 is Saturday) ---
            row_tags = ()
            if d.weekday() == 5:
                row_tags = ("saturday",)
            # -------------------------------------------------------
    
            # --- CHANGE HERE: Format as "10.Sat" ---
            day_str = d.strftime("%d.%a")
            # -------------------------------------
    
            tree.insert("", "end", values=(day_str, *row_vals), tags=row_tags)
    
        # Total Row
        total_vals = [f"{totals[c]:.2f}" for c in cols]
        total_vals.append(f"{grand_total:.2f}")
        tree.insert("", "end", values=("TOTAL", *total_vals), tags=("total",))
        
    def plot_daily_total(self, df):
        self.ax_dt.clear()
        
        try:
            year = int(self.dt_year.get())
            month = self.dt_month.current() + 1
        except:
            year = datetime.now().year
            month = datetime.now().month
    
        if df.empty:
            self.ax_dt.text(0.5, 0.5, "No Data", ha="center")
        else:
            # Group by day
            daily_totals = df.groupby('day')['amount_eur'].sum()
            
            # Reindex for 1-31 to fill gaps with 0
            all_days = range(1, 32)
            daily_totals = daily_totals.reindex(all_days, fill_value=0)
            
            # PLOT CHANGES:
            # 1. kind='line' instead of 'bar'
            # 2. Added marker='o'
            daily_totals.plot(kind='line', ax=self.ax_dt, color='teal', marker='o', linewidth=2)
            
            # Mark weekends with vertical lines
            for day in range(1, 32):
                try:
                    d = datetime(year, month, day)
                    if d.weekday() >= 5: # Sat or Sun
                        self.ax_dt.axvline(x=day, color='red', linestyle='--', alpha=0.5, linewidth=1)
                except ValueError:
                    pass
    
            self.ax_dt.set_title(f"Total Expense Trend: {self.dt_month.get()} {self.dt_year.get()}")
            self.ax_dt.set_xlabel("Day of Month")
            self.ax_dt.set_ylabel("Amount (EUR)")
            self.ax_dt.grid(True, linestyle='-', alpha=0.3)
            self.ax_dt.set_xticks(all_days[::2]) # Show every other day label if crowded, or all_days
            
        self.fig_dt.tight_layout()
        self.canvas_dt.draw()
    #----
   

if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()
