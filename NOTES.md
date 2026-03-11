# Notes

Ongoing decisions, compliance requirements, and planning context that doesn't fit in TASK.md.

---

## AC 120-78B Compliance

**Reference:** FAA Advisory Circular AC 120-78B — *Acceptance and Use of Electronic Signatures, Electronic Recordkeeping Systems, and Electronic Manuals*

**Why it applies:** This app is an electronic recordkeeping system for NADCAP-certified special processes. Work orders, process travelers, logbook entries, and inspection records are all covered by this AC.

**OpSpec requirement:** Certificate holders operating under 14 CFR Parts 121, 125, 133, 135, 141, 142, 145, and 147 must hold OpSpec A025 to use electronic signatures.

---

### What the AC Requires (and current gap)

| Requirement | AC 120-78B says | Current state |
|---|---|---|
| Unique credentials | Every user has a non-shareable login | Django auth exists but no `@login_required` on most views |
| Role-based authorization | Authorization tied to job function (Mechanic, Inspector, QC, Supervisor) | No roles defined — all authenticated users see everything |
| Audit trail | Every write action logged: who, what, when | No audit log model exists |
| Electronic signature | Work order sign-off tied to user credentials, non-repudiable | No signature model or workflow exists |
| Account suspension | Departed users deactivated (`is_active=False`), never deleted | No policy enforced |
| Signature retrieval | Operator can list all records they have signed | No such view exists |
| Credential sharing prohibited | Policy must be communicated to users | Not yet communicated |

---

### Phased Implementation Plan

**Phase 1 — Authentication (S-3, current sprint)**
Add `LoginRequiredMiddleware` so every view requires login. Login page includes AC 120-78B notice informing operators of the credential-sharing prohibition and audit logging.

**Phase 2 — Roles and Permissions**
Define Django `Groups` for the following roles and enforce them per view:
- `Mechanic` — can create/view work orders and log entries; cannot edit standards or processes
- `Inspector` — can view and sign off on work orders
- `QC Inspector` — can view all records, run reports
- `Supervisor` — full read/write; manages user accounts
- `Admin` — system-level access via Django admin only

**Phase 3 — Audit Trail**
Add an `AuditLog` model that records every create/update/delete action on critical models (`WorkOrder`, `LogEntry`, `RackPM`, `PeriodicTestExecution`). Fields: `user`, `timestamp`, `action`, `model`, `object_id`, `changes`.

**Phase 4 — Electronic Signature**
Add a `Signature` model linked to `WorkOrder`. The sign-off workflow requires the operator to re-enter their password at the point of signing. The signature record stores: `user`, `timestamp`, `work_order`, `ip_address`. The traveler PDF renders the signature block with name, date, and a unique signature ID.

**Phase 5 — Account Lifecycle Policy**
- Document the policy: departed operators → `is_active=False`, never delete User records
- Add a Supervisor-only view to manage user accounts (activate/deactivate)
- Add a view for each operator to see all records they have signed

---

### Questions for QC/Compliance Team (before Phase 2–5)

1. What roles exist at your facility? Does "Inspector" = a separate person from "Mechanic" or can one person hold both?
2. Which specific records require a formal electronic signature under your OpSpec?
3. Is re-entering a password at sign-off acceptable, or do you need a separate PIN?
4. Who is responsible for creating and deactivating user accounts — IT, the QC manager, or a supervisor in the app?
5. What is the record retention period for signed work orders?

---

## Customer Links / Landing Page — Public vs. Protected

The `customer_links` app and `landing_page` app may need to remain publicly accessible if external customers access them directly. Currently both are protected by `LoginRequiredMiddleware`.

**Decision needed:** Confirm with management whether `customer_links` and/or `landing_page` should be exempt from login. If yes, add `@login_not_required` to those views.
