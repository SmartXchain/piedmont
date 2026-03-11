# Data Model Reference

Full reference for the Piedmont database schema. For the high-level overview see `CLAUDE.md`.

---

## Core Chain

The central chain that drives work order travelers:

```
Standard ──► StandardProcess
    │               │
    └──► Classification ◄──────────────┐
              │                        │
              ▼                        │
         Process  ──────────── (unique per Standard + Classification)
              │
              ▼
         ProcessStep  (ordered list, step_number ≥ 1)
              │
              ▼
           Method
              │
              ▼
    ParameterToBeRecorded  (auto-created from ParameterTemplate)
```

---

## App: `standard`

### `Standard`
The top-level aerospace specification (e.g., AMS 2400, BAC 5719).

| Field | Type | Notes |
|---|---|---|
| `name` | CharField | Spec name |
| `description` | TextField | |
| `revision` | CharField | Changing this triggers `requires_process_review = True` on save |
| `author` | CharField | |
| `nadcap` | BooleanField | Whether NADCAP-certified |
| `upload_file` | FileField | PDF of the spec |
| `previous_version` | FK(self) | Links to prior revision |
| `requires_process_review` | BooleanField | Auto-set when revision changes |

Unique constraint: `(name, revision)`.

### `StandardProcess`
A named process block within a standard (e.g., "Alkaline Clean", "Cadmium Plate"). One standard can have multiple process blocks.

| Field | Type | Notes |
|---|---|---|
| `standard` | FK(Standard) | CASCADE |
| `process_type` | CharField (choices) | anodize, clean, electroplate, strip, etc. |
| `title` | CharField | Operator-facing label |
| `notes` | TextField | Local limits for this block |

Unique constraint: `(standard, title)`.

### `Classification`
Method/class/type breakdown within a standard (e.g., Type I, Class 2, Method A). Can be scoped to a specific `StandardProcess`.

| Field | Type | Notes |
|---|---|---|
| `standard` | FK(Standard, null=True) | CASCADE |
| `standard_process` | FK(StandardProcess, null=True) | SET_NULL — scopes to a sub-process |
| `method` | CharField | |
| `class_name` | CharField | |
| `type` | CharField | |
| `strike_asf` | DecimalField | Amps per square foot for strike step |
| `plate_asf` | DecimalField | Amps per square foot for plating step |
| `plating_time_minutes` | PositiveIntegerField | |

### `InspectionRequirement`
Acceptance criteria tied to a standard, optionally scoped to a `StandardProcess`.

### `PeriodicTest`
Periodic test requirements at the standard level (salt spray, solution analysis, etc.).

### `PeriodicTestResult`
Execution log for a `PeriodicTest` (pass/fail, date, notes).

### `StandardPeriodicRequirement`
Maps a `Standard` to a `tank_controls.PeriodicTestSpec`. One spec can satisfy multiple standards.

### `StandardRevisionNotification`
Alert record created when a standard revision changes.

---

## App: `methods`

### `Method`
A single reusable work step. Referenced by `ProcessStep`.

| Field | Type | Notes |
|---|---|---|
| `method_type` | CharField (choices) | `processing_tank` or `manual_method` |
| `title` | CharField | Unique |
| `category` | CharField (choices) | Maps to NADCAP process categories; triggers auto-param creation |
| `description` | TextField | Operator-facing work instruction |
| `tank_name` | CharField | |
| `temp_min / temp_max` | PositiveIntegerField | °F |
| `immersion_time_min/max` | PositiveIntegerField | minutes |
| `touch_time_min/max` | PositiveIntegerField | minutes |
| `run_time_min/max` | PositiveIntegerField | minutes |
| `chemical` | CharField | Bath chemistry callout |
| `is_rectified` | BooleanField | Uses a rectifier (triggers amps calc on WorkOrder) |
| `is_strike_etch` | BooleanField | Strike / activation step prior to plating |
| `is_masking_operation` | BooleanField | |
| `is_stress_relief_operation` | BooleanField | |
| `is_hydrogen_relief_operation` | BooleanField | |

**Key behavior:** When `category` is set (or changed), `save()` auto-creates `ParameterToBeRecorded` rows from `ParameterTemplate`.

### `ParameterTemplate`
Master template: what the operator must record for each process category. One template per category (unique constraint).

### `ParameterToBeRecorded`
Per-method rows printed as blank lines on the traveler. Auto-created from `ParameterTemplate`. Unique on `(method, description)`.

---

## App: `process`

### `Process`
A unique combination of `Standard` + `Classification` that has an ordered list of steps.

| Field | Type | Notes |
|---|---|---|
| `standard` | FK(Standard) | CASCADE |
| `standard_process` | FK(StandardProcess) | CASCADE — **risk: deleting StandardProcess cascades here** |
| `classification` | FK(Classification, null=True) | SET_NULL |
| `is_template` | BooleanField | If True, prints as untracked template (not a Work Order) |

DB constraints enforce one Process per `(standard, classification)` pair, with separate constraints for classified and unclassified.

### `ProcessStep`
An ordered step within a `Process`, pointing to a `Method`.

| Field | Type | Notes |
|---|---|---|
| `process` | FK(Process) | CASCADE |
| `method` | FK(Method) | CASCADE |
| `step_number` | PositiveIntegerField | ≥ 1, unique per process |

---

## App: `part`

### `Part`
A part number with optional revision.

| Field | Type | Notes |
|---|---|---|
| `part_number` | CharField | |
| `part_description` | CharField | |
| `part_revision` | CharField (null) | |

Unique on `(part_number, part_revision)`.

### `PartStandard`
Maps a `Part` to a `Standard` (+ optional `Classification`). Tracks which specs apply to a part.

### `WorkOrder`
A single job run: part + standard + classification + work order number.

| Field | Type | Notes |
|---|---|---|
| `part` | FK(Part) | CASCADE |
| `work_order_number` | CharField | Same WO# can appear multiple times for different standards |
| `standard` | FK(Standard) | PROTECT |
| `classification` | FK(Classification, null=True) | SET_NULL |
| `job_identity` | CharField (choices) | anodize, cadmium_plate, etc. |
| `surface_area` | FloatField (null) | sq in — required for rectified steps |
| `date` | DateField | |
| `rework` | BooleanField | |
| `requires_masking` | BooleanField | |
| `requires_stress_relief` | BooleanField | |
| `requires_hydrogen_relief` | BooleanField | |

**Key behavior:** `clean()` / `save()` checks for rectified steps and validates `surface_area` is present. `_calc_amps()` computes strike/plate amps = (surface_area / 144) × ASF and stashes them on the instance as `_plate_amps` / `_strike_amps`.

### `PDFSettings`
Singleton-style model. Controls footer content (doc ID, revision, repair station number) on printed work order travelers.

---

## App: `tanks`

### `ProductionLine`
Named production line (Line 1–7, Kernersville, Honeywell).

### `Tank`
Physical tank on a line. Stores dimensions, liquid level, scrubber info, max amps.

---

## App: `tank_controls`

Bath control parameters for a tank, organized as:

```
Tank ──► ControlSet ──► TemperatureSpec
                   ──► ChemicalSpec
                   ──► CheckSpec
                   ──► PeriodicTestSpec ◄── StandardPeriodicRequirement (in standard app)
```

### `PeriodicTestExecution`
Log of an actual test run against a `PeriodicTestSpec` (pass/fail, performed_by FK to User).

---

## App: `kanban`

### `Product`
A chemical/consumable product tracked for inventory.

| Field | Notes |
|---|---|
| `trigger_level` | Reorder point |
| `total_quantity` | Property — sums `chemical_lots` quantities (fires a query each call) |

### `ChemicalLot`
A specific lot of a product with quantity and expiry date.

---

## App: `masking`

### `MaskingProcess`
A named masking procedure.

### `MaskingStep`
An ordered step in a masking process. `step_number` is auto-assigned and re-normalized on every save via `reorder_steps()`. Steps cannot be deleted from views — only from the Django admin (enforced in `delete()` via `_force_delete` flag).

---

## App: `fixtures`

### `Rack`
A physical shop rack/fixture.

### `PMTask`
A PM task definition (what to do, frequency in days).

### `RackPMPlan`
Maps a `PMTask` to a `Rack` with due-date tracking.

### `RackPM`
A completed PM record for a rack + task.

---

## App: `logbook`

### `LogEntry`
A process run log entry. Uses free-text fields for standard/classification (no FK) to avoid coupling.

### `DailyInspectionLogEntry`
Daily secondary-containment inspection checklist.

### `ScrubberLog`
Scrubber stage reading log with pass/fail.

---

## Key Cross-App Relationships

```
standard.StandardPeriodicRequirement
    └── standard FK → standard.Standard
    └── test_spec FK → tank_controls.PeriodicTestSpec

standard.Classification
    └── used by → process.Process
    └── used by → part.WorkOrder
    └── used by → part.PartStandard

methods.Method
    └── used by → process.ProcessStep
```

---

## Constraints Worth Knowing

| Model | Constraint | Note |
|---|---|---|
| `Standard` | unique `(name, revision)` | |
| `Process` | unique `(standard, classification)` — two partial constraints | one for classified, one for null |
| `ProcessStep` | unique `(process, step_number)`, `step_number ≥ 1` | |
| `Method` | unique `title` | |
| `ParameterTemplate` | unique `category` | |
| `ParameterToBeRecorded` | unique `(method, description)` | |
| `PartStandard` | **BUG** — both constraints have same condition | see `TASK.md` item 5 |
| `Part` | unique `(part_number, part_revision)` | |
