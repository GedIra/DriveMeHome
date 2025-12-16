document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. CONFIGURATION ---
    if (typeof mapboxgl === 'undefined') {
        console.error("Mapbox GL JS failed to load.");
        const mapContainer = document.getElementById('map');
        if (mapContainer) {
            mapContainer.innerHTML = '<div class="flex items-center justify-center h-full text-red-500 bg-gray-100 p-4 text-center">Map unavailable. Check internet connection.</div>';
        }
        return;
    }

    if (!window.mapboxAccessToken) {
        console.error("Mapbox Access Token is missing!");
        alert("System Error: Map configuration missing.");
        return;
    }
    
    mapboxgl.accessToken = window.mapboxAccessToken;
    const DEFAULT_CENTER = [30.0619, -1.9441]; // Kigali
    const DEFAULT_ZOOM = 12;

    const map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v12',
        center: DEFAULT_CENTER,
        zoom: DEFAULT_ZOOM
    });

    map.addControl(new mapboxgl.NavigationControl());

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

    // --- 3. MARKER SETUP ---
    const pickupMarker = new mapboxgl.Marker({ color: '#22c55e', draggable: true });
    const dropoffMarker = new mapboxgl.Marker({ color: '#ef4444', draggable: true });

    let pickupCoords = null;
    let dropoffCoords = null;
    let debounceTimer = null;

    // --- 4. CORE LOGIC ---

    function updateLocationState(type, lng, lat, address = null) {
        const input = document.getElementById(`${type}-input`);
        const latInput = document.getElementById(`id_${type}_latitude`);
        const lngInput = document.getElementById(`id_${type}_longitude`);
        
        if(!input || !latInput || !lngInput) return;

        const marker = type === 'pickup' ? pickupMarker : dropoffMarker;

        if (type === 'pickup') pickupCoords = { lng, lat };
        else dropoffCoords = { lng, lat };

        latInput.value = lat;
        lngInput.value = lng;

        marker.setLngLat([lng, lat]).addTo(map);

        if (address) {
            input.value = address;
        } else {
            reverseGeocode(lng, lat).then(addr => {
                input.value = addr;
            });
        }

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

    async function calculateEstimate() {
        if (!pickupCoords || !dropoffCoords) return;

        const card = document.getElementById('estimate-card');
        const priceEl = document.getElementById('est-price');
        const reqBtn = document.getElementById('btn-request');
        
        if (card) {
            card.classList.remove('hidden');
            card.classList.add('animate-pulse');
        }
        if (priceEl) priceEl.innerText = "Calculating...";
        if (reqBtn) {
            reqBtn.disabled = true;
            reqBtn.classList.remove('bg-blue-700', 'hover:bg-blue-800');
            reqBtn.classList.add('bg-gray-300', 'cursor-not-allowed');
        }

        try {
            const params = new URLSearchParams({
                pickup_lat: pickupCoords.lat,
                pickup_lng: pickupCoords.lng,
                dropoff_lat: dropoffCoords.lat,
                dropoff_lng: dropoffCoords.lng
            });

            // Use dynamic URL injected from Template
            const url = window.estimateUrl || '/api/estimate-ride/';
            const res = await fetch(`${url}?${params}`);
            const data = await res.json();

            if (card) card.classList.remove('animate-pulse');

            if (data.success) {
                if (priceEl) priceEl.textContent = `${data.currency || 'RWF'} ${data.estimated_price.toLocaleString()}`;
                
                const distEl = document.getElementById('est-distance');
                const durEl = document.getElementById('est-duration');
                
                if (distEl) distEl.textContent = `${data.distance_km} km`;
                if (durEl) durEl.textContent = `${data.duration_min} min`;
                
                if (reqBtn) {
                    reqBtn.disabled = false;
                    reqBtn.classList.remove('bg-gray-300', 'cursor-not-allowed');
                    reqBtn.classList.add('bg-blue-700', 'hover:bg-blue-800', 'shadow-lg');
                }
            } else {
                if (priceEl) priceEl.textContent = 'Unavailable';
                console.error("Backend Error:", data.error);
            }
        } catch (e) {
            console.error("Estimate Error:", e);
            if (card) card.classList.remove('animate-pulse');
            if (priceEl) priceEl.textContent = 'Error';
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
    pickupMarker.on('dragend', () => {
        const lngLat = pickupMarker.getLngLat();
        updateLocationState('pickup', lngLat.lng, lngLat.lat);
    });

    dropoffMarker.on('dragend', () => {
        const lngLat = dropoffMarker.getLngLat();
        updateLocationState('dropoff', lngLat.lng, lngLat.lat);
    });

    document.querySelectorAll('.saved-place-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.target; 
            const lat = parseFloat(btn.dataset.lat);
            const lng = parseFloat(btn.dataset.lng);
            const address = btn.dataset.address;
            updateLocationState(target, lng, lat, address);
        });
    });

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
                if (!features || features.length === 0) { results.classList.add('hidden'); return; }
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
                    const modalClose = document.querySelector('[data-modal-hide="add-vehicle-modal"]');
                    if(modalClose) modalClose.click();
                } else alert("Error: " + data.error);
            } catch (err) { console.error(err); } 
            finally { btn.textContent = "Save Vehicle"; btn.disabled = false; }
        });
    }
});