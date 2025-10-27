# COCOMO (High-Level Coursework Estimate)

Scope: Flask-based RBAC hospital management system
Modules: auth, patients, appointments, prescriptions, billing, notifications

Estimated size: ~2.5 KLOC (Python + JS)

COCOMO Organic Model:
Effort (PM) = 2.4 * (KLOC ^ 1.05)
Schedule (Months) = 2.5 * (Effort ^ 0.38)

For 2.5 KLOC:
Effort ≈ 2.4 * (2.5 ^ 1.05) ≈ ~6.3 person-months
Schedule ≈ 2.5 * (6.3 ^ 0.38) ≈ ~3.2 months

Interpretation:
- A 2-3 person student team over ~1 academic term (10-14 weeks)
  can realistically deliver and iterate on this system,
  including testing and documentation.
