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
            // Populate overlay details
            const ride = data.ride;
            const clientNameEl = document.getElementById('track-client-name');
            if (clientNameEl) clientNameEl.textContent = ride.customer_name || '--';
            const phoneEl = document.getElementById('track-phone');
            if (phoneEl) phoneEl.textContent = ride.customer_phone || (ride.customer && ride.customer.user && ride.customer.user.phone_number) || '--';
            const earningEl = document.getElementById('track-earning');
            if (earningEl) earningEl.textContent = 'RWF ' + (ride.est_earning || '--');
            const pickupEl = document.getElementById('track-pickup');
            if (pickupEl) pickupEl.textContent = ride.pickup || '--';
            const dropoffEl = document.getElementById('track-dropoff');
            if (dropoffEl) dropoffEl.textContent = ride.dropoff || '--';
            const rideIdEl = document.getElementById('track-ride-id');
            if (rideIdEl) rideIdEl.textContent = ride.id || '--';
            const statusEl = document.getElementById('track-status');
            if (statusEl) {
                const statusText = ride.status || '--';
                statusEl.textContent = statusText;
                // adjust badge color
                statusEl.className = 'inline-block text-xs font-semibold px-2.5 py-0.5 rounded';
                if (statusText === 'ASSIGNED') statusEl.classList.add('bg-blue-100','text-blue-800');
                else if (statusText === 'ARRIVED') statusEl.classList.add('bg-yellow-100','text-yellow-800');
                else if (statusText === 'IN_PROGRESS') statusEl.classList.add('bg-green-100','text-green-800');
                else if (statusText === 'COMPLETED') statusEl.classList.add('bg-gray-200','text-gray-800');
                else statusEl.classList.add('bg-gray-100','text-gray-800');
            }

            // avatar
            const avatarEl = document.getElementById('track-modal-avatar');
            if (avatarEl) {
                if (ride.customer_avatar) avatarEl.innerHTML = `<img src="${ride.customer_avatar}" class="w-full h-full object-cover">`;
                else avatarEl.textContent = (ride.customer_name || '?').slice(0,1).toUpperCase();
            }

            initTrackingMap(ride);
            // set current ride id and update action button
            currentRideId = ride.id || rideId;
            updateActionButton(ride.status);
            // start polling ride details while modal open
            if (trackingInterval) clearInterval(trackingInterval);
            trackingInterval = setInterval(async () => {
                try {
                    const r = await fetch(`${window.rideDetailsBaseUrl}${currentRideId}/`);
                    const d = await r.json();
                    if (d.success && d.ride) {
                        if (d.ride.status && d.ride.status !== ride.status) {
                            ride.status = d.ride.status;
                            updateActionButton(d.ride.status);
                        }
                    }
                } catch(e) { console.error('poll ride details', e); }
            }, 8000);
        }
    };

    window.closeTrackingModal = function() {
        trackingModal.classList.add('hidden');
        trackingModal.classList.remove('flex');
        // Stop polling specific to this modal if any
        if (trackingInterval) { clearInterval(trackingInterval); trackingInterval = null; }
        currentRideId = null;
    };

    function updateActionButton(status) {
        const btn = document.getElementById('btn-ride-action');
        const text = btn;
        if (!btn) return;
        btn.disabled = false;

        // Normalize status names used in backend
        switch(status) {
            case 'ASSIGNED':
            case 'DRIVER_ASSIGNED':
            case 'REQUESTED':
                btn.textContent = 'I Have Arrived';
                btn.onclick = () => updateRideStatus('ARRIVED');
                btn.className = 'w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded-md text-sm';
                break;
            case 'ARRIVED':
            case 'DRIVER_ARRIVED':
                btn.textContent = 'Start Ride';
                btn.onclick = () => updateRideStatus('IN_PROGRESS');
                btn.className = 'w-full bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 rounded-md text-sm';
                break;
            case 'IN_PROGRESS':
                btn.textContent = 'End Ride';
                btn.onclick = () => updateRideStatus('COMPLETED');
                btn.className = 'w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 rounded-md text-sm';
                break;
            case 'COMPLETED':
                btn.textContent = 'Ride Completed';
                btn.disabled = true;
                btn.className = 'w-full bg-gray-300 text-gray-700 font-bold py-2 rounded-md text-sm';
                break;
            default:
                btn.textContent = 'Update Status';
                btn.onclick = () => {};
                btn.className = 'w-full bg-gray-600 text-white font-bold py-2 rounded-md text-sm';
        }
    }

    async function updateRideStatus(newStatus) {
        if (!currentRideId) return alert('No ride selected');
        const btn = document.getElementById('btn-ride-action');
        if (btn) { btn.disabled = true; btn.textContent = 'Updating...'; }
        try {
            const res = await fetch(`${window.updateRideStatusBaseUrl}${currentRideId}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': window.csrfToken, 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });
            const data = await res.json();
            if (data.success) {
                // reflect new status locally and update UI
                updateActionButton(newStatus);
                // also update status badge
                const statusEl = document.getElementById('track-status');
                if (statusEl) {
                    statusEl.textContent = newStatus;
                }
            } else {
                alert('Status update failed: ' + (data.error || 'unknown'));
                if (btn) btn.disabled = false;
            }
        } catch(e) {
            console.error('update status', e);
            alert('Could not update status');
            if (btn) btn.disabled = false;
        }
    }

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
        // Draw two legs: driver -> pickup (blue) and pickup -> dropoff (green)
        if (!driverLng || !driverLat || !ride.pickup_lng || !ride.pickup_lat) return;

        const legAUrl = `https://api.mapbox.com/directions/v5/mapbox/driving/${driverLng},${driverLat};${ride.pickup_lng},${ride.pickup_lat}?geometries=geojson&access_token=${mapboxgl.accessToken}`;
        const legBUrl = `https://api.mapbox.com/directions/v5/mapbox/driving/${ride.pickup_lng},${ride.pickup_lat};${ride.dropoff_lng},${ride.dropoff_lat}?geometries=geojson&access_token=${mapboxgl.accessToken}`;

        try {
            // Leg A: driver -> pickup (blue)
            const resA = await fetch(legAUrl);
            const dataA = await resA.json();
            if (dataA.routes && dataA.routes[0]) {
                const routeA = dataA.routes[0].geometry;
                if (trackingMap.getSource('track-route-1')) {
                    trackingMap.getSource('track-route-1').setData({ 'type': 'Feature', 'properties': {}, 'geometry': routeA });
                } else {
                    trackingMap.addSource('track-route-1', { 'type': 'geojson', 'data': { 'type': 'Feature', 'properties': {}, 'geometry': routeA } });
                    trackingMap.addLayer({ 'id': 'track-route-1', 'type': 'line', 'source': 'track-route-1', 'layout': { 'line-join': 'round', 'line-cap': 'round' }, 'paint': { 'line-color': '#3b82f6', 'line-width': 5 } });
                }
            }

            // Leg B: pickup -> dropoff (green)
            const resB = await fetch(legBUrl);
            const dataB = await resB.json();
            if (dataB.routes && dataB.routes[0]) {
                const routeB = dataB.routes[0].geometry;
                if (trackingMap.getSource('track-route-2')) {
                    trackingMap.getSource('track-route-2').setData({ 'type': 'Feature', 'properties': {}, 'geometry': routeB });
                } else {
                    trackingMap.addSource('track-route-2', { 'type': 'geojson', 'data': { 'type': 'Feature', 'properties': {}, 'geometry': routeB } });
                    trackingMap.addLayer({ 'id': 'track-route-2', 'type': 'line', 'source': 'track-route-2', 'layout': { 'line-join': 'round', 'line-cap': 'round' }, 'paint': { 'line-color': '#10b981', 'line-width': 5 } });
                }
            }

            // Update Info Stats using combined duration/distance if available (sum of legs)
            let totalDuration = 0, totalDistance = 0;
            if (dataA.routes && dataA.routes[0]) {
                totalDuration += dataA.routes[0].duration;
                totalDistance += dataA.routes[0].distance;
            }
            if (dataB.routes && dataB.routes[0]) {
                totalDuration += dataB.routes[0].duration;
                totalDistance += dataB.routes[0].distance;
            }
            if (totalDuration && totalDistance) {
                const duration = Math.round(totalDuration / 60);
                const distance = (totalDistance / 1000).toFixed(1);
                const distEl = document.getElementById('track-dist');
                const timeEl = document.getElementById('track-time');
                if (distEl) distEl.textContent = distance;
                if (timeEl) timeEl.textContent = duration;
            }

        } catch (e) { console.error('drawTrackingRoute error', e); }
    }

    // --- 4. SHARED HELPERS ---
    async function drawStaticRoute(mapInstance, ride) {
        const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${ride.pickup_lng},${ride.pickup_lat};${ride.dropoff_lng},${ride.dropoff_lat}?geometries=geojson&access_token=${mapboxgl.accessToken}`;
        try {
            const res = await fetch(url);
            const data = await res.json();
            if (data.routes && data.routes[0]) {
                const route = data.routes[0].geometry;
                const srcId = 'static-route';
                if (mapInstance.getSource(srcId)) {
                    mapInstance.getSource(srcId).setData({ 'type': 'Feature', 'properties': {}, 'geometry': route });
                } else {
                    mapInstance.addSource(srcId, { 'type': 'geojson', 'data': { 'type': 'Feature', 'properties': {}, 'geometry': route } });
                    mapInstance.addLayer({ 'id': srcId, 'type': 'line', 'source': srcId, 'layout': {'line-join': 'round'}, 'paint': { 'line-color': '#10b981', 'line-width': 4 } });
                }
            }
        } catch (e) { console.error('drawStaticRoute error', e); }
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