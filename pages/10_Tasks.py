"""
Task Management - Full CRUD with Projects, Time Tracking, Dashboard
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add engine to path
ENGINE_DIR = Path(__file__).parent.parent / "engine"
sys.path.insert(0, str(ENGINE_DIR))

from task_manager import TaskManager, TaskStatus, TaskPriority, ProjectStatus

st.set_page_config(page_title="RAGSPRO - Task Management", page_icon="✅", layout="wide")

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.main { font-family: 'Inter', sans-serif; }

.task-card {
    background: white;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.task-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transform: translateY(-1px);
    transition: all 0.2s;
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.status-todo { background: #f3f4f6; color: #6b7280; }
.status-in_progress { background: #dbeafe; color: #2563eb; }
.status-review { background: #fef3c7; color: #d97706; }
.status-done { background: #d1fae5; color: #059669; }
.status-cancelled { background: #fee2e2; color: #dc2626; }

.priority-urgent { color: #dc2626; }
.priority-high { color: #ea580c; }
.priority-medium { color: #ca8a04; }
.priority-low { color: #6b7280; }

.project-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.25rem;
    border-radius: 12px;
    margin-bottom: 1rem;
}

.project-card h4 { margin: 0 0 0.5rem 0; }
.project-card p { margin: 0; opacity: 0.9; font-size: 0.9rem; }

.metric-card {
    background: white;
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
    border: 1px solid #e5e7eb;
}

.metric-card .value {
    font-size: 2rem;
    font-weight: 700;
    color: #1f2937;
}

.metric-card .label {
    font-size: 0.8rem;
    color: #6b7280;
    text-transform: uppercase;
}

.overdue { color: #dc2626; font-weight: 600; }
.due-soon { color: #ea580c; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Initialize task manager
@st.cache_resource
def get_task_manager():
    return TaskManager()

tm = get_task_manager()

# ─── Header ───────────────────────────────────────────────────────────────────

st.title("✅ Task Management")

# ─── Dashboard Stats ──────────────────────────────────────────────────────────

st.subheader("📊 Dashboard")
stats = tm.get_dashboard_stats()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_tasks = stats.get('total_tasks', 0)
    st.markdown(f"""
    <div class='metric-card'>
        <div class='value'>{total_tasks}</div>
        <div class='label'>Total Tasks</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    done = stats.get('tasks_by_status', {}).get('done', 0)
    st.markdown(f"""
    <div class='metric-card'>
        <div class='value' style='color: #10b981;'>{done}</div>
        <div class='label'>Completed</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    in_progress = stats.get('tasks_by_status', {}).get('in_progress', 0)
    st.markdown(f"""
    <div class='metric-card'>
        <div class='value' style='color: #3b82f6;'>{in_progress}</div>
        <div class='label'>In Progress</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    due_today = stats.get('due_today', 0)
    st.markdown(f"""
    <div class='metric-card'>
        <div class='value' style='color: #f59e0b;'>{due_today}</div>
        <div class='label'>Due Today</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    overdue = stats.get('overdue', 0)
    st.markdown(f"""
    <div class='metric-card'>
        <div class='value' style='color: #ef4444;'>{overdue}</div>
        <div class='label'>Overdue</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ─── Main Tabs ────────────────────────────────────────────────────────────────

tab_tasks, tab_projects, tab_time, tab_analytics = st.tabs([
    "📝 Tasks", "📁 Projects", "⏱️ Time Tracking", "📈 Analytics"
])

# ─── TASKS TAB ─────────────────────────────────────────────────────────────────

with tab_tasks:
    # Filters
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        status_filter = st.selectbox("Status", ["All"] + [s.value for s in TaskStatus], key="task_status_filter")
    with filter_col2:
        priority_filter = st.selectbox("Priority", ["All", "Urgent", "High", "Medium", "Low"], key="task_priority_filter")
    with filter_col3:
        projects = tm.get_projects()
        project_options = ["All"] + [p.name for p in projects]
        project_filter = st.selectbox("Project", project_options, key="task_project_filter")
    with filter_col4:
        search_query = st.text_input("🔍 Search tasks", placeholder="Search...", key="task_search")

    # Get filtered tasks
    status_param = None if status_filter == "All" else status_filter
    priority_map = {"Urgent": 4, "High": 3, "Medium": 2, "Low": 1}
    priority_param = priority_map.get(priority_filter) if priority_filter != "All" else None

    project_id_param = None
    if project_filter != "All":
        for p in projects:
            if p.name == project_filter:
                project_id_param = p.id
                break

    if search_query:
        tasks = tm.search_tasks(search_query)
    else:
        tasks = tm.get_tasks(
            project_id=project_id_param,
            status=status_param,
            priority=priority_param
        )

    # Quick Add Task
    with st.expander("➕ Quick Add Task", expanded=False):
        with st.form("quick_add_task"):
            qa_col1, qa_col2, qa_col3 = st.columns([2, 1, 1])

            with qa_col1:
                task_title = st.text_input("Task Title", placeholder="What needs to be done?")
                task_desc = st.text_area("Description", placeholder="Add details...", height=80)

            with qa_col2:
                if projects:
                    task_project = st.selectbox("Project", [p.name for p in projects])
                else:
                    task_project = None
                    st.info("Create a project first")

                task_priority = st.selectbox("Priority", ["High", "Medium", "Low", "Urgent"])

            with qa_col3:
                task_due = st.date_input("Due Date", value=datetime.now() + timedelta(days=7))
                task_hours = st.number_input("Est. Hours", min_value=0.0, step=0.5, value=1.0)

            submitted = st.form_submit_button("✅ Create Task", type="primary", use_container_width=True)

            if submitted and task_title and task_project:
                project_id = next((p.id for p in projects if p.name == task_project), None)
                if project_id:
                    priority_val = priority_map.get(task_priority, 2)
                    tm.create_task(
                        project_id=project_id,
                        title=task_title,
                        description=task_desc,
                        priority=priority_val,
                        due_date=task_due.strftime("%Y-%m-%d"),
                        estimated_hours=task_hours
                    )
                    st.success("✅ Task created!")
                    st.rerun()

    # Display Tasks
    st.subheader(f"Tasks ({len(tasks)})")

    if tasks:
        for task in tasks:
            # Task card
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 0.5])

            with col1:
                priority_class = f"priority-{['low', 'medium', 'high', 'urgent'][task.priority - 1]}"
                status_class = f"status-{task.status}"

                # Check if overdue
                due_warning = ""
                if task.due_date and task.status not in ['done', 'cancelled']:
                    due = datetime.strptime(task.due_date, "%Y-%m-%d")
                    if due < datetime.now():
                        due_warning = "<span class='overdue'>⚠️ OVERDUE</span>"
                    elif (due - datetime.now()).days <= 2:
                        due_warning = "<span class='due-soon'>⚡ DUE SOON</span>"

                st.markdown(f"""
                <div class='task-card'>
                    <div style='display: flex; align-items: center; gap: 0.5rem;'>
                        <span class='{priority_class}'>●</span>
                        <strong>{task.title}</strong>
                        <span class='status-badge {status_class}'>{task.status.replace('_', ' ')}</span>
                        {due_warning}
                    </div>
                    <div style='color: #6b7280; font-size: 0.85rem; margin-top: 0.25rem;'>
                        {task.description[:100]}{'...' if len(task.description) > 100 else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.caption(f"📅 {task.due_date or 'No due date'}")

            with col3:
                progress = min((task.actual_hours / task.estimated_hours * 100) if task.estimated_hours > 0 else 0, 100)
                st.caption(f"⏱️ {task.actual_hours:.1f}h / {task.estimated_hours:.1f}h")
                st.progress(progress / 100)

            with col4:
                # Status change buttons
                new_status = st.selectbox(
                    "Status",
                    [s.value for s in TaskStatus],
                    index=[s.value for s in TaskStatus].index(task.status) if task.status in [s.value for s in TaskStatus] else 0,
                    key=f"status_{task.id}"
                )
                if new_status != task.status:
                    tm.update_task(task.id, status=new_status)
                    st.rerun()

            with col5:
                if st.button("🗑️", key=f"delete_{task.id}"):
                    tm.delete_task(task.id)
                    st.rerun()

            # Task actions expander
            with st.expander("Actions", expanded=False):
                action_col1, action_col2 = st.columns(2)

                with action_col1:
                    # Log time
                    with st.form(f"log_time_{task.id}"):
                        st.write("⏱️ Log Time")
                        hours = st.number_input("Hours", min_value=0.1, step=0.5, value=1.0, key=f"hours_{task.id}")
                        desc = st.text_input("Description", placeholder="What did you work on?", key=f"desc_{task.id}")
                        if st.form_submit_button("Log Time"):
                            tm.log_time(task.id, hours, desc)
                            st.success("Time logged!")
                            st.rerun()

                with action_col2:
                    # Edit task
                    with st.form(f"edit_{task.id}"):
                        st.write("✏️ Edit Task")
                        new_title = st.text_input("Title", value=task.title, key=f"title_{task.id}")
                        new_priority = st.selectbox("Priority", [1, 2, 3, 4],
                                                     index=task.priority - 1,
                                                     format_func=lambda x: ["Low", "Medium", "High", "Urgent"][x-1],
                                                     key=f"pri_{task.id}")
                        if st.form_submit_button("Update"):
                            tm.update_task(task.id, title=new_title, priority=new_priority)
                            st.rerun()
    else:
        st.info("No tasks found. Create your first task above!")

    # Upcoming Tasks
    st.divider()
    st.subheader("📅 Upcoming (Next 7 Days)")
    upcoming = tm.get_upcoming_tasks(days=7)

    if upcoming:
        up_df = st.dataframe(
            data=[{
                "Task": t.title,
                "Due": t.due_date,
                "Priority": ["Low", "Medium", "High", "Urgent"][t.priority - 1],
                "Status": t.status
            } for t in upcoming],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No upcoming tasks")

# ─── PROJECTS TAB ─────────────────────────────────────────────────────────────

with tab_projects:
    proj_col1, proj_col2 = st.columns([1, 2])

    with proj_col1:
        st.subheader("📁 Projects")

        # Add Project
        with st.form("add_project"):
            st.write("➕ New Project")
            proj_name = st.text_input("Project Name", placeholder="e.g., Website Redesign")
            proj_desc = st.text_area("Description", placeholder="Project details...")
            proj_budget = st.number_input("Budget (₹)", min_value=0, step=10000, value=0)
            proj_due = st.date_input("Due Date", value=datetime.now() + timedelta(days=30))

            if st.form_submit_button("Create Project", type="primary"):
                if proj_name:
                    tm.create_project(
                        name=proj_name,
                        description=proj_desc,
                        budget=proj_budget,
                        due_date=proj_due.strftime("%Y-%m-%d")
                    )
                    st.success("✅ Project created!")
                    st.rerun()

        # Project list
        st.divider()
        projects = tm.get_projects()

        for proj in projects:
            # Get project stats
            proj_tasks = tm.get_tasks(project_id=proj.id)
            completed = len([t for t in proj_tasks if t.status == 'done'])
            total = len(proj_tasks)

            status_color = {
                'active': '#10b981',
                'on_hold': '#f59e0b',
                'completed': '#3b82f6',
                'cancelled': '#ef4444'
            }.get(proj.status, '#6b7280')

            st.markdown(f"""
            <div style='background: white; border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem; border-left: 4px solid {status_color};'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <strong>{proj.name}</strong>
                    <span style='color: {status_color}; font-size: 0.75rem; text-transform: uppercase;'>{proj.status}</span>
                </div>
                <div style='color: #6b7280; font-size: 0.85rem; margin-top: 0.25rem;'>
                    {proj.description[:60]}{'...' if len(proj.description) > 60 else ''}
                </div>
                <div style='margin-top: 0.5rem; font-size: 0.8rem; color: #6b7280;'>
                    ✅ {completed}/{total} tasks | 💰 {proj.budget:,} | 📅 {proj.due_date or 'No deadline'}
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Manage"):
                new_status = st.selectbox("Status", [s.value for s in ProjectStatus], key=f"proj_status_{proj.id}")
                if st.button("Update Status", key=f"update_proj_{proj.id}"):
                    tm.update_project(proj.id, status=new_status)
                    st.rerun()
                if st.button("🗑️ Delete Project", key=f"del_proj_{proj.id}"):
                    tm.delete_project(proj.id)
                    st.rerun()

    with proj_col2:
        # Project Analytics
        if projects:
            st.subheader("📈 Project Analytics")

            # Project status distribution
            status_counts = {}
            for p in projects:
                status_counts[p.status] = status_counts.get(p.status, 0) + 1

            st.bar_chart(status_counts)

            # Task completion by project
            st.subheader("Task Completion Rate")
            completion_data = {}
            for proj in projects:
                proj_tasks = tm.get_tasks(project_id=proj.id)
                if proj_tasks:
                    completed = len([t for t in proj_tasks if t.status == 'done'])
                    completion_data[proj.name[:20]] = (completed / len(proj_tasks)) * 100

            if completion_data:
                st.bar_chart(completion_data)

# ─── TIME TRACKING TAB ─────────────────────────────────────────────────────────

with tab_time:
    time_col1, time_col2 = st.columns([1, 2])

    with time_col1:
        st.subheader("⏱️ Log Time")

        # Quick time log
        all_tasks = tm.get_tasks(status='in_progress')
        if all_tasks:
            with st.form("log_time"):
                task_options = {f"{t.title} ({t.id})": t.id for t in all_tasks}
                selected_task = st.selectbox("Task", list(task_options.keys()))
                hours = st.number_input("Hours", min_value=0.1, step=0.5, value=1.0)
                desc = st.text_input("Description", placeholder="What did you work on?")
                date = st.date_input("Date", value=datetime.now())

                if st.form_submit_button("Log Time", type="primary"):
                    task_id = task_options[selected_task]
                    tm.log_time(task_id, hours, desc, date=date.strftime("%Y-%m-%d"))
                    st.success("✅ Time logged!")
                    st.rerun()
        else:
            st.info("No in-progress tasks. Start a task to log time!")

    with time_col2:
        st.subheader("📊 Time Report (Last 30 Days)")

        # Get time entries
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        entries = tm.get_time_entries(date_from=from_date)

        if entries:
            # Group by date
            daily_hours = {}
            for e in entries:
                date = e.date
                daily_hours[date] = daily_hours.get(date, 0) + e.hours

            # Sort by date
            dates = sorted(daily_hours.keys())
            chart_data = {d: daily_hours[d] for d in dates}

            st.line_chart(chart_data)

            # Total hours
            total_hours = sum(e.hours for e in entries)
            st.metric("Total Hours (30 days)", f"{total_hours:.1f}h")
        else:
            st.info("No time entries in the last 30 days")

# ─── ANALYTICS TAB ─────────────────────────────────────────────────────────────

with tab_analytics:
    st.subheader("📊 Team Workload")

    workload = tm.get_user_workload()
    if workload:
        for item in workload:
            user = item['user']
            tasks = item['tasks']
            total = sum(tasks.values())

            st.write(f"**{user}**: {total} tasks")
            cols = st.columns(len(tasks))
            for i, (status, count) in enumerate(tasks.items()):
                with cols[i]:
                    st.metric(status.replace('_', ' ').title(), count)
    else:
        st.info("No assigned tasks yet")

    st.divider()

    st.subheader("📈 Task Status Distribution")
    status_data = stats.get('tasks_by_status', {})
    if status_data:
        st.bar_chart(status_data)
    else:
        st.info("No task data yet")

st.divider()
st.caption("💡 Tip: Use the sidebar to navigate between different sections of Agency OS")
