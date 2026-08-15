# Smart Callender - University Timetable Management System

Smart Callender is an intelligent desktop application designed to manage university schedules. It leverages Object-Oriented Programming (OOP) principles in Python and uses a Constraint Satisfaction Problem (CSP) solver to automatically generate and optimize timetables.

The application features a "Fat Client" architecture with a native Tkinter GUI and a Flask/SQLAlchemy backend layer for data management.

## 🚀 Key Features

### 1. Intelligent Scheduling (CSP)
- **Automatic Generation**: Creates conflict-free timetables using **Google OR-Tools**.
- **Constraint Handling**:
  - **Hard Constraints**: No double bookings for rooms, teachers, or student groups. Room capacity must meet group size.
  - **Soft Constraints**: Optimization of resource allocation.
- **Conflict Detection**: Real-time validation of manual changes.

### 2. Multi-Role Architecture
The application provides tailored interfaces for three user profiles:

#### 👑 Administrator
- **Dashboard**: Real-time statistics (KPIs) on room usage, teacher load, and pending requests.
- **Resource Management**: CRUD operations for Rooms, Teachers, Groups, and Subjects.
- **Schedule Management**: 
  - One-click automatic schedule generation.
  - Visual grid view of all schedules.
  - **PDF Export** of timetables.
- **Reservations**: Validate or refuse room reservation requests from teachers.

#### 🎓 Teacher
- **Personal Planning**: View their own weekly schedule.
- **Room Reservation**: Submit requests for specific dates/times (e.g., makeup classes).
- **Unavailability**: Declare recurring unavailable slots (e.g., "Not available Monday mornings") which the scheduler respects.
- **Search**: Find free rooms for spontaneous needs.

#### 🎒 Student
- **Group Planning**: View the schedule for their assigned group.
- **Room Search**: Find available rooms for group study or revision.

---

## 🛠 Technologies Used

### Core Logic & Backend
- **Python 3.10+**: Core language.
- **Flask**: Used as an Application Framework (Dependency Injection, Config).
- **SQLAlchemy**: ORM for database interactions.
- **SQLite**: Local database storage.
- **Google OR-Tools**: CP-SAT solver for the scheduling engine.

### Graphical User Interface (GUI)
- **Tkinter**: Native Python GUI toolkit.
- **Tkinter.ttk**: Themed widgets for a modern look.
- **tkcalendar**: Date pickers for reservation forms.
- **Matplotlib**: Embedded charts for statistics.

### Utilities
- **ReportLab**: PDF generation.
- **Pandas**: Data handling for exports.

---

## 📂 Project Structure

```text
smart-callender/
├── app/
│   ├── models/           # Database Models (OOP)
│   │   ├── utilisateur.py   # User & Roles
│   │   ├── seance.py        # Schedule Session
│   │   ├── salle.py         # Room Resource
│   │   └── ...
│   ├── services/         # Business Logic Layer
│   │   ├── auth_service.py      # Login/Auth Logic
│   │   ├── resource_service.py  # CRUD Operations
│   │   └── scheduler.py         # OR-Tools CSP Engine
│   ├── gui/              # Presentation Layer (Tkinter)
│   │   ├── main.py          # Main Window & Router
│   │   ├── auth.py          # Login Screen
│   │   ├── admin.py         # Admin Dashboard
│   │   ├── teacher.py       # Teacher Portal
│   │   └── student.py       # Student Portal
│   ├── __init__.py       # App Factory
│   └── extensions.py     # DB, Migration, Login Setup
├── scripts/              # Utility & maintenance scripts
│   └── seed_db.py         # Original DB seeding logic
├── instance/             # Local Database Storage
├── my_config.py          # App configuration (DB URL, secret key, etc.)
├── desktop_run.py        # Application Entry Point
├── seed.py               # Database Initialization Script (calls scripts/seed_db logic)
└── requirements.txt      # Dependency List
```

---

## ⚡ How to Run (with venv)

The application runs with **Python in a virtual environment (venv)**. Use these steps yourself or share them with your professor.

### 1. Prerequisites
- **Python 3.10+** installed.

### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
cd path\to\smart-callender
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
cd path\to\smart-callender
python -m venv venv
venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
cd path/to/smart-callender
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
With the venv activated:

```bash
pip install -r requirements.txt
```

### 4. Initialize the database
Run the seed script to create the database and sample data (admin, teachers, rooms, etc.):

```bash
python seed.py
```

### 5. Launch the application
Start the desktop application:

```bash
python desktop_run.py
```

### 6. User credentials (from `seed.py`)

After running `python seed.py`, you can log in with these accounts:

| Role       | Email                   | Password  | Note                          |
|------------|-------------------------|-----------|-------------------------------|
| Admin      | `admin@test.com`        | `password`| Administrator                 |
| Teacher    | `benjelloun@univ.ma`    | `password`| Prof. Math (SMI)              |
| Teacher    | `elamrani@univ.ma`      | `password`| Prof. Info (SMI)              |
| Student    | `etudiant.smi@univ.ma`  | `password`| Student in SMI S1             |

**To share with your professor (do not send the whole folder with venv):**

1. **Create a zip without venv:** Double-click `prepare_zip_for_professor.bat` (or run `prepare_zip_for_professor.ps1` in PowerShell). This creates `SmartCallender_pour_prof.zip` in the parent folder (e.g. Desktop), excluding `venv`, `__pycache__`, and the local database.
2. Send the zip file to the professor (email, USB, etc.).
3. Give them the short instructions in `POUR_LE_PROFESSEUR.txt` (or point them to this README). They unzip, then: create venv → activate → `pip install -r requirements.txt` → `python seed.py` → `python desktop_run.py`.

---

## 🧠 How the Scheduling Works

The `SchedulerService` (`app/services/scheduler.py`) transforms the timetable problem into a mathematical model:

1.  **Variables**: Every potential class session is a variable that needs to be assigned a `(Room, TimeSlot)`.
2.  **Constraints**:
    *   `Sum(Sessions for Teacher T at Time H) <= 1`
    *   `Sum(Sessions in Room R at Time H) <= 1`
    *   `Sum(Sessions for Group G at Time H) <= 1`
    *   `Room Capacity >= Group Size`
    *   `Teacher Unavailability != TimeSlot`
3.  **Solver**: The CP-SAT solver explores millions of possibilities to find a feasible solution that satisfies all constraints, then saves the result to the database.

---

## 📘 Understanding the CSP Engine

**CSP** stands for **Constraint Satisfaction Problem**. It is a mathematical approach used to solve problems where you have a set of **variables** that must be assigned **values**, but those assignments must obey a set of strict **constraints** (rules).

Think of it like a Sudoku puzzle:
- **Variables**: The empty cells you must fill.
- **Domain**: The possible values (e.g. numbers 1–9).
- **Constraints**: No duplicate in any row, column, or 3×3 box.

### How the CSP engine works in this app

The scheduler uses **Google OR-Tools** (`app/services/scheduler.py`).

1. **Variables (what we decide)**  
   For each **session** (e.g. “Math for Group A with Prof. Turing”), the engine creates variables to decide:
   - **TimeSlot**: When it happens (e.g. Monday 8:30).
   - **Room**: Where it happens (e.g. Room 101).

2. **Constraints (the rules)**  
   The engine is told what is allowed and what is forbidden:
   - **Teacher conflict**: A teacher cannot be in two rooms at the same time.
   - **Room conflict**: A room cannot host two sessions at the same time.
   - **Group conflict**: A student group cannot have two sessions at the same time.
   - **Capacity**: Room capacity must be at least the group size.
   - **Unavailability**: If a teacher marks “Monday morning” as unavailable, those slots are forbidden for that teacher.

3. **Solver**  
   When you click “Generate”, the solver explores many possible combinations, discards those that violate any constraint, and returns a valid assignment (if one exists). That result is then saved to the database.

---

## 📁 Why These Files Exist

### `my_config.py`

This file holds the **configuration** of the application (database URL, secret key, debug mode, etc.).

- **Why it exists**: Flask needs a single place to read settings such as where the database is, whether debug is on, and security keys.
- **Why the name**: The usual name is `config.py`. Here it is `my_config.py` to avoid import conflicts with other modules or system paths (e.g. on Windows), so the app always loads the right configuration.
- **What’s inside**: For example `SQLALCHEMY_DATABASE_URI` (path to `smart_callender.db`), `SECRET_KEY`, and options like `SLOT_DURATION_MINUTES` for the scheduler.

### `scripts/`

This folder is for **utility and maintenance scripts**, separate from the main application code in `app/`.

- **Purpose**: Keeps helper scripts (seeding, backups, resets) out of the core app and makes the project structure clearer.
- **Content**: `seed_db.py` contains the original logic to create and fill the database (admin, teachers, rooms, etc.). The root-level `seed.py` calls this logic so you can run `python seed.py` easily; keeping `scripts/` allows you to add other scripts later (e.g. `reset_db.py`, `backup_db.py`) without cluttering the project root.
