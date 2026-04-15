// PATH: app/static/js/map.js
const ISLAND_COORDS = {
  "Trinidad": [10.6918, -61.2225],
  "Tobago": [11.1851, -60.6893],
  "Barbados": [13.1939, -59.5432],
  "Jamaica": [18.1096, -77.2975],
  "St. Lucia": [13.9094, -60.9789],
  "Grenada": [12.1165, -61.6790],
  "Antigua": [17.0608, -61.7964],
  "St. Vincent": [13.2528, -61.1971],
  "Dominica": [15.4150, -61.3710],
  "St. Kitts": [17.3578, -62.7830],
  "Bahamas": [25.0343, -77.3963],
  "Cayman Islands": [19.3133, -81.2546],
  "Martinique": [14.6415, -61.0242],
  "Guadeloupe": [16.9950, -62.0676],
  "Curaçao": [12.1696, -68.9900],
  "Aruba": [12.5211, -69.9683],
  "Puerto Rico": [18.2208, -66.5901],
  "Haiti": [18.9712, -72.2852],
  "Dominican Republic": [18.7357, -70.1627],
  "Other": [15.0000, -65.0000],
};

const CATEGORIES = {
  "Music":        { color: "#8b5cf6", bg: "#ede9fe", icon: "♪" },
  "Food & Drink": { color: "#f59e0b", bg: "#fef3c7", icon: "◈" },
  "Sports":       { color: "#10b981", bg: "#d1fae5", icon: "◉" },
  "Culture & Arts": { color: "#3b82f6", bg: "#dbeafe", icon: "✦" },
  "Nightlife":    { color: "#ec4899", bg: "#fce7f3", icon: "★" },
  "Festival":     { color: "#ef4444", bg: "#fee2e2", icon: "◆" },
  "Carnival":     { color: "#f97316", bg: "#ffedd5", icon: "◈" },
  "Business":     { color: "#6b7280", bg: "#f3f4f6", icon: "▪" },
  "Other":        { color: "#64748b", bg: "#f1f5f9", icon: "•" },
};

function isUpcoming(iso) {
  const d = new Date(iso);
  const diff = (d - new Date()) / (1000 * 60 * 60 * 24);
  return diff >= 0 && diff <= 7;
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("en-TT", {
    weekday: "short", day: "numeric", month: "short", year: "numeric",
  });
}

function formatPrice(price) {
  if (price === null || price === undefined || price === 0) return "Free";
  return `TT$${parseFloat(price).toFixed(2)}`;
}

function makeMarkerIcon(category, upcoming) {
  const cat = CATEGORIES[category] || CATEGORIES["Other"];
  const size = upcoming ? 36 : 30;
  const pulseRing = upcoming
    ? `<div style="position:absolute;top:50%;left:50%;width:${size}px;height:${size}px;margin:-${size/2}px;border-radius:50%;background:${cat.color};opacity:0;animation:pulse-ring 1.8s ease-out infinite;"></div>`
    : "";
  const svg = `
    <div style="position:relative;width:${size}px;height:${size+8}px;">
      ${pulseRing}
      <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size+8}" viewBox="0 0 ${size} ${size+8}" style="filter:drop-shadow(0 2px 4px rgba(0,0,0,.25))">
        <path d="M${size/2} 0C${size*.224} 0 0 ${size*.224} 0 ${size/2}c0 ${size*.345} ${size/2} ${size*.286} ${size/2} ${size*.286}S${size} ${size*.845} ${size} ${size/2}C${size} ${size*.224} ${size*.776} 0 ${size/2} 0z"
              fill="${cat.color}" />
        <circle cx="${size/2}" cy="${size/2}" r="${size*.28}" fill="rgba(255,255,255,0.95)" />
        <text x="${size/2}" y="${size/2+5}" text-anchor="middle" font-size="${size*.3}" font-family="Poppins, sans-serif" fill="${cat.color}" font-weight="700">${cat.icon}</text>
      </svg>
    </div>`;
  return L.divIcon({
    html: svg,
    className: "",
    iconSize: [size, size+8],
    iconAnchor: [size/2, size+8],
    popupAnchor: [0, -(size+10)],
  });
}

function makePopup(event) {
  const cat = CATEGORIES[event.category] || CATEGORIES["Other"];

  const header = event.image_url
    ? `<div style="height:110px;background:url('${event.image_url}') center/cover no-repeat;position:relative;border-radius:12px 12px 0 0;overflow:hidden;">
         <div style="position:absolute;inset:0;background:linear-gradient(to bottom,transparent 30%,rgba(0,0,0,0.72));"></div>
         <div style="position:absolute;bottom:0;left:0;right:0;padding:10px 12px;">
           <div style="display:inline-block;background:${cat.color};color:#fff;font-size:10px;font-weight:700;padding:2px 7px;border-radius:20px;margin-bottom:4px;letter-spacing:.4px;text-transform:uppercase;">
             ${event.category}
           </div>
           <div style="font-size:13px;font-weight:700;color:#fff;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${event.title}</div>
         </div>
       </div>`
    : `<div style="padding:14px 14px 10px;background:${cat.color};border-radius:12px 12px 0 0;">
         <div style="display:inline-block;background:rgba(255,255,255,.2);color:#fff;font-size:10px;font-weight:700;padding:2px 7px;border-radius:20px;margin-bottom:5px;letter-spacing:.4px;text-transform:uppercase;">
           ${event.category}
         </div>
         <div style="font-size:13px;font-weight:700;color:#fff;line-height:1.3;">${event.title}</div>
       </div>`;

  const priceColor = (event.price === null || event.price === undefined || event.price === 0)
    ? "#10b981"
    : cat.color;

  const body = `
    <div style="padding:10px 12px 4px;">
      <div style="display:flex;align-items:flex-start;gap:6px;margin-bottom:6px;font-size:12px;color:#374151;line-height:1.3;">
        <span style="flex-shrink:0;font-size:13px;">📍</span>
        <span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${event.venue}</span>
      </div>
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;font-size:12px;color:#374151;">
        <span style="flex-shrink:0;font-size:13px;">📅</span>
        <span>${formatDate(event.date)}</span>
      </div>
      <div style="display:flex;align-items:center;gap:6px;font-size:12px;">
        <span style="flex-shrink:0;font-size:13px;">💰</span>
        <span style="font-weight:700;color:${priceColor};">${formatPrice(event.price)}</span>
        <span style="margin-left:auto;">
          <span style="display:inline-block;background:${cat.bg};color:${cat.color};font-size:10px;font-weight:600;padding:1px 7px;border-radius:20px;">
            ${event.island}
          </span>
        </span>
      </div>
    </div>`;

  const footer = `
    <div style="padding:8px 12px 12px;">
      <a href="/events/${event.id}"
         style="display:block;text-align:center;background:${cat.color};color:#fff;text-decoration:none;
                font-size:12px;font-weight:700;padding:8px 12px;border-radius:8px;
                transition:opacity .15s;letter-spacing:.3px;"
         onmouseover="this.style.opacity='.85'" onmouseout="this.style.opacity='1'">
        View Details →
      </a>
    </div>`;

  return `<div style="width:240px;border-radius:12px;overflow:hidden;font-family:Poppins,sans-serif;">
    ${header}${body}${footer}
  </div>`;
}

function makeClusterIcon(cluster) {
  const count = cluster.getChildCount();
  const size = count < 10 ? 36 : count < 100 ? 42 : 48;
  return L.divIcon({
    html: `<div class="cluster-icon" style="width:${size}px;height:${size}px">${count}</div>`,
    className: "",
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
  });
}

function initMap(events) {
  const map = L.map("map", {
    center: [14.5, -66.0],
    zoom: 6,
    zoomControl: false,
  });

  L.control.zoom({ position: "bottomright" }).addTo(map);

  L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OSM</a> © <a href="https://carto.com/">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 19,
  }).addTo(map);

  let activeCategories = new Set(Object.keys(CATEGORIES));
  let searchTerm = "";
  let activeMarkerId = null;
  const markerMap = {};

  const clusterGroup = L.markerClusterGroup({
    iconCreateFunction: makeClusterIcon,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true,
    maxClusterRadius: 60,
    disableClusteringAtZoom: 12,
  });

  events.forEach((event) => {
    const coords = ISLAND_COORDS[event.island] || ISLAND_COORDS["Other"];
    const jitter = () => (Math.random() - 0.5) * 0.13;
    const pos = [coords[0] + jitter(), coords[1] + jitter()];
    const upcoming = isUpcoming(event.date);

    const marker = L.marker(pos, { icon: makeMarkerIcon(event.category, upcoming) });
    marker.bindPopup(makePopup(event), { maxWidth: 260, className: "fancy-popup" });
    marker.on("click", () => setActiveSidebarItem(event.id));
    marker.eventId = event.id;
    markerMap[event.id] = { marker, pos, event };
    clusterGroup.addLayer(marker);
  });

  map.addLayer(clusterGroup);

  const filtersEl = document.getElementById("catFilters");
  if (filtersEl) {
    Object.entries(CATEGORIES).forEach(([name, cat]) => {
      const pill = document.createElement("button");
      pill.className = "cat-pill";
      pill.style.borderColor = cat.color;
      pill.style.color = cat.color;
      pill.innerHTML = `<span class="cat-dot" style="background:${cat.color}"></span>${name}`;
      pill.title = `Toggle ${name}`;
      pill.addEventListener("click", () => {
        if (activeCategories.has(name)) {
          activeCategories.delete(name);
          pill.classList.add("off");
        } else {
          activeCategories.add(name);
          pill.classList.remove("off");
        }
        renderSidebar();
        updateMarkers();
      });
      filtersEl.appendChild(pill);
    });
  }

  function getFilteredEvents() {
    return events.filter(e => {
      const matchesCat = activeCategories.has(e.category);
      const matchesSearch = !searchTerm ||
        e.title.toLowerCase().includes(searchTerm) ||
        e.venue.toLowerCase().includes(searchTerm) ||
        e.island.toLowerCase().includes(searchTerm);
      return matchesCat && matchesSearch;
    }).sort((a, b) => new Date(a.date) - new Date(b.date));
  }

  function renderSidebar() {
    const list = document.getElementById("sidebarList");
    const count = document.getElementById("sidebarCount");
    if (!list) return;

    const filtered = getFilteredEvents();
    if (count) count.textContent = `${filtered.length} event${filtered.length !== 1 ? "s" : ""}`;

    list.innerHTML = "";
    if (!filtered.length) {
      list.innerHTML = `<div style="padding:24px;text-align:center;color:#9ca3af;font-size:13px">No events match your filters</div>`;
      return;
    }

    filtered.forEach(event => {
      const cat = CATEGORIES[event.category] || CATEGORIES["Other"];
      const item = document.createElement("div");
      item.className = "sidebar-item" + (event.id === activeMarkerId ? " active" : "");
      item.dataset.eventId = event.id;
      item.innerHTML = `
        <div class="si-title">${event.title}</div>
        <div class="si-meta">
          <span><span class="si-dot" style="background:${cat.color}"></span>${event.category}</span>
          <span>${event.island}</span>
          <span>${formatDate(event.date)}</span>
        </div>`;
      item.addEventListener("click", () => flyToEvent(event.id));
      list.appendChild(item);
    });
  }

  function updateMarkers() {
    clusterGroup.clearLayers();
    events.forEach(event => {
      if (activeCategories.has(event.category)) {
        clusterGroup.addLayer(markerMap[event.id].marker);
      }
    });
  }

  function flyToEvent(id) {
    const m = markerMap[id];
    if (!m) return;
    setActiveSidebarItem(id);
    map.flyTo(m.pos, 13, { duration: 0.8 });
    setTimeout(() => m.marker.openPopup(), 900);
  }

  function setActiveSidebarItem(id) {
    activeMarkerId = id;
    document.querySelectorAll(".sidebar-item").forEach(el => {
      el.classList.toggle("active", parseInt(el.dataset.eventId) === id);
    });
    const activeEl = document.querySelector(`.sidebar-item[data-event-id="${id}"]`);
    if (activeEl) activeEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  const searchEl = document.getElementById("sidebarSearch");
  if (searchEl) {
    let debounce;
    searchEl.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        searchTerm = searchEl.value.trim().toLowerCase();
        renderSidebar();
      }, 200);
    });
  }

  renderSidebar();
  return map;
}
