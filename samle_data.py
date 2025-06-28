import mysql.connector
import random
from faker import Faker
from dotenv import load_dotenv
import os

# Initialize Faker for fake data generation
fake = Faker()

load_dotenv()  # Load variables from .env

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", "yourpassword"),
    database=os.getenv("DB_NAME", "librarydb")
)

cursor = conn.cursor()

# Function to generate student data with unique emails
def generate_students(count=30):
    courses = ["Computer Science", "Electrical Engineering", "Mechanical Engineering", 
               "Physics", "Mathematics", "Biology", "Chemistry", "Business Administration"]
    
    used_emails = set()
    
    for i in range(1, count+1):
        card_id = f"LIB-{i:04d}"
        name = fake.name()
        name_parts = name.split()
        if len(name_parts) >= 2:
            email = f"{name_parts[0].lower()}.{name_parts[-1].lower()}@university.edu"
        else:
            email = f"{name.lower().replace(' ', '')}@university.edu"
        
        # Avoid duplicate emails
        while email in used_emails:
            name = fake.name()
            name_parts = name.split()
            if len(name_parts) >= 2:
                email = f"{name_parts[0].lower()}.{name_parts[-1].lower()}@university.edu"
            else:
                email = f"{name.lower().replace(' ', '')}@university.edu"
        
        used_emails.add(email)
        
        course = random.choice(courses)
        year = random.randint(1, 4)
        
        cursor.execute("""
            INSERT INTO Students (Card_ID, Name, Email, Course, Year)
            VALUES (%s, %s, %s, %s, %s)
        """, (card_id, name, email, course, year))
    
    conn.commit()
    print(f"Generated {count} student records")

# Function to generate book data
def generate_books(count=50):
    statuses = ["Available", "Issued"]
    authors = ["J.K. Rowling", "George R.R. Martin", "J.R.R. Tolkien", 
               "Stephen King", "Agatha Christie", "Dan Brown", "Harper Lee",
               "Jane Austen", "Mark Twain", "Leo Tolstoy", "F. Scott Fitzgerald"]
    
    genres = ["Fiction", "Science Fiction", "Fantasy", "Mystery", "Thriller",
              "Romance", "Horror", "Biography", "History", "Science"]
    
    # Get all student card IDs for issuing books
    cursor.execute("SELECT Card_ID FROM Students")
    student_ids = [row[0] for row in cursor.fetchall()]
    
    for i in range(1, count+1):
        bk_id = f"BK-{i:04d}"
        genre = random.choice(genres)
        bk_name = f"{fake.word().capitalize()} {fake.word().capitalize()}"
        if random.random() > 0.7:
            bk_name = f"The {bk_name}"
        author = random.choice(authors)
        status = random.choice(statuses)
        card_id = None
        
        if status == "Issued" and student_ids:
            card_id = random.choice(student_ids)
        
        cursor.execute("""
            INSERT INTO Library (BK_NAME, BK_ID, AUTHOR_NAME, GENRE, BK_STATUS, CARD_ID)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (bk_name, bk_id, author, genre, status, card_id))
    
    conn.commit()
    print(f"Generated {count} book records")

# Main execution
if __name__ == "__main__":
    try:
        # Clear existing data (optional)
        cursor.execute("DELETE FROM Library")
        cursor.execute("DELETE FROM Students")
        conn.commit()
        print("Cleared existing data")
        
        # Generate new data
        generate_students(30)  # Generate 30 students
        generate_books(50)     # Generate 50 books
        
        print("Database populated successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
