# Security / Privacy Notes

1. **Authentication**
   - `/api/auth/login` verifies username/password.
   - Session stores only `user_id` and `role`. No plaintext passwords.

2. **CSRF**
   - `security.py` issues a CSRF token per session (`generate_csrf_token`).
   - All POST/PUT/DELETE routes call `require_login_and_csrf`, which:
     - checks session
     - checks `allowed_roles`
     - validates `X-CSRF-Token`

3. **RBAC**
   - `require_login_and_csrf(allowed_roles=[...])` prevents unauthorized role access.
   - Example:
     - Only `Doctor` can call `/api/prescriptions` POST.
     - Only `Admin` or `Pharmacy` can create billing.

4. **Patient Privacy**
   - `/api/patients/<id>`:
     - `Pharmacy` sees demographics but medical_history is replaced with "[REDACTED]".
     - `Patient` can only view their OWN record, matched by `owner_user_id`.
     - `Admin`, `Staff`, `Doctor` see full chart.

5. **Double Booking**
   - `appointments` table uses `UNIQUE(doctor_id,start_time)`.
   - If violated, `/api/appointments` POST returns 409.

6. **Transport Security**
   - Cookies are `HttpOnly` and `SameSite=Strict`.
   - `SESSION_COOKIE_SECURE` can be set to True in production to enforce HTTPS cookies.

7. **Secrets**
   - `.env.example` is safe to commit.
   - The real `.env` with `SECRET_KEY` is ignored via `.gitignore`.
