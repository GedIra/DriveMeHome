# DriveMe Home - Testing Guide

## Base URLs
- **Local Development**: `http://localhost:8000`
- **Production**: Configured in settings

---

## 🔓 PUBLIC ROUTES (No Authentication Required)

### Authentication & Registration
| # | URL | Method | Function | Description |
|---|-----|--------|----------|-------------|
| 1 | `/` | GET | `landing_view` | Landing page / homepage |
| 2 | `/auth/login/` | GET, POST | `UserLoginView` | User login page |
| 3 | `/auth/register/` | GET, POST | `RegisterView` | User registration page |
| 4 | `/auth/activation-sent/` | GET | `activation_sent_view` | Email activation confirmation page |
| 5 | `/auth/activate/<uidb64>/<token>/` | GET | `ActivateAccountView` | Email activation link (from email) |
| 6 | `/auth/password-reset/` | GET, POST | `PasswordResetView` | Password reset request page |
| 7 | `/auth/password-reset/done/` | GET | `PasswordResetDoneView` | Password reset email sent confirmation |
| 8 | `/auth/password-reset-confirm/<uidb64>/<token>/` | GET, POST | `PasswordResetConfirmView` | Password reset confirmation link (from email) |
| 9 | `/auth/password-reset-complete/` | GET | `PasswordResetCompleteView` | Password reset completed page |

### Validation APIs (AJAX)
| # | URL | Method | Function | Description |
|---|-----|--------|----------|-------------|
| 10 | `/auth/ajax/check-username/` | GET | `check_username_existence` | Check if username is available (AJAX) |
| 11 | `/auth/ajax/check-email/` | GET | `check_email_existence` | Check if email is registered (AJAX) |
| 12 | `/auth/ajax/check-phone/` | GET | `check_phone_existence` | Check if phone is registered (AJAX) |

---

## 🔐 AUTHENTICATED ROUTES (Login Required)

### User Profile Management
| # | URL | Method | Function | Description |
|---|-----|--------|----------|-------------|
| 13 | `/auth/logout/` | GET, POST | `LogoutView` | User logout |
| 14 | `/auth/profile/` | GET, POST | `profile_view` | View/edit user profile (driver or customer) |
| 15 | `/auth/driver/apply/` | GET, POST | `driver_application_view` | Driver verification application form |

### Customer Account Settings
| # | URL | Method | Function | Description |
|---|-----|--------|----------|-------------|
| 16 | `/auth/settings/customer/` | GET, POST | `customer_profile_settings_view` | Customer account settings & profile updates |
| 17 | `/auth/settings/driver/` | GET, POST | `driver_profile_settings_view` | Driver account settings & document updates |

### Customer Preferences
| # | URL | Method | Function | Description |
|---|-----|--------|----------|-------------|
| 18 | `/auth/preferences/` | GET | `client_preferences_view` | View saved destinations & emergency contacts |
| 19 | `/auth/preferences/dest/add/` | POST | `add_destination_view` | Add new preferred destination |
| 20 | `/auth/preferences/dest/edit/<id>/` | POST | `edit_destination_view` | Edit existing destination (ID = destination pk) |
| 21 | `/auth/preferences/dest/del/<id>/` | GET | `delete_destination_view` | Delete destination (ID = destination pk) |
| 22 | `/auth/preferences/contact/add/` | POST | `add_emergency_contact_view` | Add emergency contact |
| 23 | `/auth/preferences/contact/edit/<id>/` | POST | `edit_emergency_contact_view` | Edit emergency contact (ID = contact pk) |
| 24 | `/auth/preferences/contact/del/<id>/` | GET | `delete_emergency_contact_view` | Delete emergency contact (ID = contact pk) |

### Ride Booking (Customer)
| # | URL | Method | Function | Description |
|---|-----|--------|----------|-------------|
| 25 | `/rides/book/` | GET, POST | `book_ride_view` | Book a ride page |
| 26 | `/rides/history/` | GET | `ride_history_view` | View past rides with filters & pagination |

### Ride Booking APIs (AJAX)
| # | URL | Method | Function | Description |
|---|-----|--------|----------|-------------|
| 27 | `/rides/api/add-vehicle/` | POST | `add_vehicle_view` | Add vehicle (AJAX) - Body: `{name, plate, transmission, category}` |
| 28 | `/rides/api/estimate-ride/` | GET | `get_ride_estimate_view` | Get ride estimate - Params: `pickup_lat, pickup_lng, dropoff_lat, dropoff_lng` |
| 29 | `/rides/api/get-drivers/` | GET | `get_qualified_drivers_view` | Get qualified drivers - Params: `vehicle_id` |

### Driver Dashboard
| # | URL | Method | Function | Description |
|---|-----|--------|----------|-------------|
| 30 | `/rides/driver/dashboard/` | GET | `driver_dashboard_view` | Driver dashboard (active ride & job queue) |

### Driver APIs (AJAX)
| # | URL | Method | Function | Description |
|---|-----|--------|----------|-------------|
| 31 | `/rides/api/driver/status/` | POST | `update_driver_status_api` | Update driver online/offline status - Body: `{status: 'AVAILABLE'\|'OFFLINE'}` |
| 32 | `/rides/api/driver/accept/<ride_id>/` | POST | `accept_ride_api` | Accept a ride request (ID = ride pk) |
| 33 | `/rides/api/driver/location/update/` | POST | `update_driver_location_api` | Update driver's current location - Body: `{latitude, longitude}` |
| 34 | `/rides/api/ride/details/<ride_id>/` | GET | `get_ride_details_api` | Get ride details for tracking modal (ID = ride pk) |

### Admin
| # | URL | Method | Function | Description |
|---|-----|--------|----------|-------------|
| 35 | `/admin/` | GET, POST | Django Admin | Django admin panel (staff only) |

---

## 📋 TESTING WORKFLOW

### 1. **Registration & Activation** (No Auth)
1. Go to `/auth/register/`
2. Fill form: username, email, phone, password
3. Check browser console or email for activation link
4. Visit `/auth/activate/<uidb64>/<token>/`
5. Verify account is activated

### 2. **Login** (No Auth)
1. Go to `/auth/login/`
2. Enter credentials
3. Should redirect to profile or dashboard

### 3. **Customer Workflow** (Auth as Customer)
1. Go to `/auth/profile/` → set profile picture, name, etc.
2. Go to `/auth/preferences/` → add destinations & emergency contacts
3. Go to `/rides/book/` → request a ride
4. Use `/rides/api/estimate-ride/` to see pricing
5. Go to `/rides/history/` → see past rides

### 4. **Driver Workflow** (Auth as Driver)
1. Go to `/auth/profile/` → fill basic info
2. Go to `/auth/driver/apply/` → submit verification docs (license, insurance, etc.)
3. Once verified, go to `/auth/settings/driver/` → manage documents
4. Go to `/rides/driver/dashboard/` → see active ride & job queue
5. Use `/rides/api/driver/status/` to toggle online/offline
6. Use `/rides/api/driver/accept/<ride_id>/` to accept a ride
7. Use `/rides/api/ride/details/<ride_id>/` to open tracking modal
8. Use driver status button in modal to transition ride states (Arrived → Start → End)

---

## 🧪 TESTING SCENARIOS

### Scenario A: Complete Ride Booking (Customer → Driver)
1. **Customer**: Register, activate, set profile
2. **Customer**: Go to `/rides/book/` → request a ride
3. **Driver**: Register, activate, apply for verification
4. **Driver**: Go to `/rides/driver/dashboard/` → see job request
5. **Driver**: Use API `/rides/api/driver/accept/<ride_id>/` to accept
6. **Driver**: Go to `/rides/driver/dashboard/` → click "Track Route"
7. **Driver**: Modal opens with map, client info, legend, and action button
8. **Driver**: Click "I Have Arrived" → status updates
9. **Driver**: Click "Start Ride" → status updates
10. **Driver**: Click "End Ride" → ride completed
11. **Customer**: Go to `/rides/history/` → see completed ride

### Scenario B: Password Reset
1. Go to `/auth/password-reset/`
2. Enter registered email
3. Check console/email for reset link
4. Visit `/auth/password-reset-confirm/<uidb64>/<token>/`
5. Enter new password
6. Confirm at `/auth/password-reset-complete/`

### Scenario C: Real-time Location Tracking
1. **Driver**: Accept a ride
2. **Driver**: Open tracking modal (`/rides/driver/dashboard/` → Track Route button)
3. **Driver**: Allow geolocation permission
4. Driver marker (blue dot) appears and updates every ~5 seconds
5. Routes redraw: blue line (driver→pickup), green line (pickup→dropoff)
6. Distance & time update in real-time

---

## 🔧 EXAMPLE AJAX REQUESTS (Using cURL or Postman)

### Check Username Availability
```bash
curl "http://localhost:8000/auth/ajax/check-username/?username=johndoe"
# Response: {"exists": false, "message": "Username is available."}
```

### Estimate Ride
```bash
curl "http://localhost:8000/rides/api/estimate-ride/?pickup_lat=-1.9536&pickup_lng=29.8739&dropoff_lat=-1.9600&dropoff_lng=29.9000"
# Response: {"success": true, "distance_km": 5.2, "duration_min": 12, "estimated_price": 8500, "currency": "RWF"}
```

### Accept a Ride
```bash
curl -X POST http://localhost:8000/rides/api/driver/accept/1/ \
  -H "X-CSRFToken: <csrf_token>" \
  -H "Content-Type: application/json" \
  -d "{}"
# Response: {"success": true, "ride_id": 1}
```

### Update Driver Status
```bash
curl -X POST http://localhost:8000/rides/api/driver/status/ \
  -H "X-CSRFToken: <csrf_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "AVAILABLE"}'
# Response: {"success": true, "new_status": "AVAILABLE", "display_status": "Available"}
```

### Get Ride Details
```bash
curl "http://localhost:8000/rides/api/ride/details/1/"
# Response: {"success": true, "ride": {"id": 1, "customer_name": "Alice", "pickup": "Kigali Center", ...}}
```

### Update Driver Location
```bash
curl -X POST http://localhost:8000/rides/api/driver/location/update/ \
  -H "X-CSRFToken: <csrf_token>" \
  -H "Content-Type: application/json" \
  -d '{"latitude": -1.9536, "longitude": 29.8739}'
# Response: {"success": true, "message": "Location updated"}
```

---

## 🛠 FRONTEND TECHNOLOGIES

| Technology | Purpose |
|------------|---------|
| **HTML5** | Semantic markup & structure |
| **Tailwind CSS v4** | Utility-first CSS framework for styling |
| **Vanilla JavaScript** | Core interactivity (no jQuery/React) |
| **Mapbox GL JS v3.1.2** | Interactive maps & routing visualization |
| **Ionicons 7.1.0** | SVG icon library |
| **Django Template Language** | Server-side templating |

### Key Frontend Features
- Real-time map tracking with dual-leg routes (blue: driver→pickup, green: pickup→dropoff)
- Live geolocation updates every ~5s (watchPosition)
- Modal accessibility with aria-hidden / focus management
- Responsive design with grid & flexbox
- AJAX form validation (check username, email, phone)

---

## 🔙 BACKEND TECHNOLOGIES

| Technology | Purpose |
|------------|---------|
| **Django 5.2** | Web framework |
| **Python 3.10+** | Programming language |
| **SQLite / PostgreSQL** | Database |
| **Decimal** | Precise financial calculations |
| **Django Signals** | Auto-create user profiles |
| **Django Mail Framework** | Email sending (activation, password reset) |
| **Mapbox Directions API** | Route & distance calculation |

### Key Backend Features
- User authentication (registration, email activation, password reset)
- Role-based access (Customer vs Driver)
- Ride lifecycle management (REQUESTED → ASSIGNED → ARRIVED → IN_PROGRESS → COMPLETED)
- Dynamic pricing based on distance & duration
- Real-time driver location tracking
- Multi-user concurrency (single active ride per driver)

---

## ⚙️ SETUP & RUN

### Prerequisites
- Python 3.10+
- pip or pipenv
- Mapbox API token (free account at mapbox.com)

### Installation
```bash
# Clone repo
git clone <repo_url>
cd DriveMeHome

# Install dependencies
pipenv install
pipenv shell

# Configure environment
cp .env.example .env
# Edit .env with your Mapbox token and database credentials

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start dev server
python manage.py runserver
```

### Access
- App: `http://localhost:8000`
- Admin: `http://localhost:8000/admin/`

---

## 📞 TEST ACCOUNTS (Seed Data - Optional)

If you populate test data via Django shell or fixtures:

**Customer Account:**
- Username: `customer1`
- Password: `test123`
- Email: `customer@example.com`

**Driver Account:**
- Username: `driver1`
- Password: `test123`
- Email: `driver@example.com`

---

## ✅ TESTING CHECKLIST

- [ ] Public pages load without errors (landing, login, register)
- [ ] Registration validates & sends activation email
- [ ] Email activation link works
- [ ] Login with valid/invalid credentials
- [ ] Password reset flow complete
- [ ] Customer can add vehicle, preferences, destinations
- [ ] Customer can book a ride and see history
- [ ] Driver can apply for verification
- [ ] Driver can toggle online/offline status
- [ ] Driver can see job queue when online
- [ ] Driver can accept a ride
- [ ] Tracking modal opens with map
- [ ] Map shows driver, pickup, dropoff markers
- [ ] Routes display with correct colors
- [ ] Driver location updates in real-time
- [ ] Ride status transitions work (I Have Arrived → Start Ride → End Ride)
- [ ] Ride details populate correctly
- [ ] No console errors or CORS issues
- [ ] Mobile responsive layout
- [ ] Accessibility: keyboard navigation, screen readers

---

## 📝 NOTES FOR TESTERS

1. **Geolocation Permission**: Browser will request permission to access location. Grant it to see live tracking.
2. **CSRF Tokens**: All POST requests require `X-CSRFToken` header (automatically included by Django forms).
3. **Local Testing**: Use `localhost` or `127.0.0.1:8000`. Remote URLs will not work without proper domain configuration.
4. **Email**: Configure `EMAIL_BACKEND` in settings (console backend for development).
5. **Map Tiles**: Mapbox requires valid token; invalid tokens show blank maps.
6. **API Rate Limits**: Mapbox Directions API has free tier limits; monitor usage.

---

**Last Updated**: December 18, 2025  
**Version**: 1.0.0
