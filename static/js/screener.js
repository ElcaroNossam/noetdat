document.addEventListener("DOMContentLoaded", () => {
    const screenerTableBody = document.getElementById("screener-table-body");
    const autoRefreshIntervalMs = 1000; // 1s for main screener

    const availableColumns = window.SCREENER_AVAILABLE_COLUMNS || [];
    const storageKey = "screener_visible_columns";

    // Default visible columns (matching initial display)
    const defaultVisible = new Set([
        "symbol",
        "price",
        "change_15m",
        "volume_15m",
        "oi_change_15m",
        "funding_rate",
        "open_interest",
        "ts",
    ]);

    function loadVisibleColumns() {
        try {
            const raw = localStorage.getItem(storageKey);
            if (!raw) return defaultVisible;
            const parsed = JSON.parse(raw);
            if (!Array.isArray(parsed)) return defaultVisible;
            return new Set(parsed);
        } catch (e) {
            return defaultVisible;
        }
    }

    function saveVisibleColumns(set) {
        try {
            localStorage.setItem(storageKey, JSON.stringify(Array.from(set)));
        } catch (e) {
            // ignore
        }
    }

    const visibleColumns = loadVisibleColumns();

    function applyColumnVisibility() {
        // Apply visibility even if availableColumns is not set yet (for server-rendered HTML)
        const table = document.getElementById("screener-main-table");
        if (!table) return;
        
        // If availableColumns is not set, try to get columns from table headers
        const allColumns = availableColumns.length > 0 
            ? availableColumns 
            : Array.from(table.querySelectorAll("thead th[data-column]")).map(th => th.getAttribute("data-column")).filter(Boolean);
        
        if (allColumns.length === 0) return;

        // Apply to header cells - use more reliable method
        const headerCells = table.querySelectorAll("thead th[data-column]");
        headerCells.forEach((th) => {
            const col = th.getAttribute("data-column");
            if (!col) return;
            const visible = visibleColumns.has(col);
            // Force hide/show with !important via style attribute
            if (visible) {
                th.style.display = "table-cell";
                th.style.visibility = "visible";
                th.style.opacity = "1";
                th.removeAttribute("hidden");
                th.classList.remove("hidden-column");
            } else {
                th.style.display = "none";
                th.style.visibility = "hidden";
                th.style.opacity = "0";
                th.setAttribute("hidden", "true");
                th.classList.add("hidden-column");
            }
        });

        // Apply to body cells - use more reliable method
        const rows = table.querySelectorAll("tbody tr");
        rows.forEach((tr) => {
            tr.querySelectorAll("td[data-column]").forEach((td) => {
                const col = td.getAttribute("data-column");
                if (!col) return;
                const visible = visibleColumns.has(col);
                // Force hide/show with !important via style attribute
                if (visible) {
                    td.style.display = "table-cell";
                    td.style.visibility = "visible";
                    td.style.opacity = "1";
                    td.removeAttribute("hidden");
                    td.classList.remove("hidden-column");
                } else {
                    td.style.display = "none";
                    td.style.visibility = "hidden";
                    td.style.opacity = "0";
                    td.setAttribute("hidden", "true");
                    td.classList.add("hidden-column");
                }
            });
        });

        // Update checkboxes in settings panel if it exists.
        document
            .querySelectorAll(".screener-settings input[type=checkbox][data-column]")
            .forEach((cb) => {
                const col = cb.getAttribute("data-column");
                if (!col) return;
                cb.checked = visibleColumns.has(col);
                const label = cb.closest("label.settings-button");
                if (label) {
                    if (cb.checked) label.classList.add("selected");
                    else label.classList.remove("selected");
                }
            });
    }

    function buildSettingsPanel() {
        const btn = document.getElementById("toggle-settings");
        if (!btn) return;

        let panel = document.querySelector(".screener-settings");
        if (!panel) {
            panel = document.createElement("div");
            panel.className = "screener-settings";
            document.body.appendChild(panel);
        }
        
        // Clear existing event listeners by removing and re-adding panel content
        const existingInner = panel.querySelector(".screener-settings-inner");
        if (existingInner) {
            existingInner.remove();
        }

        const categories = {
            "Change": ["change_5m", "change_15m", "change_1h", "change_8h", "change_1d"],
            "OI Change": ["oi_change_5m", "oi_change_15m", "oi_change_1h", "oi_change_8h", "oi_change_1d"],
            "Volatility": ["volatility_5m", "volatility_15m", "volatility_1h"],
            "Ticks": ["ticks_5m", "ticks_15m", "ticks_1h"],
            "Vdelta": ["vdelta_5m", "vdelta_15m", "vdelta_1h", "vdelta_8h", "vdelta_1d"],
            "Volume": ["volume_5m", "volume_15m", "volume_1h", "volume_8h", "volume_1d"],
            "Others": ["symbol", "price", "funding_rate", "open_interest", "ts"],
        };

        let html = `
            <div class="screener-settings-inner">
                <div class="settings-header">
                    <h2>Screener Settings</h2>
                    <button type="button" class="close-settings" id="close-settings">×</button>
                </div>
                <p class="chart-note">Customize the table display by selecting the columns you want to see.</p>
                <div class="settings-columns">
        `;

        for (const [category, cols] of Object.entries(categories)) {
            html += `<div class="settings-category"><strong>${category}:</strong><div class="settings-buttons">`;
            cols.forEach((col) => {
                const checked = visibleColumns.has(col) ? "checked" : "";
                const selected = visibleColumns.has(col) ? "selected" : "";
                const label = col.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
                html += `<label class="settings-button ${selected}" data-column="${col}">
                    <input type="checkbox" data-column="${col}" ${checked} style="display:none">
                    ${label}
                </label>`;
            });
            html += `</div></div>`;
        }

        html += `
                </div>
                <div class="settings-footer">
                    <div class="settings-reset">
                        <span>Restore Default Column Order</span>
                        <button type="button" class="btn-secondary" id="reset-settings">Reset</button>
                    </div>
                </div>
            </div>
        `;

        panel.innerHTML = html;

        // Use event delegation for better reliability
        panel.addEventListener("click", (e) => {
            const label = e.target.closest("label.settings-button");
            if (!label) return;
            
            e.preventDefault();
            e.stopPropagation();
            
            const cb = label.querySelector("input[type=checkbox]");
            if (!cb) return;
            
            const col = label.dataset.column;
            if (!col) {
                console.warn("No column attribute found on label");
                return;
            }
            
            // Toggle checkbox state
            cb.checked = !cb.checked;
            
            // Update visibleColumns set
            if (cb.checked) {
                visibleColumns.add(col);
                label.classList.add("selected");
            } else {
                visibleColumns.delete(col);
                label.classList.remove("selected");
            }
            
            // Save to localStorage
            saveVisibleColumns(visibleColumns);
            
            // Immediately apply visibility changes - use requestAnimationFrame for reliable DOM update
            requestAnimationFrame(() => {
                applyColumnVisibility();
            });
        });

        panel.querySelector("#close-settings").addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            panel.classList.remove("open");
        });

        panel.querySelector("#reset-settings").addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            visibleColumns.clear();
            defaultVisible.forEach((col) => visibleColumns.add(col));
            saveVisibleColumns(visibleColumns);
            applyColumnVisibility();
            // Rebuild panel to update checkboxes
            buildSettingsPanel();
        });

        // Close on background click
        panel.addEventListener("click", (e) => {
            if (e.target === panel) {
                panel.classList.remove("open");
            }
        });
    }

    // Attach toggle button handler (outside buildSettingsPanel to avoid duplicates)
    function attachToggleButton() {
        const btn = document.getElementById("toggle-settings");
        if (!btn) return;
        
        // Remove all existing click handlers by cloning
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        newBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            const panel = document.querySelector(".screener-settings");
            if (panel) {
                panel.classList.toggle("open");
            }
        });
    }

    // Add sorting functionality to table headers
    function setupTableSorting() {
        const table = document.getElementById("screener-main-table");
        if (!table) return;

        const headers = table.querySelectorAll("thead th[data-column]");
        headers.forEach((th) => {
            const col = th.getAttribute("data-column");
            if (col === "symbol" || col === "ts") {
                // Make these sortable
                th.style.cursor = "pointer";
                th.addEventListener("click", () => {
                    sortTable(col);
                });
            } else if (["price", "change_5m", "change_15m", "change_1h", "change_8h", "change_1d",
                        "oi_change_5m", "oi_change_15m", "oi_change_1h", "oi_change_8h", "oi_change_1d",
                        "volatility_5m", "volatility_15m", "volatility_1h",
                        "ticks_5m", "ticks_15m", "ticks_1h",
                        "vdelta_5m", "vdelta_15m", "vdelta_1h", "vdelta_8h", "vdelta_1d",
                        "volume_5m", "volume_15m", "volume_1h", "volume_8h", "volume_1d",
                        "funding_rate", "open_interest"].includes(col)) {
                th.style.cursor = "pointer";
                th.addEventListener("click", () => {
                    sortTable(col);
                });
            }
        });
    }

    function sortTable(column) {
        const url = new URL(window.location);
        const currentSort = url.searchParams.get("sort");
        const currentOrder = url.searchParams.get("order");

        let newOrder = "desc";
        if (currentSort === column && currentOrder === "desc") {
            newOrder = "asc";
        }

        // Preserve all existing query parameters (filters, etc.)
        url.searchParams.set("sort", column);
        url.searchParams.set("order", newOrder);
        window.location.href = url.toString();
    }

    function buildQueryFromCurrentLocation() {
        const url = new URL(window.location);
        // Ensure market_type is preserved
        if (!url.searchParams.has("market_type")) {
            url.searchParams.set("market_type", "futures");
        }
        return url.search || "?";
    }

    function formatPrice(v) {
        if (v === null || v === undefined) return "";
        const value = Number(v);
        if (isNaN(value)) return String(v);
        const absV = Math.abs(value);
        if (absV >= 1) return value.toFixed(2);
        if (absV >= 0.01) return value.toFixed(4);
        return value.toFixed(8);
    }

    function formatVolume(v) {
        if (v === null || v === undefined || v === "") return "0.00";
        const value = Number(v);
        if (isNaN(value) || value === 0) return "0.00";
        const absV = Math.abs(value);
        if (absV >= 1_000_000_000) return (value / 1_000_000_000).toFixed(2) + "B";
        if (absV >= 1_000_000) return (value / 1_000_000).toFixed(2) + "M";
        if (absV >= 1_000) return (value / 1_000).toFixed(2) + "K";
        return value.toFixed(2);
    }

    async function refreshScreener() {
        if (!screenerTableBody) return;
        try {
            const query = buildQueryFromCurrentLocation();
            const url = "/api/screener/" + query.replace(/^\?/, "?");
            const resp = await fetch(url);
            if (!resp.ok) return;

            const data = await resp.json();
            renderScreenerTable(data);
            // Always reapply column visibility immediately after rendering
            applyColumnVisibility();
        } catch (e) {
            console.error("Failed to refresh screener", e);
        }
    }

    function renderScreenerTable(rows) {
        if (!screenerTableBody) return;
        screenerTableBody.innerHTML = "";
        if (!rows.length) {
            const tr = document.createElement("tr");
            const td = document.createElement("td");
            td.colSpan = 31;
            td.className = "empty-row";
            td.textContent = "Нет данных для отображения.";
            tr.appendChild(td);
            screenerTableBody.appendChild(tr);
            return;
        }

        for (const row of rows) {
            const tr = document.createElement("tr");

            const makeTd = (col, text, className) => {
                const td = document.createElement("td");
                td.dataset.column = col;
                if (className) td.className = className;
                td.textContent = text;
                return td;
            };

            const symbolTd = document.createElement("td");
            symbolTd.dataset.column = "symbol";
            const link = document.createElement("a");
            const marketType = new URLSearchParams(window.location.search).get("market_type") || "futures";
            link.href = `/symbol/${row.symbol}/?market_type=${marketType}`;
            link.textContent = row.symbol;
            symbolTd.appendChild(link);

            tr.appendChild(symbolTd);
            tr.appendChild(makeTd("price", formatPrice(row.price)));

            // Change columns
            ["change_5m", "change_15m", "change_1h", "change_8h", "change_1d"].forEach((col) => {
                const v = row[col] ?? 0;
                let cls = "";
                if (v > 0) cls = "value-up";
                else if (v < 0) cls = "value-down";
                tr.appendChild(makeTd(col, v?.toFixed ? v.toFixed(2) : v, cls));
            });

            // OI Change columns
            ["oi_change_5m", "oi_change_15m", "oi_change_1h", "oi_change_8h", "oi_change_1d"].forEach((col) => {
                const v = row[col] ?? 0;
                let cls = "";
                if (v > 0) cls = "value-up";
                else if (v < 0) cls = "value-down";
                tr.appendChild(makeTd(col, v?.toFixed ? v.toFixed(3) : v, cls));
            });

            // Volatility columns
            ["volatility_5m", "volatility_15m", "volatility_1h"].forEach((col) => {
                const v = row[col] ?? 0;
                tr.appendChild(makeTd(col, v?.toFixed ? v.toFixed(2) : v));
            });

            // Ticks columns
            ["ticks_5m", "ticks_15m", "ticks_1h"].forEach((col) => {
                tr.appendChild(makeTd(col, row[col] ?? 0));
            });

            // Vdelta columns
            ["vdelta_5m", "vdelta_15m", "vdelta_1h", "vdelta_8h", "vdelta_1d"].forEach((col) => {
                const v = row[col] ?? 0;
                tr.appendChild(makeTd(col, v?.toFixed ? v.toFixed(2) : v));
            });

            // Volume columns
            ["volume_5m", "volume_15m", "volume_1h", "volume_8h", "volume_1d"].forEach((col) => {
                tr.appendChild(makeTd(col, formatVolume(row[col])));
            });

            // Funding
            const funding = row.funding_rate ?? 0;
            let fundClass = "";
            if (funding > 0) fundClass = "value-up";
            else if (funding < 0) fundClass = "value-down";
            tr.appendChild(makeTd("funding_rate", funding?.toFixed ? funding.toFixed(6) : funding, fundClass));

            // Open Interest - ensure it's a number
            const oiValue = row.open_interest != null ? Number(row.open_interest) : 0;
            tr.appendChild(makeTd("open_interest", formatVolume(oiValue)));

            // Timestamp
            tr.appendChild(makeTd("ts", row.ts));

            screenerTableBody.appendChild(tr);
        }
        // Apply visibility immediately after rendering all rows
        applyColumnVisibility();
    }

    // Sync top and bottom scrollbars
    function syncScrollbars() {
        const topScrollbar = document.getElementById("top-scrollbar");
        const tableWrapper = document.getElementById("table-wrapper");
        const scrollbarSpacer = document.getElementById("scrollbar-spacer");
        
        if (!topScrollbar || !tableWrapper || !scrollbarSpacer) return;
        
        const table = document.getElementById("screener-main-table");
        if (table) {
            // Set spacer width to match table width
            scrollbarSpacer.style.width = table.scrollWidth + "px";
        }
        
        // Sync scrolling from bottom to top
        tableWrapper.addEventListener("scroll", () => {
            topScrollbar.scrollLeft = tableWrapper.scrollLeft;
        });
        
        // Sync scrolling from top to bottom
        topScrollbar.addEventListener("scroll", () => {
            tableWrapper.scrollLeft = topScrollbar.scrollLeft;
        });
    }

    // Initialize main screener auto-refresh if we are on the list page.
    if (screenerTableBody) {
        // Apply column visibility IMMEDIATELY on page load (for server-rendered HTML)
        // Use multiple attempts to ensure it applies
        applyColumnVisibility();
        setTimeout(() => applyColumnVisibility(), 0);
        requestAnimationFrame(() => {
            applyColumnVisibility();
        });
        
        // Build settings panel
        buildSettingsPanel();
        attachToggleButton();
        setupTableSorting();
        // Sync scrollbars
        syncScrollbars();
        // Start auto-refresh
        refreshScreener();
        setInterval(refreshScreener, autoRefreshIntervalMs);
        
        // Update scrollbar spacer after table updates
        const observer = new MutationObserver(() => {
            setTimeout(() => {
                const scrollbarSpacer = document.getElementById("scrollbar-spacer");
                const table = document.getElementById("screener-main-table");
                if (scrollbarSpacer && table) {
                    scrollbarSpacer.style.width = table.scrollWidth + "px";
                }
            }, 100);
        });
        observer.observe(screenerTableBody, { childList: true, subtree: true });
    }

    // --- Symbol detail auto-refresh ---
    const symbolContainer = document.querySelector("[data-symbol-detail]");
    if (symbolContainer) {
        const symbol = symbolContainer.getAttribute("data-symbol");
        const symbolIntervalMs = 5000; // 5s for symbol detail

        async function fetchSymbolData() {
            if (!symbol) return;
            try {
                const resp = await fetch(`/api/symbol/${encodeURIComponent(symbol)}/`);
                if (!resp.ok) return;
                const data = await resp.json();
                renderSymbolDetail(data);
            } catch (e) {
                console.error("Failed to refresh symbol detail", e);
            }
        }

        function renderSymbolDetail(data) {
            if (!data) return;
            const latest = data.latest || null;
            if (latest) {
                const priceEl = document.getElementById("symbol-price");
                const vol15El = document.getElementById("symbol-volatility-15m");
                const vol5mEl = document.getElementById("symbol-volume-5m");
                const oi15El = document.getElementById("symbol-oi-change-15m");
                const fundingEl = document.getElementById("symbol-funding-rate");
                const oiEl = document.getElementById("symbol-open-interest");
                const updatedEl = document.getElementById("symbol-updated-at");

                if (priceEl) priceEl.textContent = formatPrice(latest.price);
                if (vol15El) vol15El.textContent = latest.volatility_15m?.toFixed
                    ? latest.volatility_15m.toFixed(2)
                    : latest.volatility_15m;
                if (vol5mEl) vol5mEl.textContent = formatVolume(latest.volume_5m);
                if (fundingEl) {
                    fundingEl.textContent = latest.funding_rate?.toFixed
                        ? latest.funding_rate.toFixed(6)
                        : latest.funding_rate;
                }
                if (oiEl) oiEl.textContent = formatVolume(latest.open_interest);
                if (updatedEl) updatedEl.textContent = latest.ts || "";
                if (oi15El) {
                    const v = latest.oi_change_15m ?? 0;
                    oi15El.textContent = v?.toFixed ? v.toFixed(3) : v;
                    oi15El.classList.remove("value-up", "value-down");
                    if (v > 0) oi15El.classList.add("value-up");
                    else if (v < 0) oi15El.classList.add("value-down");
                }
            }

            const body = document.getElementById("symbol-history-body");
            if (!body) return;
            const snapshots = data.snapshots || [];
            body.innerHTML = "";
            if (!snapshots.length) {
                const tr = document.createElement("tr");
                const td = document.createElement("td");
                td.colSpan = 7;
                td.className = "empty-row";
                td.textContent = "Нет данных.";
                tr.appendChild(td);
                body.appendChild(tr);
                return;
            }

            snapshots.forEach((s) => {
                const tr = document.createElement("tr");

                const tsTd = document.createElement("td");
                tsTd.textContent = s.ts;

                const priceTd = document.createElement("td");
                priceTd.textContent = formatPrice(s.price);

                const change15Td = document.createElement("td");
                const c15 = s.change_15m ?? 0;
                change15Td.textContent = c15?.toFixed ? c15.toFixed(2) : c15;
                if (c15 > 0) change15Td.classList.add("value-up");
                else if (c15 < 0) change15Td.classList.add("value-down");

                const vol15Td = document.createElement("td");
                vol15Td.textContent = formatVolume(s.volume_15m);

                const oiTd = document.createElement("td");
                oiTd.textContent = formatVolume(s.open_interest);

                const oi15Td = document.createElement("td");
                const oi15 = s.oi_change_15m ?? 0;
                oi15Td.textContent = oi15?.toFixed ? oi15.toFixed(3) : oi15;
                if (oi15 > 0) oi15Td.classList.add("value-up");
                else if (oi15 < 0) oi15Td.classList.add("value-down");

                const fundingTd = document.createElement("td");
                const f = s.funding_rate ?? 0;
                fundingTd.textContent = f?.toFixed ? f.toFixed(6) : f;
                if (f > 0) fundingTd.classList.add("value-up");
                else if (f < 0) fundingTd.classList.add("value-down");

                tr.appendChild(tsTd);
                tr.appendChild(priceTd);
                tr.appendChild(change15Td);
                tr.appendChild(vol15Td);
                tr.appendChild(oiTd);
                tr.appendChild(oi15Td);
                tr.appendChild(fundingTd);
                body.appendChild(tr);
            });
        }

        fetchSymbolData();
        setInterval(fetchSymbolData, symbolIntervalMs);
    }
});
