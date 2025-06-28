import mysql.connector
from tkinter import *
import tkinter.ttk as ttk
import tkinter.messagebox as mb
import tkinter.simpledialog as sd
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env

connector = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", "yourpassword"),
    database=os.getenv("DB_NAME", "librarydb")
)

cursor = connector.cursor()

# Creating tables if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS Library (
    BK_NAME VARCHAR(255),
    BK_ID VARCHAR(50) PRIMARY KEY,
    AUTHOR_NAME VARCHAR(255),
    GENRE VARCHAR(50),
    BK_STATUS VARCHAR(20),
    CARD_ID VARCHAR(50)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Students (
    Card_ID VARCHAR(50) PRIMARY KEY,
    Name VARCHAR(255),
    Email VARCHAR(255),
    Course VARCHAR(100),
    Year INT
)
""")
connector.commit()

# Common genres for suggestions
COMMON_GENRES = [
    "Fiction", "Science Fiction", "Fantasy", "Mystery", "Thriller",
    "Romance", "Horror", "Biography", "History", "Science", "Non-Fiction",
    "Adventure", "Crime", "Drama", "Poetry", "Self-Help"
]

# Functions
def issuer_card():
    Cid = sd.askstring('Issuer Card ID', 'What is the Issuer\'s Card ID?\t\t\t')
    if not Cid:
        mb.showerror('Issuer ID cannot be empty!', 'Please enter a valid Card ID.')
        return None
    
    # Check if the card ID exists in Students table
    cursor.execute('SELECT * FROM Students WHERE Card_ID = %s', (Cid,))
    student = cursor.fetchone()
    
    if not student:
        mb.showerror('Invalid Card ID', 'This Card ID is not registered. Please register as a student first.')
        return None
    else:
        return Cid

def display_records():
    tree.delete(*tree.get_children())
    cursor.execute('SELECT BK_NAME, BK_ID, AUTHOR_NAME, GENRE, BK_STATUS, CARD_ID FROM Library')
    data = cursor.fetchall()
    for record in data:
        tree.insert('', END, values=record)

def display_students():
    student_tree.delete(*student_tree.get_children())
    cursor.execute('SELECT * FROM Students')
    data = cursor.fetchall()
    for record in data:
        student_tree.insert('', END, values=record)

def clear_fields():
    bk_status.set('Available')
    bk_id.set(generate_next_book_id())
    bk_name.set('')
    author_name.set('')
    card_id.set('')
    genre_var.set('')
    bk_id_entry.config(state='readonly')
    bk_id_entry.config(state='normal')
    try:
        tree.selection_remove(tree.selection()[0])
    except:
        pass

def clear_student_fields():
    for var in [student_name_var, student_email_var, student_course_var]:
        var.set('')
    student_year_var.set(0)
    lib_id_preview.set(generate_next_card_id())

    try:
        student_tree.selection_remove(student_tree.selection()[0])
    except:
        pass

def clear_and_display():
    clear_fields()
    clear_student_fields()
    display_records()
    display_students()


def generate_next_card_id():
    cursor.execute("SELECT MAX(Card_ID) FROM Students")
    last_id = cursor.fetchone()[0]
    if last_id:
        # Correctly extract the numeric part, skipping "LIB-"
        num = int(last_id[4:]) + 1  # Now starts after 'LIB-'
        return f"LIB-{num:04d}"
    else:
        return "LIB-0001"  # First student

def add_record():
    if not (bk_name.get() and author_name.get() and genre_var.get()):
        mb.showerror("Error", "Please fill all fields including genre!")
        return
        
    if bk_status.get() == 'Issued':
        card_id_val = issuer_card()
        if not card_id_val:
            return
        card_id.set(card_id_val)
    else:
        card_id.set('N/A')

    surety = mb.askyesno('Are you sure?',
        'Are you sure you want to add this book?\nNote: Book ID cannot be changed later.')

    if surety:
        try:
            values = (bk_name.get(), bk_id.get(), author_name.get(), 
                     genre_var.get(), bk_status.get(), card_id.get())
            cursor.execute('''
                INSERT INTO Library 
                (BK_NAME, BK_ID, AUTHOR_NAME, GENRE, BK_STATUS, CARD_ID) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', values)
            connector.commit()
            clear_and_display()
            mb.showinfo('Success', 'Book added successfully!')
        except mysql.connector.IntegrityError:
            mb.showerror('Error', 'This Book ID already exists!')

def view_record():
    if not tree.selection():
        mb.showerror('Error', 'Please select a book!')
        return
        
    selected = tree.focus()
    values = tree.item(selected)['values']
    bk_name.set(values[0])
    bk_id.set(values[1])
    author_name.set(values[2])
    genre_var.set(values[3])  # Set genre from record
    bk_status.set(values[4])
    card_id.set(values[5])

def update_record():
    if not tree.selection():
        mb.showerror('Select a row!', 'Please select a record to update.')
        return
        
    view_record()
    
    def update():
        if bk_status.get() == 'Issued':
            card_id_val = issuer_card()
            if not card_id_val:
                return
            card_id.set(card_id_val)
        else:
            card_id.set('N/A')

        cursor.execute('''
            UPDATE Library SET 
            BK_NAME=%s, BK_STATUS=%s, AUTHOR_NAME=%s, GENRE=%s, CARD_ID=%s 
            WHERE BK_ID=%s
        ''', (bk_name.get(), bk_status.get(), author_name.get(), 
              genre_var.get(), card_id.get(), bk_id.get()))
        connector.commit()
        clear_and_display()
        edit.destroy()
        bk_id_entry.config(state='normal')
        clear.config(state='normal')

    bk_id_entry.config(state='disabled')
    clear.config(state='disabled')
    edit = Button(left_frame, text='Update Record', font=btn_font, bg=btn_hlb_bg, width=20, command=update)
    edit.place(x=50, y=425)

def remove_record():
    if not tree.selection():
        mb.showerror('Error!', 'Please select a book to delete.')
        return
    selected = tree.focus()
    values = tree.item(selected)['values']
    cursor.execute('DELETE FROM Library WHERE BK_ID=%s', (values[1],))
    connector.commit()
    tree.delete(selected)
    mb.showinfo('Deleted', 'Record deleted successfully.')
    clear_and_display()

def delete_inventory():
    if mb.askyesno('Are you sure?', 'Do you really want to delete the entire inventory?'):
        tree.delete(*tree.get_children())
        cursor.execute('DELETE FROM Library')
        connector.commit()
        mb.showinfo('Inventory Cleared', 'All books have been deleted from inventory.')

def change_availability():
    if not tree.selection():
        mb.showerror('Error!', 'Please select a book from the database')
        return

    selected = tree.focus()
    values = tree.item(selected)['values']
    BK_id = values[1]
    BK_status = values[4]  # Updated index to account for genre

    if BK_status == 'Issued':
        if mb.askyesno('Return Confirmed?', 'Has the book been returned?'):
            cursor.execute('UPDATE Library SET BK_STATUS=%s, CARD_ID=%s WHERE BK_ID=%s', ('Available', 'N/A', BK_id))
            connector.commit()
            mb.showinfo('Success', 'Book has been returned and marked as Available.')
        else:
            mb.showinfo('Not returned', 'Cannot mark as Available until returned.')
    else:
        new_card = issuer_card()
        if new_card:
            cursor.execute('UPDATE Library SET BK_STATUS=%s, CARD_ID=%s WHERE BK_ID=%s', ('Issued', new_card, BK_id))
            connector.commit()
            mb.showinfo('Success', 'Book has been issued successfully.')

    clear_and_display()

def add_student():
    student_name = student_name_var.get()
    student_email = student_email_var.get()
    student_course = student_course_var.get()
    student_year = student_year_var.get()

    if not (student_name and student_email and student_course and student_year):
        mb.showerror("Error", "All fields except Card ID are required!")
        return

    # Generate the next Card ID
    new_card_id = lib_id_preview.get()

    try:
        cursor.execute("""
            INSERT INTO Students (Card_ID, Name, Email, Course, Year)
            VALUES (%s, %s, %s, %s, %s)
        """, (new_card_id, student_name, student_email, student_course, student_year))
        connector.commit()
        mb.showinfo("Success", f"Student added successfully. Card ID: {new_card_id}")
        clear_student_fields()
        display_students()
    except mysql.connector.IntegrityError:
        mb.showerror('Error!', 'This student already exists.')
    except Exception as e:
        mb.showerror("Error", f"An error occurred: {str(e)}")

selected_student_card_id = None

def view_student():
    global selected_student_card_id
    if not student_tree.selection():
        mb.showerror('Select a student!', 'To view a record, you must select it in the table.')
        return

    current_item_selected = student_tree.focus()
    selection = student_tree.item(current_item_selected)['values']

    selected_student_card_id = selection[0]  # Save Card_ID globally
    student_name_var.set(selection[1])
    student_email_var.set(selection[2])
    student_course_var.set(selection[3])
    student_year_var.set(selection[4])

def update_student():
    global selected_student_card_id
    if not selected_student_card_id:
        mb.showerror('Select a student!', 'To update a record, you must select it in the table and view it first.')
        return

    student_name_val = student_name_var.get()
    student_email_val = student_email_var.get()
    student_course_val = student_course_var.get()
    student_year_val = student_year_var.get()

    if not (student_name_val and student_email_val and student_course_val and student_year_val):
        mb.showerror("Error", "All fields are required!")
        return

    try:
        cursor.execute("""
            UPDATE Students 
            SET Name = %s, Email = %s, Course = %s, Year = %s 
            WHERE Card_ID = %s
        """, (student_name_val, student_email_val, student_course_val, student_year_val, card_id))

        connector.commit()
        mb.showinfo("Success", "Student details updated successfully.")
        clear_student_fields()
        display_students()
    except Exception as e:
        mb.showerror("Error", f"An error occurred: {str(e)}")

def delete_student():
    if not student_tree.selection():
        mb.showerror('Select a student!', 'To delete a record, you must select it in the table.')
        return

    current_item_selected = student_tree.focus()
    values_in_selected_item = student_tree.item(current_item_selected)
    selection = values_in_selected_item['values']

    cursor.execute('DELETE FROM Students WHERE Card_ID = %s', (selection[0],))
    connector.commit()

    mb.showinfo('Success', 'Student record deleted successfully.')
    clear_student_fields()
    display_students()

def generate_next_book_id():
    cursor.execute("SELECT MAX(BK_ID) FROM Library")
    last_id = cursor.fetchone()[0]
    if last_id:
        num = int(last_id[3:]) + 1  # Skip 'BK-'
        return f"BK-{num:04d}"
    else:
        return "BK-0001"

# GUI Config
lf_bg = 'LightSkyBlue'
rtf_bg = 'DeepSkyBlue'
rbf_bg = 'DodgerBlue'
btn_hlb_bg = 'SteelBlue'

lbl_font = ('Georgia', 13)
entry_font = ('Times New Roman', 12)
btn_font = ('Gill Sans MT', 13)

root = Tk()
root.title('PythonGeeks Library Management System')
root.geometry('1200x650')
root.resizable(0, 0)

# Variables
bk_status = StringVar(value='Available')
bk_name = StringVar()
bk_id = StringVar()
author_name = StringVar()
card_id = StringVar()
genre_var = StringVar()

student_name_var = StringVar()
student_email_var = StringVar()
student_course_var = StringVar()
student_year_var = IntVar()
lib_id_preview = StringVar()

# Main container
main_container = Frame(root)
main_container.pack(fill=BOTH, expand=True)

# Header
header = Frame(main_container, bg=btn_hlb_bg)
header.pack(fill=X)
Label(header, text='LIBRARY MANAGEMENT SYSTEM', font=("Noto Sans CJK TC", 15, 'bold'), bg=btn_hlb_bg, fg='White').pack(pady=10)

# Notebook for tabs
notebook = ttk.Notebook(main_container)
notebook.pack(fill=BOTH, expand=True)

# Book Management Frame
book_frame = Frame(notebook)
notebook.add(book_frame, text='Book Management')

# Student Management Frame
student_frame = Frame(notebook)
notebook.add(student_frame, text='Student Management')

# ========== Book Management Tab ==========
# Left Frame (Book Form)
left_frame = Frame(book_frame, bg=lf_bg)
left_frame.pack(side=LEFT, fill=Y, padx=10, pady=10)

# Right Frame (Book List)
right_frame = Frame(book_frame)
right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)

# Top Right Buttons (Book Management)
button_frame = Frame(right_frame, bg=rtf_bg)
button_frame.pack(fill=X)

Button(button_frame, text='Delete book record', font=btn_font, bg=btn_hlb_bg, width=17, command=remove_record).pack(side=LEFT, padx=5, pady=5)
Button(button_frame, text='Delete full inventory', font=btn_font, bg=btn_hlb_bg, width=17, command=delete_inventory).pack(side=LEFT, padx=5, pady=5)
Button(button_frame, text='Update book details', font=btn_font, bg=btn_hlb_bg, width=17, command=update_record).pack(side=LEFT, padx=5, pady=5)
Button(button_frame, text='Change Book Availability', font=btn_font, bg=btn_hlb_bg, width=19, command=change_availability).pack(side=LEFT, padx=5, pady=5)

# Book Form (Left Frame)
Label(left_frame, text='Book Details', bg=lf_bg, font=("Arial", 14, 'bold')).pack(pady=10)

Label(left_frame, text='Book Name', bg=lf_bg, font=lbl_font).pack()
Entry(left_frame, width=25, font=entry_font, textvariable=bk_name).pack(pady=5)

Label(left_frame, text='Book ID', bg=lf_bg, font=lbl_font).pack()
bk_id_entry = Entry(left_frame, width=25, font=entry_font, textvariable=bk_id)
bk_id_entry.pack(pady=5)

Label(left_frame, text='Author Name', bg=lf_bg, font=lbl_font).pack()
Entry(left_frame, width=25, font=entry_font, textvariable=author_name).pack(pady=5)

# Genre Combobox
Label(left_frame, text='Genre', bg=lf_bg, font=lbl_font).pack()
genre_combo = ttk.Combobox(left_frame, textvariable=genre_var, values=COMMON_GENRES)
genre_combo.pack(pady=5)
genre_combo.config(font=entry_font, width=22)

Label(left_frame, text='Status', bg=lf_bg, font=lbl_font).pack()
OptionMenu(left_frame, bk_status, 'Available', 'Issued').pack(pady=5)

submit = Button(left_frame, text='Add new record', font=btn_font, bg=btn_hlb_bg, width=20, command=add_record)
submit.pack(pady=10)

clear = Button(left_frame, text='Clear fields', font=btn_font, bg=btn_hlb_bg, width=20, command=clear_fields)
clear.pack(pady=10)

# Book Treeview (Right Frame)
Label(right_frame, text='BOOK INVENTORY', bg=rbf_bg, font=("Noto Sans CJK TC", 15, 'bold')).pack(fill=X)

tree_frame = Frame(right_frame)
tree_frame.pack(fill=BOTH, expand=True)

tree = ttk.Treeview(tree_frame, selectmode=BROWSE, 
                   columns=('Book Name', 'Book ID', 'Author', 'Genre', 'Status', 'Issuer Card ID'))

scroll_y = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=tree.yview)
scroll_y.pack(side=RIGHT, fill=Y)

scroll_x = ttk.Scrollbar(tree_frame, orient=HORIZONTAL, command=tree.xview)
scroll_x.pack(side=BOTTOM, fill=X)

tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

tree.heading('Book Name', text='Book Name', anchor=CENTER)
tree.heading('Book ID', text='Book ID', anchor=CENTER)
tree.heading('Author', text='Author', anchor=CENTER)
tree.heading('Genre', text='Genre', anchor=CENTER)
tree.heading('Status', text='Status', anchor=CENTER)
tree.heading('Issuer Card ID', text='Issuer Card ID', anchor=CENTER)

tree.column('#0', width=0, stretch=NO)
tree.column('#1', width=200, stretch=NO)
tree.column('#2', width=100, stretch=NO)
tree.column('#3', width=150, stretch=NO)
tree.column('#4', width=120, stretch=NO)
tree.column('#5', width=120, stretch=NO)
tree.column('#6', width=150, stretch=NO)

tree.pack(fill=BOTH, expand=True)

# ========== Student Management Tab ==========
# Left Frame (Student Form)
student_left_frame = Frame(student_frame, bg=lf_bg)
student_left_frame.pack(side=LEFT, fill=Y, padx=10, pady=10)

# Right Frame (Student List)
student_right_frame = Frame(student_frame)
student_right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)

# Student Form (Left Frame)
Label(student_left_frame, text='Student Details', bg=lf_bg, font=("Arial", 14, 'bold')).pack(pady=10)

Label(student_left_frame, text='Library ID (Auto)', bg=lf_bg, font=lbl_font).pack()
Entry(student_left_frame, width=25, font=entry_font, textvariable=lib_id_preview, state='readonly').pack(pady=5)

Label(student_left_frame, text='Student Name', bg=lf_bg, font=lbl_font).pack()
Entry(student_left_frame, width=25, font=entry_font, textvariable=student_name_var).pack(pady=5)

Label(student_left_frame, text='Student Email', bg=lf_bg, font=lbl_font).pack()
Entry(student_left_frame, width=25, font=entry_font, textvariable=student_email_var).pack(pady=5)

Label(student_left_frame, text='Student Course', bg=lf_bg, font=lbl_font).pack()
Entry(student_left_frame, width=25, font=entry_font, textvariable=student_course_var).pack(pady=5)

Label(student_left_frame, text='Student Year', bg=lf_bg, font=lbl_font).pack()
Entry(student_left_frame, width=25, font=entry_font, textvariable=student_year_var).pack(pady=5)

add_student_btn = Button(student_left_frame, text='Add Student', font=btn_font, bg=btn_hlb_bg, width=20, command=add_student)
add_student_btn.pack(pady=10)

update_student_btn = Button(student_left_frame, text='Update Student', font=btn_font, bg=btn_hlb_bg, width=20, command=update_student)
update_student_btn.pack(pady=10)

delete_student_btn = Button(student_left_frame, text='Delete Student', font=btn_font, bg=btn_hlb_bg, width=20, command=delete_student)
delete_student_btn.pack(pady=10)

# Student Treeview (Right Frame)
Label(student_right_frame, text='STUDENT RECORDS', bg=rbf_bg, font=("Noto Sans CJK TC", 15, 'bold')).pack(fill=X)

student_tree_frame = Frame(student_right_frame)
student_tree_frame.pack(fill=BOTH, expand=True)

student_tree = ttk.Treeview(student_tree_frame, selectmode=BROWSE, columns=('Card ID', 'Name', 'Email', 'Course', 'Year'))

student_scroll_y = ttk.Scrollbar(student_tree_frame, orient=VERTICAL, command=student_tree.yview)
student_scroll_y.pack(side=RIGHT, fill=Y)

student_scroll_x = ttk.Scrollbar(student_tree_frame, orient=HORIZONTAL, command=student_tree.xview)
student_scroll_x.pack(side=BOTTOM, fill=X)

student_tree.configure(yscrollcommand=student_scroll_y.set, xscrollcommand=student_scroll_x.set)

student_tree.heading('Card ID', text='Card ID', anchor=CENTER)
student_tree.heading('Name', text='Name', anchor=CENTER)
student_tree.heading('Email', text='Email', anchor=CENTER)
student_tree.heading('Course', text='Course', anchor=CENTER)
student_tree.heading('Year', text='Year', anchor=CENTER)

student_tree.column('#0', width=0, stretch=NO)
student_tree.column('#1', width=150, stretch=NO)
student_tree.column('#2', width=200, stretch=NO)
student_tree.column('#3', width=250, stretch=NO)
student_tree.column('#4', width=200, stretch=NO)
student_tree.column('#5', width=100, stretch=NO)

student_tree.pack(fill=BOTH, expand=True)

# Start program
clear_and_display()
root.mainloop()