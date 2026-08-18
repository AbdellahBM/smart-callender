# Academic Structure and School Year Control (Phase 1) Design

## Goal
Allow the school administration to fully control the academic organization without developer intervention, including:
1) complete academic year management,
2) cycle/level hierarchy for primary/secondary/baccalauréat,
3) class and stream definition using existing `Groupe` as the operational "classe",
4) explicit year lifecycle operations (activate, archive, clone structure for a new year).

## Assumptions
- This phase keeps all existing entities (`Utilisateur`, `Seance`, `Reservation`, `Salle`, `Matiere`) and login flows.
- We use one school context in app; no multi-school support yet.
- A class in the admin interface corresponds to one `Groupe` record (as requested).
- Year and hierarchy changes should be non-destructive by default.
- “Groupes” remain the unit consumed by planning (`Seance.groupe_id`).

## Scope (Phase 1)
### In scope
- Full CRUD for academic years.
- Active-year indicator that drives defaults and controls admin UI behavior.
- School-year-specific structure management (cycle -> level -> filière -> classe/groupe).
- Archive/deactivate behavior for years and structure units.
- Clone current structure to initialize a new academic year (without auto student promotion).
- Backward compatibility path for legacy records that existed before this change.

### Out of scope (Phase 1)
- Automated student promotions to next level.
- Full timetable cross-year migration.
- Automatic mass reassignment of teachers by curriculum changes.

## Data model proposal
### New models
1. `SchoolYear`
- Fields: `id`, `libelle` (e.g. `2026-2027`), `date_debut`, `date_fin`, `actif` (bool), `archive` (bool), `created_at`.
- Business rules:
  - Exactly one year is `actif=True` at a time.
  - `archive=True` makes the year read-only for new scheduling operations.

2. `AcademicCycle`
- Fields: `id`, `school_year_id`, `nom` (Primaire/Collège/Lycée), `code`, `ordre`, `actif` (bool).
- A cycle exists inside one academic year.

3. `AcademicLevel`
- Fields: `id`, `academic_cycle_id`, `nom` (ex: `1ère année`, `2ème année`), `code` (ex: `1AP`, `1BAC`), `ordre`, `actif`.
- Represents hierarchy level under a cycle.

### Existing model extension
4. `Filiere` (keep table name, but change UI meaning to stream/option)
- Add `academic_level_id` (FK → `AcademicLevel.id`, nullable for legacy rows initially).
- Add `actif` (bool), `ordre` (int), `archive` (bool).
- `nom`/`code` continue to be used in UI and scheduling relations.

5. `Groupe` (the class)
- Keep semantics as “classe réelle” (`nom` becomes class name, e.g., `2ème BAC S.Maths A`).
- Add `school_year_id` (FK → `SchoolYear.id`, nullable during migration), `actif` (bool), `archive` (bool).
- Existing relation `groupe.filiere_id` remains.

## Domain behavior
1. Year lifecycle
- Admin creates an academic year with label + dates.
- Admin can set one year active.
- When a new year is created and marked active, planning pages and scheduling defaults target that year.
- Archiving a year disables creation of new sessions/classes tied to it in UI.

2. Structure builder
- Admin creates cycle for the active year, then levels, then filières (streams), then classes (groupes).
- Each level can be shown hierarchically.
- Existing legacy data remains readable:
  - items with no year can be shown under “Héritage / Données antérieures”.
  - editing these items invites assignment to a year before scheduling.

3. Class creation and assignment
- `Groupe` creation form always asks for:
  - filière/stream,
  - year,
  - effectif.
- `Utilisateur` (students) remain linked to `Groupe` and therefore implicitly to a year/level through class lineage.

4. Clone for next-year setup
- Admin can run “Cloner vers nouvelle année” from a source year:
  - duplicates cycles and levels
  - duplicates filières under same hierarchy
  - duplicates groupes with `actif=False` and effectif reset to 0 by default (configurable)
  - keeps no timetable/seance link yet.

5. Validation and constraints
- Prevent deleting active year if it still has groups or seances.
- Prevent duplicate class names within same filière/year context (configurable, likely case-insensitive unique suggestion).
- Soft-delete via `archive` to preserve history for audit and rollback.

## Admin UI redesign (existing app)
### New Admin tab: “Organisation scolaire”
- Subsections:
  - “Années scolaires”
  - “Cycles / niveaux / filières”
  - “Classes”
  - “Clonage d’année”
- All changes logged with existing audit logger.
- Tree/crumbles UI:
  - Year → Cycle → Niveau → Filière → Groupe
- Actions available: create/edit/archive/restore/activate year; duplicate year structure.

### Backward-compatibility compatibility mode
- Dashboard and old class lists still open.
- New data entry fields default to active year where possible.
- Admin warning appears when creating/editing legacy entity without year.

## Data flow
- `ResourceService` expands with year-aware read methods:
  - `get_groupes_for_active_year()`
  - `get_filieres_for_active_year()`
  - `get_levels_for_active_year()`
- Scheduler/filter layer uses active `SchoolYear` by default.
- Any operation adding seance links a year through class lineage and stores year consistency checks in service layer.

## Error handling
- Friendly validation errors in French.
- On deletion/archive: confirm impacted counts (classes, users, seances).
- If active year has no structure, prompt admin to bootstrap from default template.

## Testing approach
- Unit tests for model constraints and year-transition rules.
- Service tests for active-year selection and fallback behavior.
- UI tests are lightweight manual at this phase: scenario matrix per user type.

## Acceptance criteria for this phase
- Admin can create/select/archive/duplicate an academic year.
- Admin can manage cycles/levels/filieres/groupes from UI without code changes.
- Existing users (teachers/students/admin) can still open app after upgrade; no startup crash.
- No destructive migration: old data remains usable and recoverable.
- A school year’s structure can be created from prior year as a template in one action.
