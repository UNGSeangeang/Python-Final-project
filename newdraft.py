import sqlite3
import csv
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from fpdf import FPDF
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PersonalFinanceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Tracker")
        self.root.geometry("800x600")
        
        # Database connection
        self.conn = sqlite3.connect("finance_tracker.db")
        self.cursor = self.conn.cursor()
        self.current_user = None  # Will be set after login
        
        # Initialize database
        self.initialize_db()
        self.show_login_screen()

    def initialize_db(self):
        """Initialize the database tables."""
        try:
            self.conn = sqlite3.connect("financial_tracker.db")
            self.cursor = self.conn.cursor()

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                );
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    date TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES Users(id)
                );
            """)
            self.conn.commit()
        except Exception as e:
            messagebox.showerror("Error", f"Database Initialization Error: {str(e)}")

    def show_login_screen(self):
        """Show the login screen."""
        self.clear_window()
        
        Label(self.root, text="Login", font=("Arial", 20)).pack(pady=20)
        
        Label(self.root, text="Username:").pack()
        username_entry = Entry(self.root)
        username_entry.pack(pady=5)
        
        Label(self.root, text="Password:").pack()
        password_entry = Entry(self.root, show="*")
        password_entry.pack(pady=5)
        
        Button(self.root, text="Login", command=lambda: self.login_user(username_entry.get(), password_entry.get())).pack(pady=10)
        
        Label(self.root, text="Don't have an account?").pack(pady=10)
        Button(self.root, text="Register", command=self.show_register_screen).pack()

    def show_register_screen(self):
        """Show the registration screen."""
        self.clear_window()
        
        Label(self.root, text="Register", font=("Arial", 20)).pack(pady=20)
        
        Label(self.root, text="Username:").pack()
        username_entry = Entry(self.root)
        username_entry.pack(pady=5)
        
        Label(self.root, text="Password:").pack()
        password_entry = Entry(self.root, show="*")
        password_entry.pack(pady=5)
        
        Button(self.root, text="Register", command=lambda: self.register_user(username_entry.get(), password_entry.get())).pack(pady=10)
        
        Button(self.root, text="Back to Login", command=self.show_login_screen).pack(pady=10)

    def register_user(self, username, password):
        if not username or not password:
            messagebox.showerror("Error", "All fields are required!")
            return
        try:
            self.cursor.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
            self.conn.commit()
            messagebox.showinfo("Success", "Registration successful!")
            self.show_login_screen()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists!")

    def login_user(self, username, password):
        self.cursor.execute("SELECT id FROM Users WHERE username = ? AND password = ?", (username, password))
        user = self.cursor.fetchone()
        
        if user:
            self.current_user = user[0]
            messagebox.showinfo("Success", f"Welcome, {username}!")
            self.show_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password!")

    def clear_window(self):
        """Clear the current window."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        """Show the main dashboard."""
        self.clear_window()

        # Dashboard Title
        Label(self.root, text="Personal Finance Tracker", font=("Arial", 20)).pack(pady=10)

        # Summary Section
        self.summary_frame = Frame(self.root)
        self.summary_frame.pack(pady=10)
        self.update_summary()  # Display initial summary

        # Transaction Input
        input_frame = Frame(self.root)
        input_frame.pack(pady=10)
        
        Label(input_frame, text="Type:").grid(row=0, column=0, padx=5, pady=5)
        self.type_var = StringVar(value="Expense")
        ttk.Combobox(input_frame, textvariable=self.type_var, values=["Income", "Expense"], state="readonly").grid(row=0, column=1, padx=5, pady=5)

        Label(input_frame, text="Amount:").grid(row=0, column=2, padx=5, pady=5)
        self.amount_entry = Entry(input_frame)
        self.amount_entry.grid(row=0, column=3, padx=5, pady=5)

        Label(input_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5)
        self.description_entry = Entry(input_frame)
        self.description_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        Label(input_frame, text="Date:").grid(row=2, column=0, padx=5, pady=5)
        self.date_entry = DateEntry(input_frame, width=15, background="darkblue", foreground="white", borderwidth=2)
        self.date_entry.grid(row=2, column=1, padx=5, pady=5)

        Button(input_frame, text="Add Transaction", command=self.add_transaction).grid(row=2, column=3, padx=5, pady=5)

        # Transactions Table
        columns = ("Type", "Amount", "Description", "Date")
        self.transactions_table = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            self.transactions_table.heading(col, text=col)
        self.transactions_table.pack(fill=BOTH, expand=True, padx=20, pady=20)

        Button(self.root, text="Edit Transaction", command=self.edit_transaction).pack(pady=5)
        Button(self.root, text="Delete Transaction", command=self.delete_transaction).pack(pady=5)

        # Buttons for Reports
        Button(self.root, text="Export Reports", command=self.export_reports).pack(pady=10)
        Button(self.root, text="View Reports", command=self.show_reports).pack(pady=10)

        # Load transactions
        self.refresh_transactions()

    def update_summary(self):
        """Update the summary section with total income, expenses, and balance."""
        self.cursor.execute("""
            SELECT 
                SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) AS total_income,
                SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) AS total_expenses
            FROM Transactions
            WHERE user_id = ?
        """, (self.current_user,))
        summary = self.cursor.fetchone()
        total_income = summary[0] or 0
        total_expenses = summary[1] or 0
        balance = total_income - total_expenses

        # Clear previous summary
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        # Display new summary
        Label(self.summary_frame, text=f"Total Income: ${total_income:.2f}", font=("Arial", 14), fg="green").pack(side=LEFT, padx=10)
        Label(self.summary_frame, text=f"Total Expenses: ${total_expenses:.2f}", font=("Arial", 14), fg="red").pack(side=LEFT, padx=10)
        Label(self.summary_frame, text=f"Balance: ${balance:.2f}", font=("Arial", 14), fg="blue").pack(side=LEFT, padx=10)

    def add_transaction(self):
        try:
            transaction_type = self.type_var.get()
            amount = float(self.amount_entry.get())
            description = self.description_entry.get()
            date = self.date_entry.get()  # Get the date from the widget

            self.cursor.execute("""
                INSERT INTO Transactions (user_id, type, amount, description, date) 
                VALUES (?, ?, ?, ?, ?)
            """, (self.current_user, transaction_type, amount, description, date))
            self.conn.commit()
            messagebox.showinfo("Success", "Transaction added successfully!")
            self.refresh_transactions()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount!")
        
    def refresh_transactions(self):
        # Clear the table
        for item in self.transactions_table.get_children():
            self.transactions_table.delete(item)

        # Fetch transactions for the logged-in user
        self.cursor.execute("SELECT id, type, amount, description, date FROM Transactions WHERE user_id = ?", (self.current_user,))
        for row in self.cursor.fetchall():
            transaction_id = row[0]
            display_data = row[1:] 
            self.transactions_table.insert("", END, values=display_data, tags=(transaction_id,))

    def edit_transaction(self):
        selected_item = self.transactions_table.selection()
        if not selected_item:
            messagebox.showerror("Error", "No transaction selected!")
            return

        transaction = self.transactions_table.item(selected_item, "values")
        transaction_id = self.transactions_table.item(selected_item, "tags")[0]

        # Ensure the transaction belongs to the current user
        self.cursor.execute("SELECT * FROM Transactions WHERE id = ? AND user_id = ?", (transaction_id, self.current_user))
        if not self.cursor.fetchone():
            messagebox.showerror("Error", "Unauthorized action!")
            return

        self.type_var.set(transaction[0])
        self.amount_entry.delete(0, END)
        self.amount_entry.insert(0, transaction[1])
        self.description_entry.delete(0, END)
        self.description_entry.insert(0, transaction[2])
        self.date_entry.set_date(transaction[3])
       
         # Remove existing update button, if any
        if hasattr(self, "update_button") and self.update_button:
            self.update_button.destroy()

        # Create a new update button
        self.update_button = Button(self.root, text="Update Transaction", command=lambda: self.update_transaction(transaction_id))
        self.update_button.pack(pady=10)

    def update_transaction(self, transaction_id):
        try:
            # Validate transaction type
            transaction_type = self.type_var.get()
            if not transaction_type:
                messagebox.showerror("Error", "Transaction type is required!")
                return

            # Validate amount
            amount = self.amount_entry.get().strip()
            if not amount:
                messagebox.showerror("Error", "Amount is required!")
                return

            try:
                amount = float(amount)  # Ensure valid numeric input
            except ValueError:
                messagebox.showerror("Error", "Amount must be a valid number!")
                return

            # Validate description
            description = self.description_entry.get().strip()
            if not description:
                messagebox.showerror("Error", "Description is required!")
                return

            # Validate date
            date = self.date_entry.get().strip()
            if not date:
                messagebox.showerror("Error", "Date is required!")
                return

            # Execute update query
            self.cursor.execute("""
                UPDATE Transactions 
                SET type = ?, amount = ?, description = ?, date = ?
                WHERE id = ? AND user_id = ?
            """, (transaction_type, amount, description, date, transaction_id, self.current_user))
            self.conn.commit()

            # Success message and refresh table
            messagebox.showinfo("Success", "Transaction updated successfully!")
            self.refresh_transactions()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update transaction: {str(e)}")

    def delete_transaction(self):
        selected_item = self.transactions_table.selection()
        if not selected_item:
            messagebox.showerror("Error", "No transaction selected!")
            return

        transaction_id = self.transactions_table.item(selected_item, "tags")[0]

        try:
            self.cursor.execute("DELETE FROM Transactions WHERE id = ? AND user_id = ?", (transaction_id, self.current_user))
            self.conn.commit()
            messagebox.showinfo("Success", "Transaction deleted successfully!")
            self.refresh_transactions()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_reports(self):
        choice = messagebox.askyesno("Export", "Do you want to export as PDF?")
        if choice:
            self.export_report_as_pdf()
        else:
            self.export_transactions_to_csv()

    def export_report_as_pdf(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return
        try:
            self.cursor.execute("SELECT type, amount, description, date FROM Transactions WHERE user_id = ?", (self.current_user,))
            rows = self.cursor.fetchall()

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Personal Finance Tracker Report", ln=True, align="C")

            pdf.ln(10)  # Line break
            pdf.set_font("Arial", size=10)
            for row in rows:
                pdf.cell(0, 10, f"Type: {row[0]}, Amount: {row[1]}, Description: {row[2]}, Date: {row[3]}", ln=True)

            pdf.output(file_path)
            messagebox.showinfo("Success", "PDF report exported successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_transactions_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        try:
            self.cursor.execute("SELECT type, amount, description, date FROM Transactions WHERE user_id = ?", (self.current_user,))
            rows = self.cursor.fetchall()
            
            with open(file_path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Type", "Amount", "Description", "Date"])
                writer.writerows(rows)
                
            messagebox.showinfo("Success", "CSV report exported successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def show_reports(self):
        """Show reports with visualizations: Income vs. Expenses and Spending Trends."""
        self.clear_window()
        Label(self.root, text="Reports", font=("Arial", 20)).pack(pady=10)

        # Buttons to go back or view specific charts
        Button(self.root, text="Back to Dashboard", command=self.show_dashboard).pack(pady=5)
        Button(self.root, text="Income vs. Expenses Pie Chart", command=self.show_pie_chart).pack(pady=5)
        Button(self.root, text="Spending Trends Line Graph", command=self.show_spending_trends).pack(pady=5)
    
    def show_pie_chart(self):
        """Display Income vs. Expenses Pie Chart."""
        self.cursor.execute("""
            SELECT type, SUM(amount) 
            FROM Transactions 
            WHERE user_id = ? 
            GROUP BY type
        """, (self.current_user,))
        data = self.cursor.fetchall()

        if not data:
            messagebox.showinfo("Info", "No data available to create a chart!")
            return

        labels = [row[0] for row in data]
        sizes = [row[1] for row in data]
        colors = ['#4CAF50', '#FF5252']  # Green for Income, Red for Expense
        explode = (0.1, 0) if len(sizes) == 2 else None  # Highlight the first slice

        # Create the pie chart
        fig, ax = plt.subplots()
        ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.axis('equal')  # Equal aspect ratio ensures the pie is drawn as a circle.

        # Embed the chart in Tkinter
        self.embed_chart_in_tkinter(fig, "Income vs. Expenses Pie Chart")

    def show_spending_trends(self):
        """Display Spending Trends Line Graph."""
        self.cursor.execute("""
            SELECT date, SUM(amount) 
            FROM Transactions 
            WHERE user_id = ? AND type = 'Expense'
            GROUP BY date
            ORDER BY date
        """, (self.current_user,))
        data = self.cursor.fetchall()

        if not data:
            messagebox.showinfo("Info", "No spending data available to create a graph!")
            return

        dates = [row[0] for row in data]
        amounts = [row[1] for row in data]

        # Create the line graph
        fig, ax = plt.subplots()
        ax.plot(dates, amounts, marker='o', color='b', label='Expenses')
        ax.set_title("Spending Trends")
        ax.set_xlabel("Date")
        ax.set_ylabel("Amount ($)")
        ax.grid(True)
        ax.legend()

        # Rotate date labels for better readability
        plt.xticks(rotation=45)

        # Embed the chart in Tkinter
        self.embed_chart_in_tkinter(fig, "Spending Trends Line Graph")

    def embed_chart_in_tkinter(self, fig, title):
        """Embed a matplotlib chart in the Tkinter application."""
        self.clear_window()

        Label(self.root, text=title, font=("Arial", 20)).pack(pady=10)
        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        # Back button to return to reports
        Button(self.root, text="Back to Reports", command=self.show_reports).pack(pady=10)

# Main
if __name__ == "__main__":
    root = Tk()
    app = PersonalFinanceTracker(root)
    root.mainloop()
