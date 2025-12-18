document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. SETUP ---
    mapboxgl.accessToken = window.mapboxAccessToken;
    
    // Maps
    let requestMap = null; // For the "Accept Ride" modal
    let trackingMap = null; // For the "Active Ride" tracking modal
    
    // Markers for Tracking
    let driverMarker = null;
    let pickupMarker = null;
    let dropoffMarker = null;
    
    let currentRideId = null;
    let trackingInterval = null;

    // --- 2. RIDE REQUEST MODAL LOGIC ---
    const requestModal = document.getElementById('ride-request-modal');
    const acceptBtn = document.getElementById('btn-accept-ride');

    window.openRideRequestModal = async function(rideId) {
        currentRideId = rideId;
        requestModal.classList.remove('hidden');
        requestModal.classList.add('flex');
        
        // Fetch & Show Data (Simplified for brevity, assuming similar fetch logic as before)
        try {
            const res = await fetch(`${window.rideDetailsBaseUrl}${rideId}/`);
            const data = await res.json();
            if(data.success) {
                const ride = data.ride;
                // Update text fields...
                document.getElementById('request-details').innerHTML = `
                    <p><strong>Client:</strong> ${ride.customer_name}</p>
                    <p><strong>From:</strong> ${ride.pickup}</p>
                    <p><strong>To:</strong> ${ride.dropoff}</p>
                    <p><strong>Fare:</strong> RWF ${ride.est_earning}</p>
                `;
                
                // Initialize Request Map
                initRequestMap(ride);
            }
        } catch(e) { console.error(e); }
    };

    window.closeRideRequestModal = function() {
        requestModal.classList.add('hidden');
        requestModal.classList.remove('flex');
        currentRideId = null;
    };

    function initRequestMap(ride) {
        if (!requestMap) {
            requestMap = new mapboxgl.Map({
                container: 'request-map',
                style: 'mapbox://styles/mapbox/streets-v12',
                center: [ride.pickup_lng, ride.pickup_lat],
                zoom: 11
            });
        }
        setTimeout(() => {
            requestMap.resize();
            drawStaticRoute(requestMap, ride);
        }, 200);
    }

    // --- 3. TRACKING MODAL LOGIC (ACTIVE RIDE) ---
    const trackingModal = document.getElementById('tracking-modal');

    window.openTrackingModal = async function(rideId) {
        trackingModal.classList.remove('hidden');
        trackingModal.classList.add('flex');
        
        // 1. Fetch Initial Ride Data
        const res = await fetch(`${window.rideDetailsBaseUrl}${rideId}/`);
        const data = await res.json();
        
        if(data.success) {
            initTrackingMap(data.ride);
        }
    };

    window.closeTrackingModal = function() {
        trackingModal.classList.add('hidden');
        trackingModal.classList.remove('flex');
        // Stop polling specific to this modal if any
    };

    function initTrackingMap(ride) {
        if (!trackingMap) {
            trackingMap = new mapboxgl.Map({
                container: 'tracking-map',
                style: 'mapbox://styles/mapbox/streets-v12',
                center: [ride.pickup_lng, ride.pickup_lat],
                zoom: 12
            });
        }
        
        setTimeout(() => {
            trackingMap.resize();
            
            // Markers
            if(!pickupMarker) pickupMarker = new mapboxgl.Marker({ color: '#22c55e' }).setLngLat([ride.pickup_lng, ride.pickup_lat]).addTo(trackingMap);
            else pickupMarker.setLngLat([ride.pickup_lng, ride.pickup_lat]).addTo(trackingMap);

            if(!dropoffMarker) dropoffMarker = new mapboxgl.Marker({ color: '#ef4444' }).setLngLat([ride.dropoff_lng, ride.dropoff_lat]).addTo(trackingMap);
            else dropoffMarker.setLngLat([ride.dropoff_lng, ride.dropoff_lat]).addTo(trackingMap);

            // Driver Marker (Initialize at pickup or last known location)
            // Ideally we get this from the driver's current position via Geolocation API immediately
            navigator.geolocation.getCurrentPosition(pos => {
                const driverLng = pos.coords.longitude;
                const driverLat = pos.coords.latitude;
                
                if(!driverMarker) {
                    const el = document.createElement('div');
                    el.className = 'w-6 h-6 bg-blue-600 rounded-full border-2 border-white shadow-lg';
                    driverMarker = new mapboxgl.Marker(el).setLngLat([driverLng, driverLat]).addTo(trackingMap);
                } else {
                    driverMarker.setLngLat([driverLng, driverLat]);
                }
                
                // Draw Route: Driver -> Pickup -> Dropoff
                drawTrackingRoute(driverLng, driverLat, ride);
            });

            // Fit Bounds
            const bounds = new mapboxgl.LngLatBounds()
                .extend([ride.pickup_lng, ride.pickup_lat])
                .extend([ride.dropoff_lng, ride.dropoff_lat]);
            trackingMap.fitBounds(bounds, { padding: 50 });
            
        }, 200);
    }

    async function drawTrackingRoute(driverLng, driverLat, ride) {
        // Construct waypoints: Driver -> Pickup -> Dropoff
        const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${driverLng},${driverLat};${ride.pickup_lng},${ride.pickup_lat};${ride.dropoff_lng},${ride.dropoff_lat}?geometries=geojson&access_token=${mapboxgl.accessToken}`;
        
        try {
            const res = await fetch(url);
            const data = await res.json();
            if (data.routes && data.routes[0]) {
                const route = data.routes[0].geometry;
                
                // Update source
                if (trackingMap.getSource('track-route')) {
                    trackingMap.getSource('track-route').setData({
                        'type': 'Feature', 'properties': {}, 'geometry': route
                    });
                } else {
                    trackingMap.addSource('track-route', {
                        'type': 'geojson',
                        'data': { 'type': 'Feature', 'properties': {}, 'geometry': route }
                    });
                    trackingMap.addLayer({
                        'id': 'track-route',
                        'type': 'line',
                        'source': 'track-route',
                        'layout': { 'line-join': 'round', 'line-cap': 'round' },
                        'paint': { 'line-color': '#3b82f6', 'line-width': 5 }
                    });
                }
                
                // Update Info Stats
                const duration = Math.round(data.routes[0].duration / 60);
                const distance = (data.routes[0].distance / 1000).toFixed(1);
                document.getElementById('track-dist').textContent = distance;
                document.getElementById('track-time').textContent = duration;
            }
        } catch(e) { console.error(e); }
    }

    // --- 4. SHARED HELPERS ---
    async function drawStaticRoute(mapInstance, ride) {
        const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${ride.pickup_lng},${ride.pickup_lat};${ride.dropoff_lng},${ride.dropoff_lat}?geometries=geojson&access_token=${mapboxgl.accessToken}`;
        const res = await fetch(url);
        const data = await res.json();
        if (data.routes && data.routes[0]) {
            const route = data.routes[0].geometry;
            const srcId = 'static-route';
            if (mapInstance.getSource(srcId)) {
                mapInstance.getSource(srcId).setData({ 'type': 'Feature', 'properties': {}, 'geometry': route });
            } else {
                mapInstance.addSource(srcId, { 'type': 'geojson', 'data': { 'type': 'Feature', 'properties': {}, 'geometry': route } });
                mapInstance.addLayer({ 'id': srcId, 'type': 'line', 'source': srcId, 'layout': {'line-join': 'round'}, 'paint': { 'line-color': '#888', 'line-width': 4 } });
            }
        }
    }

    // Accept Ride Event
    acceptBtn.addEventListener('click', async () => {
        if(!currentRideId) return;
        acceptBtn.textContent = "Accepting...";
        try {
            const res = await fetch(`${window.acceptRideBaseUrl}${currentRideId}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': window.csrfToken, 'Content-Type': 'application/json' }
            });
            const data = await res.json();
            if(data.success) window.location.reload();
            else alert(data.error);
        } catch(e) { alert("Error accepting ride"); }
    });

    // --- 5. LOCATION SYNC (Background) ---
    function syncDriverLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(async (pos) => {
                await fetch(window.updateLocationUrl, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': window.csrfToken, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ latitude: pos.coords.latitude, longitude: pos.coords.longitude })
                });
            });
        }
    }
    // Update every 5 minutes as requested
    setInterval(syncDriverLocation, 300000); 
    syncDriverLocation(); // Initial call
});