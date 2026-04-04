"""
Task Manager - Full Project & Task CRUD System
SQLite-based with project/task hierarchy
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

DATA_DIR = Path(__file__).parent.parent / "data"
DB_FILE = DATA_DIR / "agency_os.db"

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class ProjectStatus(Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Project:
    id: str
    name: str
    description: str
    client_id: Optional[str]
    status: str
    budget: float
    start_date: str
    due_date: Optional[str]
    created_at: str
    updated_at: str

@dataclass
class Task:
    id: str
    project_id: str
    title: str
    description: str
    status: str
    priority: int
    assigned_to: Optional[str]
    due_date: Optional[str]
    estimated_hours: float
    actual_hours: float
    tags: str  # JSON array
    created_at: str
    updated_at: str
    completed_at: Optional[str]

@dataclass
class TimeEntry:
    id: str
    task_id: str
    user_id: str
    hours: float
    description: str
    date: str
    created_at: str

class TaskManager:
    def __init__(self):
        self.db_path = DB_FILE
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    client_id TEXT,
                    status TEXT DEFAULT 'active',
                    budget REAL DEFAULT 0,
                    start_date TEXT,
                    due_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'todo',
                    priority INTEGER DEFAULT 2,
                    assigned_to TEXT,
                    due_date TEXT,
                    estimated_hours REAL DEFAULT 0,
                    actual_hours REAL DEFAULT 0,
                    tags TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );

                CREATE TABLE IF NOT EXISTS time_entries (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    user_id TEXT,
                    hours REAL NOT NULL,
                    description TEXT,
                    date TEXT DEFAULT CURRENT_DATE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                );

                CREATE TABLE IF NOT EXISTS task_comments (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    user_id TEXT,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to);
                CREATE INDEX IF NOT EXISTS idx_time_entries_task ON time_entries(task_id);
                CREATE INDEX IF NOT EXISTS idx_projects_client ON projects(client_id);
                CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
            """)

    # ─── PROJECT CRUD ────────────────────────────────────────────────────────────

    def create_project(self, name: str, description: str = "", client_id: Optional[str] = None,
                       budget: float = 0, due_date: Optional[str] = None) -> Project:
        """Create a new project"""
        project_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        project = Project(
            id=project_id,
            name=name,
            description=description,
            client_id=client_id,
            status=ProjectStatus.ACTIVE.value,
            budget=budget,
            start_date=now[:10],
            due_date=due_date,
            created_at=now,
            updated_at=now
        )

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO projects (id, name, description, client_id, status, budget, start_date, due_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (project.id, project.name, project.description, project.client_id,
                  project.status, project.budget, project.start_date, project.due_date,
                  project.created_at, project.updated_at))

        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()

            if row:
                return Project(**dict(row))
            return None

    def get_projects(self, status: Optional[str] = None, client_id: Optional[str] = None) -> List[Project]:
        """Get all projects with optional filters"""
        query = "SELECT * FROM projects WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if client_id:
            query += " AND client_id = ?"
            params.append(client_id)

        query += " ORDER BY updated_at DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [Project(**dict(row)) for row in rows]

    def update_project(self, project_id: str, **kwargs) -> bool:
        """Update project fields"""
        allowed = ['name', 'description', 'client_id', 'status', 'budget', 'due_date']
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return False

        updates['updated_at'] = datetime.now().isoformat()

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [project_id]

        with self._get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE projects SET {set_clause} WHERE id = ?",
                values
            )
            return cursor.rowcount > 0

    def delete_project(self, project_id: str) -> bool:
        """Delete project and all its tasks"""
        with self._get_connection() as conn:
            # Delete time entries for project tasks
            conn.execute("""
                DELETE FROM time_entries WHERE task_id IN
                (SELECT id FROM tasks WHERE project_id = ?)
            """, (project_id,))

            # Delete comments for project tasks
            conn.execute("""
                DELETE FROM task_comments WHERE task_id IN
                (SELECT id FROM tasks WHERE project_id = ?)
            """, (project_id,))

            # Delete tasks
            conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))

            # Delete project
            cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cursor.rowcount > 0

    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """Get project statistics"""
        with self._get_connection() as conn:
            # Task counts
            task_stats = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM tasks WHERE project_id = ?
                GROUP BY status
            """, (project_id,)).fetchall()

            # Time spent
            time_result = conn.execute("""
                SELECT SUM(te.hours) as total_hours
                FROM time_entries te
                JOIN tasks t ON te.task_id = t.id
                WHERE t.project_id = ?
            """, (project_id,)).fetchone()

            # Budget utilization
            project = self.get_project(project_id)
            total_hours = time_result['total_hours'] or 0

            return {
                'task_counts': {row['status']: row['count'] for row in task_stats},
                'total_hours': total_hours,
                'budget': project.budget if project else 0,
                'budget_utilized': (total_hours * 1000) / project.budget * 100 if project and project.budget > 0 else 0
            }

    # ─── TASK CRUD ───────────────────────────────────────────────────────────────

    def create_task(self, project_id: str, title: str, description: str = "",
                    priority: int = 2, assigned_to: Optional[str] = None,
                    due_date: Optional[str] = None, estimated_hours: float = 0,
                    tags: List[str] = None) -> Task:
        """Create a new task"""
        task_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        task = Task(
            id=task_id,
            project_id=project_id,
            title=title,
            description=description,
            status=TaskStatus.TODO.value,
            priority=priority,
            assigned_to=assigned_to,
            due_date=due_date,
            estimated_hours=estimated_hours,
            actual_hours=0,
            tags=json.dumps(tags or []),
            created_at=now,
            updated_at=now,
            completed_at=None
        )

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO tasks (id, project_id, title, description, status, priority,
                                 assigned_to, due_date, estimated_hours, actual_hours, tags,
                                 created_at, updated_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (task.id, task.project_id, task.title, task.description, task.status,
                  task.priority, task.assigned_to, task.due_date, task.estimated_hours,
                  task.actual_hours, task.tags, task.created_at, task.updated_at, task.completed_at))

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()

            if row:
                return Task(**dict(row))
            return None

    def get_tasks(self, project_id: Optional[str] = None, status: Optional[str] = None,
                  assigned_to: Optional[str] = None, priority: Optional[int] = None) -> List[Task]:
        """Get tasks with filters"""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        if assigned_to:
            query += " AND assigned_to = ?"
            params.append(assigned_to)
        if priority:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY priority DESC, due_date ASC, created_at DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [Task(**dict(row)) for row in rows]

    def update_task(self, task_id: str, **kwargs) -> bool:
        """Update task fields"""
        allowed = ['title', 'description', 'status', 'priority', 'assigned_to',
                   'due_date', 'estimated_hours', 'actual_hours', 'tags']
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if not updates:
            return False

        # Handle tags as JSON
        if 'tags' in updates and isinstance(updates['tags'], list):
            updates['tags'] = json.dumps(updates['tags'])

        # If status changed to done, set completed_at
        if updates.get('status') == TaskStatus.DONE.value:
            updates['completed_at'] = datetime.now().isoformat()

        updates['updated_at'] = datetime.now().isoformat()

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [task_id]

        with self._get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE tasks SET {set_clause} WHERE id = ?",
                values
            )
            return cursor.rowcount > 0

    def delete_task(self, task_id: str) -> bool:
        """Delete task and related data"""
        with self._get_connection() as conn:
            # Delete time entries
            conn.execute("DELETE FROM time_entries WHERE task_id = ?", (task_id,))
            # Delete comments
            conn.execute("DELETE FROM task_comments WHERE task_id = ?", (task_id,))
            # Delete task
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0

    def move_task_status(self, task_id: str, new_status: TaskStatus) -> bool:
        """Move task to new status"""
        return self.update_task(task_id, status=new_status.value)

    # ─── TIME TRACKING ───────────────────────────────────────────────────────────

    def log_time(self, task_id: str, hours: float, description: str = "",
                 user_id: Optional[str] = None, date: Optional[str] = None) -> TimeEntry:
        """Log time for a task"""
        entry_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        entry = TimeEntry(
            id=entry_id,
            task_id=task_id,
            user_id=user_id or "system",
            hours=hours,
            description=description,
            date=date or now[:10],
            created_at=now
        )

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO time_entries (id, task_id, user_id, hours, description, date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (entry.id, entry.task_id, entry.user_id, entry.hours,
                  entry.description, entry.date, entry.created_at))

            # Update task actual_hours
            conn.execute("""
                UPDATE tasks SET actual_hours = actual_hours + ? WHERE id = ?
            """, (hours, task_id))

        return entry

    def get_time_entries(self, task_id: Optional[str] = None,
                         user_id: Optional[str] = None,
                         date_from: Optional[str] = None,
                         date_to: Optional[str] = None) -> List[TimeEntry]:
        """Get time entries with filters"""
        query = "SELECT * FROM time_entries WHERE 1=1"
        params = []

        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)

        query += " ORDER BY date DESC, created_at DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [TimeEntry(**dict(row)) for row in rows]

    # ─── DASHBOARD & ANALYTICS ───────────────────────────────────────────────────

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        with self._get_connection() as conn:
            # Task counts by status
            task_counts = conn.execute("""
                SELECT status, COUNT(*) as count FROM tasks GROUP BY status
            """).fetchall()

            # Tasks due today
            today = datetime.now().strftime("%Y-%m-%d")
            due_today = conn.execute(
                "SELECT COUNT(*) as count FROM tasks WHERE due_date = ? AND status != 'done'",
                (today,)
            ).fetchone()['count']

            # Tasks overdue
            overdue = conn.execute("""
                SELECT COUNT(*) as count FROM tasks
                WHERE due_date < ? AND status NOT IN ('done', 'cancelled')
            """, (today,)).fetchone()['count']

            # Total time this week
            week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            weekly_hours = conn.execute(
                "SELECT SUM(hours) as total FROM time_entries WHERE date >= ?",
                (week_start,)
            ).fetchone()['total'] or 0

            # Projects status
            project_counts = conn.execute(
                "SELECT status, COUNT(*) as count FROM projects GROUP BY status"
            ).fetchall()

            return {
                'tasks_by_status': {row['status']: row['count'] for row in task_counts},
                'due_today': due_today,
                'overdue': overdue,
                'weekly_hours': round(weekly_hours, 2),
                'projects_by_status': {row['status']: row['count'] for row in project_counts},
                'total_projects': sum(row['count'] for row in project_counts),
                'total_tasks': sum(row['count'] for row in task_counts)
            }

    def get_user_workload(self, user_id: Optional[str] = None) -> List[Dict]:
        """Get workload by user"""
        with self._get_connection() as conn:
            query = """
                SELECT assigned_to, status, COUNT(*) as count
                FROM tasks
                WHERE assigned_to IS NOT NULL
            """
            params = []

            if user_id:
                query += " AND assigned_to = ?"
                params.append(user_id)

            query += " GROUP BY assigned_to, status"

            rows = conn.execute(query, params).fetchall()

            # Group by user
            workload = {}
            for row in rows:
                user = row['assigned_to']
                if user not in workload:
                    workload[user] = {}
                workload[user][row['status']] = row['count']

            return [{'user': k, 'tasks': v} for k, v in workload.items()]

    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks by title or description"""
        search_term = f"%{query}%"

        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM tasks
                WHERE title LIKE ? OR description LIKE ?
                ORDER BY priority DESC, created_at DESC
            """, (search_term, search_term)).fetchall()

            return [Task(**dict(row)) for row in rows]

    def get_upcoming_tasks(self, days: int = 7) -> List[Task]:
        """Get tasks due in next N days"""
        today = datetime.now()
        future = today + timedelta(days=days)

        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM tasks
                WHERE due_date BETWEEN ? AND ?
                AND status NOT IN ('done', 'cancelled')
                ORDER BY due_date ASC, priority DESC
            """, (today.strftime("%Y-%m-%d"), future.strftime("%Y-%m-%d"))).fetchall()

            return [Task(**dict(row)) for row in rows]


# Global instance
task_manager = TaskManager()
