# Smart Callender - Intelligent Scheduling System

<div align="center">
  <h3>An intelligent desktop application designed to solve complex scheduling problems for educational institutions.</h3>
</div>

---

**Smart Callender** is an automated timetable management system built for schools, high schools, and universities. By leveraging Constraint Programming (CSP) via Google OR-Tools, it automatically generates conflict-free schedules, optimizing room utilization and teacher workloads.

## 🚀 Why this exists

Scheduling classes manually in any educational institution often leads to:
- Double-booked rooms or teachers.
- Room capacity violations (assigning a large class to a small room).
- Ignoring teacher unavailability preferences.

**Smart Callender** was built to eliminate these headaches. Simply input your resources (Teachers, Rooms, Groups) and constraints, and click **"Generate"**. The solver explores millions of possibilities to deliver a perfect, conflict-free schedule.

## ✨ Key Features

### 1. Intelligent Scheduling (CSP Engine)
- **Automatic Generation**: Creates conflict-free timetables using **Google OR-Tools**.
- **Constraint Handling**:
  - **Hard Constraints**: No double bookings. Room capacity must meet or exceed student group size.
  - **Soft Constraints**: Optimization of resource allocation.
  - **Teacher Availability**: Honors specific unavailability slots requested by teachers.

### 2. Multi-Role Architecture

#### 👑 Administrator (Administration)
- **Dashboard**: Real-time statistics (KPIs) on room usage and teacher workload.
- **Resource Management**: Manage Rooms, Teachers, Classes/Groups, and Subjects.
- **Schedule Management**: 
  - One-click automatic schedule generation.
  - Visual grid view of all schedules.
  - **PDF Export** of timetables for easy distribution.
  - Validate or refuse room reservation requests.

#### 🎓 Teacher
- **Personal Planning**: View their own weekly schedule.
- **Room Reservation**: Submit requests for specific dates/times (e.g., makeup classes, extra sessions).
- **Unavailability**: Declare recurring unavailable slots which the scheduler will respect during the next generation cycle.

#### 🎒 Student
- **Group Planning**: View the schedule for their assigned class/group.
- **Room Search**: Find available rooms for group study or revision.

---

## 📸 Screenshots

*(Add screenshots of the Dashboard, Timetable Grid, and Generation feature here)*

---

## 🛠 Technologies Used

- **Python 3.10+**: Core logic and scripting.
- **Google OR-Tools**: CP-SAT solver for the scheduling engine.
- **Flask & SQLAlchemy**: Application framework (dependency injection) and ORM.
- **SQLite**: Lightweight local database storage.
- **Tkinter & ttk**: Native, responsive desktop GUI.
- **ReportLab**: PDF report generation.
- **Matplotlib**: Embedded data visualization.

---

## ⚡ Installation & Quick Start

### 1. Prerequisites
- **Python 3.10+** installed.

### 2. Clone and Setup Environment

Clone the repository and set up a virtual environment:

**Windows (PowerShell):**
```powershell
git clone https://github.com/yourusername/smart-callender.git
cd smart-callender
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
git clone https://github.com/yourusername/smart-callender.git
cd smart-callender
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize the Demo Database (Manual Setup)
Run the seed script explicitly to initialize the database and demo entities:

```bash
python seed.py
```

⚠️ This script is intentional and destructive for local setup:
it drops and recreates database tables to load demo data. Run it only once
during bootstrap or in a maintenance window.

### 5. Launch the Application
```bash
python desktop_run.py
```

### 6. Demo Credentials

If you ran `python seed.py`, you can log in with the following demo accounts:

| Role       | Email                      | Password  | Note                          |
|------------|----------------------------|-----------|-------------------------------|
| Admin      | `admin@school.edu`         | `password`| Administrator dashboard       |
| Teacher    | `prof.math@school.edu`     | `password`| Math Teacher                  |
| Student    | `student.grade10@school.edu`| `password`| 10th Grade Student            |

---

## 🧠 How the Scheduling Works

The engine (`app/services/scheduler.py`) transforms the timetable problem into a mathematical model:

1.  **Variables**: Every potential class session needs a `(Room, TimeSlot)`.
2.  **Constraints**:
    *   `Sum(Sessions for Teacher T at Time H) <= 1`
    *   `Sum(Sessions in Room R at Time H) <= 1`
    *   `Sum(Sessions for Class C at Time H) <= 1`
    *   `Room Capacity >= Class Size`
    *   `Teacher Unavailability != TimeSlot`
3.  **Solver**: The CP-SAT solver explores the search space to find a feasible solution satisfying all constraints, saving the result to the local SQLite database.

## 🤝 Contributing

Contributions are welcome! Feel free to submit a Pull Request or open an Issue if you have ideas on how to improve the scheduling algorithms, UI, or overall architecture.

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
