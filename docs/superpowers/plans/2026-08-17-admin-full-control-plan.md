# Smart Callender Full Admin Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give school direction complete non-developer control over scheduling parameters and administrative resources (users, rooms, classes, teachers, students) via in-app workflows.

**Architecture:** Keep Tkinter as the primary client while making services own business rules and settings state, with ORM models owning persisted school configuration.

**Tech Stack:** Python 3.10+, Tkinter/ttkbootstrap, Flask-SQLAlchemy, OR-Tools.

**Global Constraints**
- Branch currently used: `admin-full-control`.
- Maintain backward compatibility with existing models (`Utilisateur`, `Seance`, `Reservation`) and preserve current login flow.
- No automatic destructive DB reset in application startup; seed data remains an explicit admin/dev action.
- Keep each GUI change incremental and reviewable (small modules, feature-scoped commits).

---

### Task 1: Foundation — DB-driven scheduling settings + safe defaults

**Files:**
- Create: `app/models/school_setting.py`
- Modify: `app/models/__init__.py`
- Create: `app/services/settings_service.py`
- Modify: `app/services/scheduler.py`
- Modify: `app/services/room_service.py`
- Modify: `app/gui/main.py`
- Modify: `app/gui/schedule_ui.py`
- Modify: `app/desktop_run.py`

**Interfaces:**
- Consumes: SQLAlchemy `db` session and existing `config` defaults.
- Produces: `SchoolSettingsService.get_working_days()`, `SchoolSettingsService.get_slot_times()`, `SchoolSettingsService.get_slot_duration_minutes()`, and a refactored `SchedulerService.generate_slots()` interface that reads DB settings instead of hardcoded values.

- [ ] **Step 1: Add SchoolSetting model and service contracts**
  - Implement durable settings storage via `SchoolSetting(key, value)`.
  - Implement `SchoolSettingsService` with methods:
    - `seed_default_settings()`
    - `get_value(key, default=None)`
    - `set_value(key, value)`
    - `get_working_days()` returns `list[int]`
    - `get_slot_times()` returns `list[str]`
    - `get_slot_duration_minutes()` returns `int`
    - `get_slot_starts_as_time_pairs()` returns `list[tuple[int,int]]`

- [ ] **Step 2: Wire defaults into startup path**
  - Replace automatic full seeding on startup with safe default bootstrapping:
    - ensure tables exist,
    - ensure settings defaults exist,
    - do not drop existing DB.

- [ ] **Step 3: Refactor scheduler input generation**
  - Replace hardcoded `start_times` and slot duration with values from `SchoolSettingsService`.
  - Add `SchedulerService.generate_slots()` and make `generate_schedule()` use it.
  - Keep fallback defaults equivalent to current behavior when settings are missing.

- [ ] **Step 4: Use settings in availability checks and display**
  - Update room availability and timetable display logic to use configured working days.
  - Replace fixed day labels in `ScheduleFrame` with settings-backed names.

- [ ] **Step 5: Commit this baseline step**
```bash

git add app/models/school_setting.py app/models/__init__.py app/services/settings_service.py app/services/scheduler.py app/services/room_service.py app/gui/main.py app/gui/schedule_ui.py docs/superpowers/plans/2026-08-17-admin-full-control-plan.md
git commit -m "feat: add DB-driven scheduling settings and remove startup seed reset"
```

### Task 2: Admin control panel for operational parameters

**Files:**
- Modify: `app/gui/admin.py`
- Modify: `app/services/resource_service.py`
- Modify: `app/gui/main.py` (navigation and role-based access where needed)

**Interfaces:**
- Consumes: `SchoolSettingsService` methods from Task 1.
- Produces: admin-driven runtime edit of working days, slot starts, slot duration, and system-wide scheduling behavior.

- [ ] **Step 1: Add settings tab to admin dashboard**
  - Add form fields for working days, slot starts, duration, and optional safety parameters.
  - Validate and persist values via `SchoolSettingsService`.

- [ ] **Step 2: Add lightweight feedback and refresh hooks**
  - Show success/error messages, and reload schedule view after settings save.

- [ ] **Step 3: Commit this control-plane step**
```bash

git add app/gui/admin.py app/services/resource_service.py
git commit -m "feat: add admin settings UI to control schedule parameters"
```

### Task 3: Operational hardening and admin user journey

**Files:**
- Modify: `scripts/seed_db.py`
- Modify: `desktop_run.py`, `app/models/__init__.py`, admin-facing helpers

**Interfaces:**
- Consumes: existing seed script and bootstrap behavior from Task 1.
- Produces: explicit manual-seed model and cleaner no-dev operational onboarding.

- [ ] **Step 1: Make seed/manual setup explicit**
  - Keep seed as explicit script only; remove implicit production startup seeding.
  - Add startup guidance if DB is empty (admin setup needed).

- [ ] **Step 2: Run one final cleanup pass over admin-controlled paths**
  - Remove hardcoded values from services remaining after Task 1.

- [ ] **Step 3: Commit this hardening step**
```bash
git add scripts/seed_db.py desktop_run.py app/models/__init__.py
git commit -m "chore: remove implicit startup seeding and improve explicit onboarding path"
```

