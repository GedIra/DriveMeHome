document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. CONFIGURATION ---
    if (typeof mapboxgl === 'undefined' || !window.mapboxAccessToken) {
        console.error("Mapbox Error");
        return;
    }
    mapboxgl.accessToken = window.mapboxAccessToken;
    
    const map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [30.0619, -1.9441],
        zoom: 12
    });
    map.addControl(new mapboxgl.NavigationControl());

    // --- 2. MAP LOGIC (Markers, Route, Estimate) ---
    // (Keep previous map logic for drawing lines and calculating estimates)
    const pickupMarker = new mapboxgl.Marker({ color: '#22c55e', draggable: true });
    const dropoffMarker = new mapboxgl.Marker({ color: '#ef4444', draggable: true });
    let pickupCoords = null; let dropoffCoords = null; let debounceTimer = null;

    let mapLoaded = false;
    map.on('load', () => {
        mapLoaded = true;
        map.resize(); 

        // Route Source
        if (!map.getSource('route')) {
            map.addSource('route', {
                'type': 'geojson',
                'data': {
                    'type': 'Feature',
                    'properties': {},
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': []
                    }
                }
            });

            // Route Layer
            map.addLayer({
                'id': 'route',
                'type': 'line',
                'source': 'route',
                'layout': {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                'paint': {
                    'line-color': '#3b82f6', 
                    'line-width': 5,
                    'line-opacity': 0.75
                }
            });
        }
    });

    setTimeout(() => map.resize(), 1000);

    function updateLocationState(type, lng, lat, address = null) {
        const latInput = document.getElementById(`id_${type}_latitude`);
        const lngInput = document.getElementById(`id_${type}_longitude`);
        const input = document.getElementById(`${type}-input`);
        
        if(!latInput) return; // Safety check

        if (type === 'pickup') pickupCoords = { lng, lat };
        else dropoffCoords = { lng, lat };

        latInput.value = lat;
        lngInput.value = lng;
        
        const marker = type === 'pickup' ? pickupMarker : dropoffMarker;
        marker.setLngLat([lng, lat]).addTo(map);

        if(address) input.value = address;
        else reverseGeocode(lng, lat).then(a => input.value = a);

        triggerUpdates();
    }

    function triggerUpdates() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            if (pickupCoords && dropoffCoords) {
                drawRoute();
                calculateEstimate();
                fitBounds();
            } else if (pickupCoords) {
                map.flyTo({ center: [pickupCoords.lng, pickupCoords.lat], zoom: 14 });
            }
        }, 500); 
    }

    function fitBounds() {
        if (!pickupCoords || !dropoffCoords) return;
        const bounds = new mapboxgl.LngLatBounds()
            .extend([pickupCoords.lng, pickupCoords.lat])
            .extend([dropoffCoords.lng, dropoffCoords.lat]);
        map.fitBounds(bounds, { padding: 80 });
    }

    async function drawRoute() {
        if (!pickupCoords || !dropoffCoords) return;
        if (!mapLoaded) {
            setTimeout(drawRoute, 200);
            return;
        }

        const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${pickupCoords.lng},${pickupCoords.lat};${dropoffCoords.lng},${dropoffCoords.lat}?steps=true&geometries=geojson&access_token=${mapboxgl.accessToken}`;
        
        try {
            const res = await fetch(url);
            const data = await res.json();
            
            if (data.routes && data.routes[0]) {
                const route = data.routes[0].geometry;
                if (map.getSource('route')) {
                    map.getSource('route').setData({
                        'type': 'Feature',
                        'properties': {},
                        'geometry': route
                    });
                }
            }
        } catch (e) {
            console.error("Error fetching route:", e);
        }
    }

    // --- 3. SCHEDULING TOGGLE ---
    const timeNow = document.getElementById('time-now');
    const timeLater = document.getElementById('time-later');
    const scheduleContainer = document.getElementById('schedule-container');

    function toggleSchedule() {
        if (timeLater.checked) {
            scheduleContainer.classList.remove('hidden');
        } else {
            scheduleContainer.classList.add('hidden');
            // Clear input
            scheduleContainer.querySelector('input').value = '';
        }
    }
    if(timeNow && timeLater) {
        timeNow.addEventListener('change', toggleSchedule);
        timeLater.addEventListener('change', toggleSchedule);
    }

    // --- 4. DRIVER SELECTION LOGIC ---
    const btnOpenModal = document.getElementById('btn-open-driver-modal');
    const driverModal = document.getElementById('driver-selection-modal');
    const driverModalBackdrop = document.getElementById('driver-selection-modal-backdrop');
    const driverListContainer = document.getElementById('driver-list-container');
    const bookingForm = document.getElementById('booking-form');
    const modeInput = document.getElementById('id_driver_selection_mode');

    // FLOWBITE MODAL INSTANCE
    // We manually toggle classes for simplicity if Flowbite JS instance isn't perfect
    if(btnOpenModal) {
        btnOpenModal.addEventListener('click', () => {
            // Validate form first
            if (!pickupCoords || !dropoffCoords) {
                alert("Please select pickup and dropoff locations.");
                return;
            }
            const vehicleId = document.getElementById('id_vehicle').value;
            if(!vehicleId) {
                alert("Please select a vehicle.");
                return;
            }

            // Show Modal & Backdrop
            driverModal.classList.remove('hidden');
            driverModal.classList.add('flex'); // Centered via flex
            driverModalBackdrop.classList.remove('hidden');
            
            // Fetch Drivers
            fetchDrivers(vehicleId);
        });
    }

    // Close Modal logic
    document.querySelectorAll('[data-modal-hide="driver-selection-modal"]').forEach(btn => {
        btn.addEventListener('click', () => {
            driverModal.classList.add('hidden');
            driverModal.classList.remove('flex');
            driverModalBackdrop.classList.add('hidden');
        });
    });

    async function fetchDrivers(vehicleId) {
        driverListContainer.innerHTML = '<div class="text-center p-4">Loading drivers...</div>';
        try {
            const res = await fetch(`${window.getDriversUrl}?vehicle_id=${vehicleId}`);
            const data = await res.json();
            
            if(data.success) {
                renderDrivers(data.drivers);
            } else {
                driverListContainer.innerHTML = `<div class="text-red-500 text-center">${data.error}</div>`;
            }
        } catch(e) {
            driverListContainer.innerHTML = '<div class="text-red-500 text-center">Failed to load drivers.</div>';
        }
    }

    function renderDrivers(drivers) {
        if(drivers.length === 0) {
            driverListContainer.innerHTML = '<div class="text-center p-4 text-gray-500">No qualified drivers found for this vehicle type.</div>';
            return;
        }

        driverListContainer.innerHTML = '';
        drivers.forEach(driver => {
            const el = document.createElement('div');
            el.className = 'bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-3 flex justify-between items-center driver-card';
            
            // Status Color
            const statusColor = driver.status_code === 'AVAILABLE' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800';
            
            el.innerHTML = `
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-gray-200 overflow-hidden">
                        ${driver.avatar ? `<img src="${driver.avatar}" class="w-full h-full object-cover">` : '<svg class="w-full h-full text-gray-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"></path></svg>'}
                    </div>
                    <div>
                        <h4 class="font-bold text-gray-800">${driver.name}</h4>
                        <div class="flex items-center text-xs mt-1 gap-2">
                            <span class="px-2 py-0.5 rounded-full ${statusColor} font-medium">${driver.status}</span>
                            <span class="flex items-center text-yellow-500">
                                <svg class="w-3 h-3 mr-0.5" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>
                                ${driver.rating}
                            </span>
                            <span class="text-gray-400">| Cat: ${driver.category}</span>
                        </div>
                    </div>
                </div>
                <button type="button" class="btn-select-driver text-white bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium" data-id="${driver.id}">
                    Select
                </button>
            `;
            
            // Manual Select Event
            el.querySelector('.btn-select-driver').addEventListener('click', () => {
                submitBooking(driver.id);
            });

            driverListContainer.appendChild(el);
        });
    }

    // Auto Assign Event
    const btnAutoAssign = document.getElementById('btn-auto-assign');
    if (btnAutoAssign) {
        btnAutoAssign.addEventListener('click', () => {
            submitBooking('auto');
        });
    }

    function submitBooking(mode) {
        modeInput.value = mode;
        // Trigger the real form submit
        bookingForm.submit();
    }

    // --- 5. HELPERS (Geocoding, Estimate, etc. - Keep existing logic from previous turn) ---
    
    // For brevity, ensuring the fetch logic for estimate uses the window.estimateUrl
    async function calculateEstimate() {
        if (!pickupCoords || !dropoffCoords) return;
        const card = document.getElementById('estimate-card');
        const priceEl = document.getElementById('est-price');
        const reqBtn = document.getElementById('btn-open-driver-modal'); // Changed target ID
        
        card.classList.remove('hidden');
        priceEl.innerText = "Calculating...";
        if(reqBtn) {
            reqBtn.disabled = true;
            reqBtn.classList.add('bg-gray-300', 'cursor-not-allowed');
        }

        try {
            const params = new URLSearchParams({
                pickup_lat: pickupCoords.lat, pickup_lng: pickupCoords.lng,
                dropoff_lat: dropoffCoords.lat, dropoff_lng: dropoffCoords.lng
            });
            const res = await fetch(`${window.estimateUrl}?${params}`);
            const data = await res.json();

            if (data.success) {
                priceEl.textContent = `${data.currency || 'RWF'} ${data.estimated_price.toLocaleString()}`;
                document.getElementById('est-distance').textContent = `${data.distance_km} km`;
                document.getElementById('est-duration').textContent = `${data.duration_min} min`;
                card.classList.remove('animate-pulse');
                
                if(reqBtn) {
                    reqBtn.disabled = false;
                    reqBtn.classList.remove('bg-gray-300', 'cursor-not-allowed');
                    reqBtn.classList.add('bg-blue-700', 'hover:bg-blue-800');
                }
            } else {
                priceEl.textContent = 'Unavailable';
            }
        } catch (e) {
            priceEl.textContent = 'Error';
        }
    }
    
    // --- 5. GEOCODING UTILS ---
    async function reverseGeocode(lng, lat) {
        const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${lng},${lat}.json?access_token=${mapboxgl.accessToken}&limit=1`;
        try {
            const res = await fetch(url);
            const data = await res.json();
            return data.features?.[0]?.place_name || `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        } catch (e) { return "Unknown Location"; }
    }

    async function searchLocation(query) {
        if (!query || query.length < 3) return [];
        const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${mapboxgl.accessToken}&country=RW&limit=5`;
        try {
            const res = await fetch(url);
            const data = await res.json();
            return data.features;
        } catch (e) { return []; }
    }

    // --- 6. EVENT LISTENERS ---
    
    // Dragging Pins
    pickupMarker.on('dragend', () => {
        const lngLat = pickupMarker.getLngLat();
        updateLocationState('pickup', lngLat.lng, lngLat.lat);
    });

    dropoffMarker.on('dragend', () => {
        const lngLat = dropoffMarker.getLngLat();
        updateLocationState('dropoff', lngLat.lng, lngLat.lat);
    });

    // Saved Places Buttons
    document.querySelectorAll('.saved-place-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.target; 
            const lat = parseFloat(btn.dataset.lat);
            const lng = parseFloat(btn.dataset.lng);
            const address = btn.dataset.address;
            updateLocationState(target, lng, lat, address);
        });
    });

    // Autocomplete Setup
    function setupAutocomplete(type) {
        const input = document.getElementById(`${type}-input`);
        const results = document.getElementById(`${type}-results`);
        if(!input || !results) return;

        let timeout = null;

        input.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(async () => {
                const query = input.value;
                if (query.length < 3) { results.classList.add('hidden'); return; }
                
                const features = await searchLocation(query);
                results.innerHTML = '';
                
                if (!features || features.length === 0) {
                    results.classList.add('hidden');
                    return;
                }

                results.classList.remove('hidden');
                features.forEach(feature => {
                    const li = document.createElement('li');
                    li.className = 'p-3 hover:bg-gray-100 cursor-pointer text-sm border-b border-gray-100 last:border-0';
                    li.textContent = feature.place_name;
                    li.addEventListener('click', () => {
                        const [lng, lat] = feature.center;
                        updateLocationState(type, lng, lat, feature.place_name);
                        results.classList.add('hidden');
                    });
                    results.appendChild(li);
                });
            }, 300);
        });

        // Hide results on click outside
        document.addEventListener('click', (e) => {
            if (e.target !== input && e.target !== results) results.classList.add('hidden');
        });
    }

    setupAutocomplete('pickup');
    setupAutocomplete('dropoff');

    const btnCurrentLocation = document.getElementById('btn-current-location');
    if(btnCurrentLocation) {
        btnCurrentLocation.addEventListener('click', () => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition((position) => {
                    updateLocationState('pickup', position.coords.longitude, position.coords.latitude);
                }, () => alert("Location access denied."));
            }
        });
    }

    const vehicleForm = document.getElementById('add-vehicle-form');
    if (vehicleForm) {
        vehicleForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const btn = vehicleForm.querySelector('button[type="submit"]');
            const originalText = btn.textContent;
            btn.textContent = "Saving...";
            btn.disabled = true;

            const formData = new FormData(vehicleForm);
            const payload = {
                name: formData.get('name'), plate: formData.get('plate'),
                transmission: formData.get('transmission'), category: formData.get('category')
            };

            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                // Use dynamic URL
                const url = window.addVehicleUrl || '/api/add-vehicle/';
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                if (data.success) {
                    const select = document.querySelector('select[name="vehicle"]');
                    const option = document.createElement('option');
                    option.value = data.vehicle.id;
                    option.textContent = `${data.vehicle.name} (${data.vehicle.transmission})`;
                    option.selected = true;
                    select.appendChild(option);
                    
                    vehicleForm.reset();
                    // Close modal
                    const modalCloseBtn = document.querySelector('[data-modal-hide="add-vehicle-modal"]');
                    if(modalCloseBtn) modalCloseBtn.click();
                } else {
                    alert("Error: " + data.error);
                }
            } catch (err) { console.error(err); } 
            finally { btn.textContent = originalText; btn.disabled = false; }
        });
    }
});