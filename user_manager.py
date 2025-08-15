import hashlib
import sqlite3
import time
import secrets
from typing import List, Optional

class UserManager:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the user database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                email TEXT,
                created_at TIMESTAMP,
                login_attempts INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str, salt: str = None) -> str:
        """Hash password using SHA-256 with salt - FIXED: Strong hashing algorithm"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use SHA-256 with salt for better security
        salted_password = f"{salt}:{password}"
        return f"{salt}:{hashlib.sha256(salted_password.encode()).hexdigest()}"
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, hash_value = stored_hash.split(':', 1)
            return self.hash_password(password, salt) == stored_hash
        except ValueError:
            return False
    
    def create_user(self, username: str, password: str, email: str) -> bool:
        """Create a new user with proper SQL parameterization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # FIXED: Use parameterized queries to prevent SQL injection
        query = "INSERT INTO users (username, password_hash, email, created_at) VALUES (?, ?, ?, ?)"
        
        try:
            cursor.execute(query, (username, self.hash_password(password), email, time.time()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            return False
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user - LOGIC BUG: No rate limiting on failed attempts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT password_hash, login_attempts FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if result:
            stored_hash, attempts = result
            if self.verify_password(password, stored_hash):
                # Reset login attempts on successful login
                cursor.execute("UPDATE users SET login_attempts = 0 WHERE username = ?", (username,))
                conn.commit()
                conn.close()
                return True
            else:
                # LOGIC BUG: No limit on failed login attempts
                cursor.execute("UPDATE users SET login_attempts = login_attempts + 1 WHERE username = ?", (username,))
                conn.commit()
                conn.close()
                return False
        
        conn.close()
        return False
    
    def get_all_users(self) -> List[dict]:
        """Get all users - PERFORMANCE BUG: Loads all data into memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # PERFORMANCE BUG: No pagination, loads all users at once
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        # PERFORMANCE BUG: Inefficient data processing
        result = []
        for user in users:
            # Simulate some processing for each user
            processed_user = {
                'id': user[0],
                'username': user[1],
                'email': user[3],
                'created_at': user[4],
                'login_attempts': user[5]
            }
            # PERFORMANCE BUG: Multiple database calls in loop
            cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE ?", (f"%{user[1]}%",))
            similar_users = cursor.fetchone()[0]
            processed_user['similar_users_count'] = similar_users
            
            result.append(processed_user)
        
        conn.close()
        return result
    
    def search_users(self, search_term: str) -> List[dict]:
        """Search users - LOGIC BUG: Case sensitive search and off-by-one error"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # LOGIC BUG: Case-sensitive search (should be case-insensitive)
        cursor.execute("SELECT username, email FROM users WHERE username LIKE ?", (f"%{search_term}%",))
        results = cursor.fetchall()
        
        # LOGIC BUG: Off-by-one error in result limiting
        max_results = 10
        if len(results) >= max_results:  # Should be > not >=
            results = results[:max_results-1]  # This excludes the 10th result
        
        conn.close()
        return [{'username': r[0], 'email': r[1]} for r in results]

# Example usage with potential issues
if __name__ == "__main__":
    manager = UserManager()
    
    # This would be vulnerable to SQL injection
    manager.create_user("admin", "password123", "admin@example.com")
    manager.create_user("user1", "pass456", "user1@example.com")
    
    # These calls would expose performance issues with large datasets
    print(f"Authentication result: {manager.authenticate_user('admin', 'password123')}")
    print(f"All users: {manager.get_all_users()}")
    print(f"Search results: {manager.search_users('adm')}")