# Phase 1 Release Notes: Academic Structure and School-Year Control

## For school administration

Smart Callender now lets the direction manage the school structure from the desktop application. Technical support is no longer required to create a new academic year, adapt the school's levels, or prepare the next year.

Open `Organisation scolaire` from the administrator dashboard to manage the following hierarchy:

1. Academic year
2. Cycle: for example Primaire, Collège, Lycée, or Baccalauréat
3. Level: for example 6AP, 3AC, TC, 1BAC, or 2BAC
4. Stream or section
5. Class group

The class group remains the unit used for schedules, enrolment counts, students, and lessons.

## New administration controls

- Create an academic year and make it active.
- Keep a single active operational year at a time.
- Add, edit, archive, or reopen cycles, levels, streams, and classes.
- Duplicate a complete year structure to prepare the following year.
- Choose whether the cloned classes retain their enrolment counts.
- Review these operations in the administration audit journal.

Archive is the recommended way to remove an item from daily use. It preserves historical schedule data while removing the archived item and its descendants from active resource lists and timetable generation.

## Planning behavior

Automatic scheduling, the timetable display, and PDF timetable export now use lessons attached to classes in the active academic year. This prevents an old school year's lessons from appearing in the current timetable.

## Upgrade and startup behavior

On desktop-app startup, Smart Callender creates missing academic-structure tables and columns without deleting existing school records. If no academic year exists, it creates one using the current calendar year label. The administrator can then rename, activate, or configure it from `Organisation scolaire`.

## Demo database

The demo script is still destructive and intended only for bootstrap or controlled maintenance:

```bash
python scripts/seed_db.py
```

It creates an active academic year, a Collège/Lycée demo hierarchy, nine linked classes, and demo accounts. Do not run it on a production school database.
