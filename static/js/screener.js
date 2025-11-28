document.addEventListener("DOMContentLoaded", () => {
    const screenerTableBody = document.getElementById("screener-table-body");
    const autoRefreshIntervalMs = 1000; // 1s for main screener

    const availableColumns = window.SCREENER_AVAILABLE_COLUMNS || [];
    const storageKey = "screener_visible_columns";
    
    // Store previous values for comparison (for volume, ticks, volatility, OI)
    let previousValues = new Map(); // key: symbol, value: object with previous values

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

    function formatVdelta(v) {
        if (v === null || v === undefined || v === "") return "0.00";
        const value = Number(v);
        if (isNaN(value)) return "0.00";
        const absV = Math.abs(value);
        // Handle zero case
        if (absV < 0.0001) return "0.00";
        if (absV >= 1_000_000) return (value / 1_000_000).toFixed(2) + "M";
        if (absV >= 1_000) return (value / 1_000).toFixed(2) + "K";
        if (absV >= 1) {
            if (Math.abs(absV - Math.floor(absV)) < 0.0001) return String(Math.floor(value));
            return value.toFixed(1);
        }
        return value.toFixed(2);
    }

    function formatOIChange(v) {
        if (v === null || v === undefined || v === "") return "0.0000";
        const value = Number(v);
        if (isNaN(value)) return "0.0000";
        const absV = Math.abs(value);
        // Handle zero case - only return 0.0000 if truly zero
        // For very small values (< 0.001), always show 6 decimals to distinguish from zero
        if (absV < 0.0000001) return "0.0000";
        if (absV >= 1) return value.toFixed(2);
        if (absV >= 0.1) return value.toFixed(3);
        if (absV >= 0.001) return value.toFixed(4);
        // For very small values (< 0.001), always show 6 decimals
        // This includes negative values like -0.000001 which should show as -0.000001
        return value.toFixed(6);
    }

    function formatVolatility(v) {
        if (v === null || v === undefined || v === "") return "0.000";
        const value = Number(v);
        if (isNaN(value) || value === 0) return "0.000";
        const absV = Math.abs(value);
        if (absV >= 1) return value.toFixed(2);
        return value.toFixed(3);
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

    function getComparisonClass(currentValue, previousValue, isPositiveOnly = false) {
        if (previousValue === null || previousValue === undefined) return "";
        const current = Number(currentValue);
        const previous = Number(previousValue);
        if (isNaN(current) || isNaN(previous)) return "";
        
        if (isPositiveOnly) {
            // For positive-only values (volume, ticks, volatility, OI), compare with previous
            if (current > previous) return "value-up";
            if (current < previous) return "value-down";
            return "";
        } else {
            // For values that can be negative (change, vdelta, funding)
            if (current > 0.0000001) return "value-up";
            if (current < -0.0000001) return "value-down";
            return "";
        }
    }

    function renderScreenerTable(rows) {
        if (!screenerTableBody) return;
        
        // Don't clear previousValues - keep them for comparison
        // Only clear the HTML
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
            const symbol = row.symbol;
            // Get previous values for this symbol, or use empty object if not found
            const prev = previousValues.get(symbol) || {};

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
            link.href = `/trading/${row.symbol}/?market_type=${marketType}`;
            link.textContent = row.symbol;
            symbolTd.appendChild(link);

            tr.appendChild(symbolTd);
            tr.appendChild(makeTd("price", formatPrice(row.price)));

            // Change columns
            ["change_5m", "change_15m", "change_1h", "change_8h", "change_1d"].forEach((col) => {
                const v = row[col] ?? 0;
                const numValue = Number(v);
                let cls = "";
                // Use strict comparison with epsilon for floating point precision
                if (!isNaN(numValue) && numValue > 0.0000001) cls = "value-up";
                else if (!isNaN(numValue) && numValue < -0.0000001) cls = "value-down";
                const formatted = !isNaN(numValue) ? numValue.toFixed(2) : String(v);
                tr.appendChild(makeTd(col, formatted + "%", cls));
            });

            // OI Change columns
            ["oi_change_5m", "oi_change_15m", "oi_change_1h", "oi_change_8h", "oi_change_1d"].forEach((col) => {
                const v = row[col] ?? 0;
                const numValue = Number(v);
                let cls = "";
                // Use strict comparison with epsilon for floating point precision
                if (!isNaN(numValue) && numValue > 0.0000001) cls = "value-up";
                else if (!isNaN(numValue) && numValue < -0.0000001) cls = "value-down";
                const formatted = formatOIChange(v);
                tr.appendChild(makeTd(col, formatted + "%", cls));
            });

            // Volatility columns - compare with previous values
            ["volatility_5m", "volatility_15m", "volatility_1h"].forEach((col) => {
                const v = row[col] ?? 0;
                const formatted = formatVolatility(v);
                const cls = getComparisonClass(v, prev[col], true);
                tr.appendChild(makeTd(col, formatted, cls));
            });

            // Ticks columns - compare with previous values
            ["ticks_5m", "ticks_15m", "ticks_1h"].forEach((col) => {
                const v = row[col] ?? 0;
                const cls = getComparisonClass(v, prev[col], true);
                tr.appendChild(makeTd(col, String(v), cls));
            });

            // Vdelta columns
            ["vdelta_5m", "vdelta_15m", "vdelta_1h", "vdelta_8h", "vdelta_1d"].forEach((col) => {
                const v = row[col] ?? 0;
                const numValue = Number(v);
                let cls = "";
                // Use strict comparison with epsilon for floating point precision
                if (!isNaN(numValue) && numValue > 0.0000001) cls = "value-up";
                else if (!isNaN(numValue) && numValue < -0.0000001) cls = "value-down";
                const formatted = formatVdelta(v);
                tr.appendChild(makeTd(col, formatted, cls));
            });

            // Volume columns - compare with previous values
            ["volume_5m", "volume_15m", "volume_1h", "volume_8h", "volume_1d"].forEach((col) => {
                const v = row[col] ?? 0;
                const formatted = formatVolume(v);
                const cls = getComparisonClass(v, prev[col], true);
                tr.appendChild(makeTd(col, formatted, cls));
            });

            // Funding
            const funding = row.funding_rate ?? 0;
            const fundNumValue = Number(funding);
            let fundClass = "";
            // Use strict comparison with epsilon for floating point precision
            if (!isNaN(fundNumValue) && fundNumValue > 0.0000001) fundClass = "value-up";
            else if (!isNaN(fundNumValue) && fundNumValue < -0.0000001) fundClass = "value-down";
            const fundingFormatted = !isNaN(fundNumValue) ? fundNumValue.toFixed(4) : String(funding);
            tr.appendChild(makeTd("funding_rate", fundingFormatted, fundClass));

            // Open Interest - compare with previous value
            const oiValue = row.open_interest != null ? Number(row.open_interest) : 0;
            const oiCls = getComparisonClass(oiValue, prev.open_interest, true);
            tr.appendChild(makeTd("open_interest", formatVolume(oiValue), oiCls));

            // Timestamp
            tr.appendChild(makeTd("ts", row.ts));

            screenerTableBody.appendChild(tr);
            
            // Store current values as previous for next update - ensure they are numbers
            // Only update if we have valid numeric values
            const storeValue = (val) => {
                const num = Number(val);
                return (!isNaN(num) && num !== null && num !== undefined) ? num : 0;
            };
            
            previousValues.set(symbol, {
                volatility_5m: storeValue(row.volatility_5m),
                volatility_15m: storeValue(row.volatility_15m),
                volatility_1h: storeValue(row.volatility_1h),
                ticks_5m: storeValue(row.ticks_5m),
                ticks_15m: storeValue(row.ticks_15m),
                ticks_1h: storeValue(row.ticks_1h),
                volume_5m: storeValue(row.volume_5m),
                volume_15m: storeValue(row.volume_15m),
                volume_1h: storeValue(row.volume_1h),
                volume_8h: storeValue(row.volume_8h),
                volume_1d: storeValue(row.volume_1d),
                open_interest: storeValue(row.open_interest),
            });
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

    // Initialize previous values from server-rendered table on first load
    function initializePreviousValues() {
        if (!screenerTableBody) return;
        const rows = screenerTableBody.querySelectorAll("tbody tr");
        rows.forEach((tr) => {
            const symbolCell = tr.querySelector('td[data-column="symbol"] a');
            if (!symbolCell) return;
            const symbol = symbolCell.textContent.trim();
            
            // Extract values from table cells - parse formatted values
            const getValue = (col) => {
                const cell = tr.querySelector(`td[data-column="${col}"]`);
                if (!cell) return 0;
                let text = cell.textContent.trim();
                
                // Remove % sign if present
                text = text.replace('%', '');
                
                // Parse K/M/B suffixes
                if (text.endsWith('K')) {
                    return parseFloat(text.replace('K', '')) * 1000;
                }
                if (text.endsWith('M')) {
                    return parseFloat(text.replace('M', '')) * 1000000;
                }
                if (text.endsWith('B')) {
                    return parseFloat(text.replace('B', '')) * 1000000000;
                }
                
                const parsed = parseFloat(text);
                return isNaN(parsed) ? 0 : parsed;
            };
            
            previousValues.set(symbol, {
                volatility_5m: getValue("volatility_5m"),
                volatility_15m: getValue("volatility_15m"),
                volatility_1h: getValue("volatility_1h"),
                ticks_5m: getValue("ticks_5m"),
                ticks_15m: getValue("ticks_15m"),
                ticks_1h: getValue("ticks_1h"),
                volume_5m: getValue("volume_5m"),
                volume_15m: getValue("volume_15m"),
                volume_1h: getValue("volume_1h"),
                volume_8h: getValue("volume_8h"),
                volume_1d: getValue("volume_1d"),
                open_interest: getValue("open_interest"),
            });
        });
    }

    // Initialize main screener auto-refresh if we are on the list page.
    if (screenerTableBody) {
        // Initialize previous values from server-rendered table
        initializePreviousValues();
        
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
        // Start auto-refresh - delay first refresh to ensure previousValues is initialized
        setTimeout(() => {
            refreshScreener();
            setInterval(refreshScreener, autoRefreshIntervalMs);
        }, 100);
        
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
                if (vol15El) {
                    const v = latest.volatility_15m ?? 0;
                    vol15El.textContent = formatVolatility(v);
                }
                if (vol5mEl) vol5mEl.textContent = formatVolume(latest.volume_5m);
                if (fundingEl) {
                    const f = latest.funding_rate ?? 0;
                    const fNumValue = Number(f);
                    fundingEl.textContent = !isNaN(fNumValue) ? fNumValue.toFixed(4) : String(f);
                    fundingEl.classList.remove("value-up", "value-down");
                    if (!isNaN(fNumValue) && fNumValue > 0.0000001) fundingEl.classList.add("value-up");
                    else if (!isNaN(fNumValue) && fNumValue < -0.0000001) fundingEl.classList.add("value-down");
                }
                if (oiEl) oiEl.textContent = formatVolume(latest.open_interest);
                if (updatedEl) updatedEl.textContent = latest.ts || "";
                if (oi15El) {
                    const v = latest.oi_change_15m ?? 0;
                    const numValue = Number(v);
                    oi15El.textContent = formatOIChange(v) + "%";
                    oi15El.classList.remove("value-up", "value-down");
                    if (!isNaN(numValue) && numValue > 0.0000001) oi15El.classList.add("value-up");
                    else if (!isNaN(numValue) && numValue < -0.0000001) oi15El.classList.add("value-down");
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
                const c15NumValue = Number(c15);
                change15Td.textContent = (!isNaN(c15NumValue) ? c15NumValue.toFixed(2) : String(c15)) + "%";
                if (!isNaN(c15NumValue) && c15NumValue > 0.0000001) change15Td.classList.add("value-up");
                else if (!isNaN(c15NumValue) && c15NumValue < -0.0000001) change15Td.classList.add("value-down");

                const vol15Td = document.createElement("td");
                vol15Td.textContent = formatVolume(s.volume_15m);
                // Volume comparison - compare with previous snapshot in the list
                if (snapshots.indexOf(s) > 0) {
                    const prevSnapshot = snapshots[snapshots.indexOf(s) - 1];
                    const volCls = getComparisonClass(s.volume_15m, prevSnapshot.volume_15m, true);
                    if (volCls) vol15Td.classList.add(volCls);
                }

                const oiTd = document.createElement("td");
                oiTd.textContent = formatVolume(s.open_interest);
                // OI comparison - compare with previous snapshot in the list
                if (snapshots.indexOf(s) > 0) {
                    const prevSnapshot = snapshots[snapshots.indexOf(s) - 1];
                    const oiCls = getComparisonClass(s.open_interest, prevSnapshot.open_interest, true);
                    if (oiCls) oiTd.classList.add(oiCls);
                }

                const oi15Td = document.createElement("td");
                const oi15 = s.oi_change_15m ?? 0;
                const oi15NumValue = Number(oi15);
                oi15Td.textContent = formatOIChange(oi15) + "%";
                if (!isNaN(oi15NumValue) && oi15NumValue > 0.0000001) oi15Td.classList.add("value-up");
                else if (!isNaN(oi15NumValue) && oi15NumValue < -0.0000001) oi15Td.classList.add("value-down");

                const fundingTd = document.createElement("td");
                const f = s.funding_rate ?? 0;
                const fNumValue = Number(f);
                fundingTd.textContent = !isNaN(fNumValue) ? fNumValue.toFixed(4) : String(f);
                if (!isNaN(fNumValue) && fNumValue > 0.0000001) fundingTd.classList.add("value-up");
                else if (!isNaN(fNumValue) && fNumValue < -0.0000001) fundingTd.classList.add("value-down");

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
