import sqlite3
from sqlite3 import Cursor

DB_NAME = 'database.db'

class Routes:
    def __init__(self, name: str, route: str, last_accessed: str = None, project_id: int = None):
        self.name = name
        self.route = route
        self.last_accessed = last_accessed
        self.project_id = project_id
    def __repr__(self):
        return f"Routes(name={self.name}, route={self.route}, last_accessed={self.last_accessed}, project_id={self.project_id})"
    
def init_db():
    conn = sqlite3.connect(DB_NAME)
    
    # Create routes table if it doesn't exist
    conn.execute('CREATE TABLE IF NOT EXISTS routes (id INTEGER PRIMARY KEY, name TEXT, route TEXT, last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    
    # Create projects table
    conn.execute('CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT UNIQUE)')
    
    # Check if project_id exists in routes table, if not add it safely
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(routes)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'project_id' not in columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL")
        
    conn.commit()
    conn.close()

def get_routes():
    conn = sqlite3.connect(DB_NAME)
    cursor: Cursor = conn.cursor()
    cursor.execute('SELECT name, route, last_accessed, project_id FROM routes ORDER BY name ASC')
    routes = [Routes(name, route, last_accessed, project_id) for name, route, last_accessed, project_id in cursor.fetchall()]
    conn.close()
    return routes

def get_recent_routes():
    conn = sqlite3.connect(DB_NAME)
    cursor: Cursor = conn.cursor()
    cursor.execute('SELECT name, route, last_accessed, project_id FROM routes ORDER BY last_accessed DESC LIMIT 5')
    routes = [Routes(name, route, last_accessed, project_id) for name, route, last_accessed, project_id in cursor.fetchall()]
    conn.close()
    return routes

def update_last_accessed(name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor: Cursor = conn.cursor()
    cursor.execute('UPDATE routes SET last_accessed = CURRENT_TIMESTAMP WHERE name = ?', (name,))
    conn.commit()
    conn.close()

def add_route(name: str, route: str):
    conn = sqlite3.connect(DB_NAME)
    cursor: Cursor = conn.cursor()
    cursor.execute('INSERT INTO routes (name, route) VALUES (?, ?)', (name, route))
    conn.commit()
    conn.close()

def delete_route(name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor: Cursor = conn.cursor()
    cursor.execute('DELETE FROM routes WHERE name = ?', (name,))
    conn.commit()
    conn.close()

# --- Project Management Functions ---

def add_project(name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor: Cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO projects (name) VALUES (?)', (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Project already exists
    conn.close()

def delete_project(name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor: Cursor = conn.cursor()
    # Get project ID
    cursor.execute('SELECT id FROM projects WHERE name = ?', (name,))
    row = cursor.fetchone()
    if row:
        project_id = row[0]
        # Set project_id to NULL for all routes in this project (leaves them ungrouped)
        cursor.execute('UPDATE routes SET project_id = NULL WHERE project_id = ?', (project_id,))
        # Delete the project
        cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
        conn.commit()
    conn.close()

def get_projects():
    conn = sqlite3.connect(DB_NAME)
    cursor: Cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM projects ORDER BY name ASC')
    projects = cursor.fetchall()  # list of tuples (id, name)
    conn.close()
    return projects

def assign_route_to_project(route_name: str, project_name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor: Cursor = conn.cursor()
    
    # Get project id
    cursor.execute('SELECT id FROM projects WHERE name = ?', (project_name,))
    p_row = cursor.fetchone()
    if p_row:
        project_id = p_row[0]
        cursor.execute('UPDATE routes SET project_id = ? WHERE name = ?', (project_id, route_name))
        conn.commit()
    conn.close()

def remove_route_from_project(route_name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor: Cursor = conn.cursor()
    cursor.execute('UPDATE routes SET project_id = NULL WHERE name = ?', (route_name,))
    conn.commit()
    conn.close()

def get_grouped_routes():
    conn = sqlite3.connect(DB_NAME)
    cursor: Cursor = conn.cursor()
    
    # 1. Get all projects
    cursor.execute('SELECT id, name FROM projects ORDER BY name ASC')
    projects = cursor.fetchall()
    
    # Map project_id -> project_name
    proj_map = {p[0]: p[1] for p in projects}
    
    # Initialize dictionary for grouped routes
    grouped = {p[1]: [] for p in projects}
    ungrouped = []
    
    # 2. Get all routes
    cursor.execute('SELECT name, route, last_accessed, project_id FROM routes ORDER BY name ASC')
    for name, route, last_accessed, project_id in cursor.fetchall():
        r = Routes(name, route, last_accessed, project_id)
        if project_id in proj_map:
            grouped[proj_map[project_id]].append(r)
        else:
            ungrouped.append(r)
            
    conn.close()
    return grouped, ungrouped

# Automatically run initialization
init_db()
