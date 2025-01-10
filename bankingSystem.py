import sqlite3
import random
import re
from getpass import getpass

# Database connection
conn = sqlite3.connect('banking_system.db')
cursor = conn.cursor()

# Table creation
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    account_number TEXT UNIQUE NOT NULL,
    dob TEXT NOT NULL,
    city TEXT NOT NULL,
    password TEXT NOT NULL,
    balance REAL NOT NULL,
    contact_number TEXT NOT NULL,
    email TEXT NOT NULL,
    address TEXT NOT NULL,
    is_active INTEGER DEFAULT 1
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(account_number) REFERENCES users(account_number)
);
''')

# Utility functions
def validate_email(email):
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email)

def validate_contact_number(contact):
    return re.match(r"^\d{10}$", contact)

def validate_password(password):
    return re.match(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$", password)

def generate_account_number():
    return str(random.randint(1000000000, 9999999999))

def add_user():
    name = input("Enter your name: ")
    dob = input("Enter your date of birth (YYYY-MM-DD): ")
    city = input("Enter your city: ")
    contact_number = input("Enter your contact number: ")
    email = input("Enter your email ID: ")
    address = input("Enter your address: ")
    password = getpass("Create your password (min 8 chars, 1 letter, 1 number): ")
    initial_balance = float(input("Enter initial balance (minimum 2000): "))

    if initial_balance < 2000:
        print("Initial balance must be at least 2000.")
        return

    if not validate_email(email):
        print("Invalid email format.")
        return

    if not validate_contact_number(contact_number):
        print("Invalid contact number. It should be 10 digits.")
        return

    if not validate_password(password):
        print("Invalid password. It should contain at least 8 characters, 1 letter, and 1 number.")
        return

    account_number = generate_account_number()
    
    try:
        cursor.execute('''
        INSERT INTO users (name, account_number, dob, city, password, balance, contact_number, email, address) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, account_number, dob, city, password, initial_balance, contact_number, email, address))
        conn.commit()
        print(f"User added successfully! Your account number is {account_number}.")
    except sqlite3.IntegrityError:
        print("Account number already exists. Please try again.")

def show_users():
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    if users:
        for user in users:
            print(f"ID: {user[0]}, Name: {user[1]}, Account Number: {user[2]}, DOB: {user[3]}, City: {user[4]}, Balance: {user[6]}, Contact: {user[7]}, Email: {user[8]}, Address: {user[9]}, Active: {'Yes' if user[10] else 'No'}")
    else:
        print("No users found.")

def login():
    account_number = input("Enter your account number: ")
    password = getpass("Enter your password: ")

    cursor.execute('SELECT * FROM users WHERE account_number = ? AND password = ?', (account_number, password))
    user = cursor.fetchone()

    if user:
        if not user[10]:
            print("Your account is deactivated. Please contact the bank.")
            return

        print(f"Welcome {user[1]}!")
        while True:
            print("""
            1. Show Balance
            2. Show Transactions
            3. Credit Amount
            4. Debit Amount
            5. Transfer Amount
            6. Activate/Deactivate Account
            7. Change Password
            8. Update Profile
            9. Logout
            """)
            choice = int(input("Enter your choice: "))

            if choice == 1:
                print(f"Your balance is: {user[6]}")

            elif choice == 2:
                cursor.execute('SELECT * FROM transactions WHERE account_number = ?', (account_number,))
                transactions = cursor.fetchall()
                for txn in transactions:
                    print(f"ID: {txn[0]}, Type: {txn[2]}, Amount: {txn[3]}, Timestamp: {txn[4]}")

            elif choice == 3:
                amount = float(input("Enter amount to credit: "))
                cursor.execute('UPDATE users SET balance = balance + ? WHERE account_number = ?', (amount, account_number))
                cursor.execute('INSERT INTO transactions (account_number, type, amount) VALUES (?, ?, ?)', (account_number, 'Credit', amount))
                conn.commit()
                print("Amount credited successfully.")

            elif choice == 4:
                amount = float(input("Enter amount to debit: "))
                if amount > user[6]:
                    print("Insufficient balance.")
                else:
                    cursor.execute('UPDATE users SET balance = balance - ? WHERE account_number = ?', (amount, account_number))
                    cursor.execute('INSERT INTO transactions (account_number, type, amount) VALUES (?, ?, ?)', (account_number, 'Debit', amount))
                    conn.commit()
                    print("Amount debited successfully.")

            elif choice == 5:
                target_account = input("Enter target account number: ")
                amount = float(input("Enter amount to transfer: "))
                cursor.execute('SELECT * FROM users WHERE account_number = ?', (target_account,))
                target_user = cursor.fetchone()
                if target_user:
                    if amount > user[6]:
                        print("Insufficient balance.")
                    else:
                        cursor.execute('UPDATE users SET balance = balance - ? WHERE account_number = ?', (amount, account_number))
                        cursor.execute('UPDATE users SET balance = balance + ? WHERE account_number = ?', (amount, target_account))
                        cursor.execute('INSERT INTO transactions (account_number, type, amount) VALUES (?, ?, ?)', (account_number, 'Transfer Out', amount))
                        cursor.execute('INSERT INTO transactions (account_number, type, amount) VALUES (?, ?, ?)', (target_account, 'Transfer In', amount))
                        conn.commit()
                        print("Amount transferred successfully.")
                else:
                    print("Target account not found.")

            elif choice == 6:
                status = int(input("Enter 1 to activate or 0 to deactivate your account: "))
                cursor.execute('UPDATE users SET is_active = ? WHERE account_number = ?', (status, account_number))
                conn.commit()
                print("Account status updated.")

            elif choice == 7:
                new_password = getpass("Enter your new password: ")
                if validate_password(new_password):
                    cursor.execute('UPDATE users SET password = ? WHERE account_number = ?', (new_password, account_number))
                    conn.commit()
                    print("Password updated successfully.")
                else:
                    print("Invalid password format.")

            elif choice == 8:
                new_city = input("Enter your new city: ")
                new_contact = input("Enter your new contact number: ")
                new_email = input("Enter your new email ID: ")
                new_address = input("Enter your new address: ")

                if validate_email(new_email) and validate_contact_number(new_contact):
                    cursor.execute('''
                    UPDATE users SET city = ?, contact_number = ?, email = ?, address = ? WHERE account_number = ?
                    ''', (new_city, new_contact, new_email, new_address, account_number))
                    conn.commit()
                    print("Profile updated successfully.")
                else:
                    print("Invalid email or contact number format.")

            elif choice == 9:
                print("Logged out successfully.")
                break

            else:
                print("Invalid choice.")
    else:
        print("Invalid account number or password.")

def main():
    while True:
        print("""
        BANKING SYSTEM
        1. Add User
        2. Show Users
        3. Login
        4. Exit
        """)
        choice = int(input("Enter your choice: "))

        if choice == 1:
            add_user()
        elif choice == 2:
            show_users()
        elif choice == 3:
            login()
        elif choice == 4:
            print("Thank you for using the Banking System. Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

# Close the database connection on exit
conn.close()
