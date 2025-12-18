document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. SETUP ---
    mapboxgl.accessToken = window.mapboxAccessToken;
    let modalMap = null;
    let currentRideId = null;

    // --- 2. MODAL LOGIC ---
    const modal = document.getElementById('ride-request-modal');
    const acceptBtn = document.getElementById('btn-accept-ride');

    window.openRideModal = async function(rideId) {
        currentRideId = rideId;
        
        // Show Modal
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        // Show Loading State
        document.getElementById('modal-client-name').textContent = "Loading...";

        // Fetch Details
        try {
            const res = await fetch(`${window.rideDetailsBaseUrl}${rideId}/`);
            const data = await res.json();
            
            if(data.success) {
                const ride = data.ride;
                
                // Populate Text
                document.getElementById('modal-client-name').textContent = ride.customer_name;
                document.getElementById('modal-pickup').textContent = ride.pickup;
                document.getElementById('modal-dropoff').textContent = ride.dropoff;
                document.getElementById('modal-distance').textContent = ride.distance + " km";
                document.getElementById('modal-duration').textContent = ride.duration + " min";
                document.getElementById('modal-earning').textContent = "RWF " + Math.round(ride.est_earning);
                
                if(ride.customer_avatar) {
                    document.getElementById('modal-avatar').innerHTML = `<img src="${ride.customer_avatar}" class="w-full h-full object-cover">`;
                }

                // Initialize Map
                initModalMap(ride);
            }
        } catch(e) {
            console.error("Error fetching ride details", e);
            alert("Could not load ride details.");
            closeRideModal();
        }
    };

    window.closeRideModal = function() {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        currentRideId = null;
    };

    // --- 3. MAP IN MODAL ---
    function initModalMap(ride) {
        if(!modalMap) {
            modalMap = new mapboxgl.Map({
                container: 'modal-map',
                style: 'mapbox://styles/mapbox/streets-v12',
                center: [ride.pickup_lng, ride.pickup_lat],
                zoom: 11
            });
        }

        // Resize fix for modals
        setTimeout(() => {
            modalMap.resize();
            
            // Fit Bounds to show full route
            const bounds = new mapboxgl.LngLatBounds()
                .extend([ride.pickup_lng, ride.pickup_lat])
                .extend([ride.dropoff_lng, ride.dropoff_lat]);
            
            modalMap.fitBounds(bounds, { padding: 40 });

            // Add Markers (Clear old ones first if needed, simpler to just add new ones for MVP)
            new mapboxgl.Marker({ color: '#22c55e' }).setLngLat([ride.pickup_lng, ride.pickup_lat]).addTo(modalMap);
            new mapboxgl.Marker({ color: '#ef4444' }).setLngLat([ride.dropoff_lng, ride.dropoff_lat]).addTo(modalMap);
            
            // Draw Route (Visual Line)
            drawRoute(ride.pickup_lng, ride.pickup_lat, ride.dropoff_lng, ride.dropoff_lat);
        }, 300);
    }

    async function drawRoute(startLng, startLat, endLng, endLat) {
        const url = `https://api.mapbox.com/directions/v5/mapbox/driving/${startLng},${startLat};${endLng},${endLat}?geometries=geojson&access_token=${mapboxgl.accessToken}`;
        const res = await fetch(url);
        const data = await res.json();
        
        if (data.routes && data.routes[0]) {
            const route = data.routes[0].geometry;
            
            if (modalMap.getSource('modal-route')) {
                modalMap.getSource('modal-route').setData({
                    'type': 'Feature',
                    'properties': {},
                    'geometry': route
                });
            } else {
                modalMap.addSource('modal-route', {
                    'type': 'geojson',
                    'data': {
                        'type': 'Feature',
                        'properties': {},
                        'geometry': route
                    }
                });
                modalMap.addLayer({
                    'id': 'modal-route',
                    'type': 'line',
                    'source': 'modal-route',
                    'layout': { 'line-join': 'round', 'line-cap': 'round' },
                    'paint': { 'line-color': '#3b82f6', 'line-width': 4 }
                });
            }
        }
    }

    // --- 4. ACCEPT ACTION ---
    acceptBtn.addEventListener('click', async () => {
        if(!currentRideId) return;
        
        acceptBtn.disabled = true;
        acceptBtn.textContent = "Accepting...";

        try {
            const res = await fetch(`${window.acceptRideBaseUrl}${currentRideId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            const data = await res.json();
            
            if(data.success) {
                alert("Ride Accepted! Redirecting to navigation...");
                window.location.reload(); // Reload to show active ride view
            } else {
                alert("Error: " + data.error);
                acceptBtn.disabled = false;
                acceptBtn.textContent = "Accept Ride";
            }
        } catch(e) {
            console.error(e);
            alert("Network Error");
            acceptBtn.disabled = false;
            acceptBtn.textContent = "Accept Ride";
        }
    });

    // --- 5. LOCATION TRACKING (Every 5 mins = 300000ms) ---
    // Note: 5 mins is very sparse for a "live" app. 
    // Drivers moving at 60km/h will jump 5km between updates.
    // Recommended: 30s (30000) or 1min (60000). I will use 5min as requested.
    
    function sendLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(async (pos) => {
                try {
                    await fetch(window.updateLocationUrl, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': window.csrfToken,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            latitude: pos.coords.latitude,
                            longitude: pos.coords.longitude
                        })
                    });
                    console.log("Location updated");
                } catch(e) {
                    console.error("Location update failed", e);
                }
            });
        }
    }

    // Send immediately on load, then interval
    sendLocation();
    setInterval(sendLocation, 300000); // 5 minutes
});