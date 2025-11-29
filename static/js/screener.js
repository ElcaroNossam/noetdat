document.addEventListener("DOMContentLoaded", () => {
    const screenerTableBody = document.getElementById("screener-table-body");
    const autoRefreshIntervalMs = 5000; // 5s for main screener (reduced frequency to avoid blocking user interactions)

    const availableColumns = window.SCREENER_AVAILABLE_COLUMNS || [];
    const storageKey = "screener_visible_columns";
    const languageStorageKey = "preferred_language";
    
    // Track if user is interacting with the page to pause auto-refresh
    let isUserInteracting = false;
    let interactionTimeout = null;
    
    // Track user interactions to pause auto-refresh
    document.addEventListener('mousedown', () => {
        isUserInteracting = true;
        clearTimeout(interactionTimeout);
        interactionTimeout = setTimeout(() => {
            isUserInteracting = false;
        }, 2000); // Reset after 2s of no interaction
    });
    
    document.addEventListener('keydown', () => {
        isUserInteracting = true;
        clearTimeout(interactionTimeout);
        interactionTimeout = setTimeout(() => {
            isUserInteracting = false;
        }, 2000);
    });
    
    // Store previous values for comparison (for volume, ticks, volatility, OI)
    let previousValues = new Map(); // key: symbol, value: object with previous values
    
    // Use global language functions from base.html
    function getLanguagePrefix() {
        if (window.getLanguagePrefix) {
            return window.getLanguagePrefix();
        }
        // Fallback if global function not available
        const currentPath = window.location.pathname;
        const langMatch = currentPath.match(/^\/(ru|en|es|he)\//);
        if (langMatch && langMatch[1]) {
            return langMatch[1];
        }
        // If no prefix in URL, it's default language (ru) - but we still need prefix for API
        // Check localStorage
        try {
            const savedLang = localStorage.getItem('preferred_language');
            if (savedLang && ['ru', 'en', 'es', 'he'].includes(savedLang)) {
                return savedLang;
            }
        } catch (e) {
            // ignore
        }
        // Default to Russian
        return 'ru';
    }

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
                    <h2>${window.__ ? window.__('Screener Settings') : 'Screener Settings'}</h2>
                    <button type="button" class="close-settings" id="close-settings">×</button>
                </div>
                <p class="chart-note">${window.__ ? window.__('Customize the table display by selecting the columns you want to see.') : 'Customize the table display by selecting the columns you want to see.'}</p>
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
                        <span>${window.__ ? window.__('Restore Default Column Order') : 'Restore Default Column Order'}</span>
                        <button type="button" class="btn-secondary" id="reset-settings">${window.__ ? window.__('Reset') : 'Reset'}</button>
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
        // Remove duplicate market_type params first
        const marketType = url.searchParams.get("market_type") || "spot";
        url.searchParams.delete("market_type");
        url.searchParams.set("market_type", marketType);
        // Preserve language from URL path (e.g., /ru/, /en/, etc.)
        const pathParts = url.pathname.split('/').filter(p => p);
        if (pathParts.length > 0 && ['ru', 'en', 'es', 'he'].includes(pathParts[0])) {
            // Language is in path, it will be preserved automatically
        }
        // Also preserve language from query params if present
        const langFromPath = pathParts[0];
        if (langFromPath && ['ru', 'en', 'es', 'he'].includes(langFromPath)) {
            // Language is in path, no need to add to query
        }
        return url.search || "?";
    }

    function formatPrice(v) {
        if (v === null || v === undefined) return "";
        const value = Number(v);
        if (isNaN(value)) return String(v);
        const absV = Math.abs(value);
        // For large prices (>= 1000), use K/M/B suffixes
        if (absV >= 1_000_000_000) return (value / 1_000_000_000).toFixed(2) + "B";
        if (absV >= 1_000_000) return (value / 1_000_000).toFixed(2) + "M";
        if (absV >= 1_000) return (value / 1_000).toFixed(2) + "K";
        // For smaller prices, use adaptive formatting
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
            // Check if value is whole number (same logic as Django: abs_v == int(abs_v))
            // For whole numbers, return as integer (preserve sign like int(v) in Python)
            const intAbs = Math.floor(absV);
            if (Math.abs(absV - intAbs) < 0.0001) {
                // Value is whole number, return as integer with correct sign
                // int(v) in Python preserves sign: int(5.0) = 5, int(-5.0) = -5
                return String(value >= 0 ? intAbs : -intAbs);
            }
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
        // Skip refresh if user is interacting
        if (isUserInteracting) {
            return;
        }
        try {
            const query = buildQueryFromCurrentLocation();
            // Build API path based on current URL structure
            const currentPath = window.location.pathname;
            const pathParts = currentPath.split('/').filter(p => p);
            const hasLangPrefix = pathParts.length > 0 && ['ru', 'en', 'es', 'he'].includes(pathParts[0]);
            
            // Build API path: if current URL has language prefix, use it; otherwise use /api/ directly
            const apiPath = hasLangPrefix 
                ? `/${pathParts[0]}/api/screener/`
                : `/api/screener/`;
            
            const url = apiPath + query.replace(/^\?/, "?");
            
            const resp = await fetch(url);
            if (!resp.ok) {
                // Silently fail - will retry on next interval
                return;
            }

            const data = await resp.json();
            renderScreenerTable(data);
            // Always reapply column visibility immediately after rendering
            applyColumnVisibility();
        } catch (e) {
            // Silently fail - will retry on next interval
        }
    }

    function getComparisonClass(currentValue, previousValue, isPositiveOnly = false) {
        const current = Number(currentValue);
        const previous = previousValue !== null && previousValue !== undefined && previousValue !== "" ? Number(previousValue) : null;
        
        // Check for NaN
        if (isNaN(current)) return "";
        
        // If we have previous value, always compare (for both positive-only and negative values)
        if (previous !== null && !isNaN(previous)) {
            const diff = current - previous;
            if (diff > 0.0001) return "value-up";
            if (diff < -0.0001) return "value-down";
            // If values are equal or very close, no color (white)
            return "";
        }
        
        // No previous value - no color (white) for all values
        // Changed: Vdelta now works like Volume - only shows color when comparing with previous value
        return "";
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
            td.textContent = "No data to display.";
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
                // Set className - empty string means no class, which is fine
                if (className && className.trim() !== "") {
                    td.className = className;
                }
                td.textContent = text;
                return td;
            };

            const symbolTd = document.createElement("td");
            symbolTd.dataset.column = "symbol";
            const link = document.createElement("a");
            const marketType = new URLSearchParams(window.location.search).get("market_type") || "spot";
            link.href = `/trading/${row.symbol}/?market_type=${marketType}`;
            link.textContent = row.symbol;
            symbolTd.appendChild(link);

            tr.appendChild(symbolTd);
            
            // Price - use formatted value from backend if available, otherwise format on client
            const priceValue = Number(row.price ?? 0);
            const priceFormatted = (row.price_formatted !== undefined && row.price_formatted !== null && row.price_formatted !== "") 
                ? row.price_formatted 
                : formatPrice(row.price);
            let priceCls = (row.price_color !== undefined && row.price_color !== null && row.price_color !== "") 
                ? row.price_color 
                : "";
            if (!priceCls) {
                const prevPrice = prev.price !== undefined && prev.price !== null && prev.price !== "" ? Number(prev.price) : undefined;
                priceCls = getComparisonClass(priceValue, prevPrice, true);
            }
            tr.appendChild(makeTd("price", priceFormatted, priceCls));

            // Change columns - compare with previous values (same logic as Volume)
            ["change_5m", "change_15m", "change_1h", "change_8h", "change_1d"].forEach((col) => {
                const v = row[col] ?? 0;
                const numValue = Number(v);
                const formatted = !isNaN(numValue) ? numValue.toFixed(2) : String(v);
                const prevValue = prev[col] !== undefined && prev[col] !== null && prev[col] !== "" ? Number(prev[col]) : undefined;
                const cls = getComparisonClass(numValue, prevValue, false);
                tr.appendChild(makeTd(col, formatted + "%", cls));
            });

            // OI Change columns - compare with previous values (same logic as Volume)
            ["oi_change_5m", "oi_change_15m", "oi_change_1h", "oi_change_8h", "oi_change_1d"].forEach((col) => {
                const v = row[col] ?? 0;
                const numValue = Number(v);
                const formatted = formatOIChange(v);
                const prevValue = prev[col] !== undefined && prev[col] !== null && prev[col] !== "" ? Number(prev[col]) : undefined;
                const cls = getComparisonClass(numValue, prevValue, false);
                tr.appendChild(makeTd(col, formatted + "%", cls));
            });

            // Volatility columns - compare with previous values
            ["volatility_5m", "volatility_15m", "volatility_1h"].forEach((col) => {
                const v = row[col] ?? 0;
                const numValue = Number(v);
                const formatted = formatVolatility(v);
                const prevValue = prev[col] !== undefined && prev[col] !== null && prev[col] !== "" ? Number(prev[col]) : undefined;
                const cls = getComparisonClass(numValue, prevValue, true);
                tr.appendChild(makeTd(col, formatted, cls));
            });

            // Ticks columns - use formatted values from backend if available, otherwise format on client
            ["ticks_5m", "ticks_15m", "ticks_1h"].forEach((col) => {
                const v = row[col] ?? 0;
                const numValue = Number(v);
                // Use formatted value from backend if available, otherwise format on client
                let formatted = (row[col + "_formatted"] !== undefined && row[col + "_formatted"] !== null && row[col + "_formatted"] !== "") 
                    ? row[col + "_formatted"] 
                    : (() => {
                        if (isNaN(numValue)) return String(v);
                        const absV = Math.abs(numValue);
                        if (absV >= 1_000_000_000) return (numValue / 1_000_000_000).toFixed(2) + "B";
                        if (absV >= 1_000_000) return (numValue / 1_000_000).toFixed(2) + "M";
                        if (absV >= 1_000) return (numValue / 1_000).toFixed(2) + "K";
                        return String(Math.round(numValue));
                    })();
                // Use color from backend if available, otherwise calculate based on previousValues
                let cls = (row[col + "_color"] !== undefined && row[col + "_color"] !== null && row[col + "_color"] !== "") 
                    ? row[col + "_color"] 
                    : "";
                if (!cls) {
                    const prevValue = prev[col] !== undefined && prev[col] !== null && prev[col] !== "" ? Number(prev[col]) : undefined;
                    cls = getComparisonClass(numValue, prevValue, true);
                }
                tr.appendChild(makeTd(col, formatted, cls));
            });

            // Vdelta columns - use formatted values and colors from backend (same logic as OI)
            ["vdelta_5m", "vdelta_15m", "vdelta_1h", "vdelta_8h", "vdelta_1d"].forEach((col) => {
                // Use formatted value from backend if available, otherwise format on client
                const formatted = (row[col + "_formatted"] !== undefined && row[col + "_formatted"] !== null && row[col + "_formatted"] !== "") 
                    ? row[col + "_formatted"] 
                    : formatVdelta(row[col] ?? 0);
                // Use color from backend if available, otherwise calculate based on previousValues
                let cls = (row[col + "_color"] !== undefined && row[col + "_color"] !== null && row[col + "_color"] !== "") 
                    ? row[col + "_color"] 
                    : "";
                if (!cls) {
                    // If no color from backend, calculate based on previous value from previousValues
                    const numValue = Number(row[col] ?? 0);
                    const prevValue = prev[col] !== undefined && prev[col] !== null && prev[col] !== "" ? Number(prev[col]) : undefined;
                    cls = getComparisonClass(numValue, prevValue, false);
                }
                tr.appendChild(makeTd(col, formatted, cls));
            });

            // Volume columns - use formatted values and colors from backend (same logic as OI)
            ["volume_5m", "volume_15m", "volume_1h", "volume_8h", "volume_1d"].forEach((col) => {
                // Use formatted value from backend if available, otherwise format on client
                const formatted = (row[col + "_formatted"] !== undefined && row[col + "_formatted"] !== null && row[col + "_formatted"] !== "") 
                    ? row[col + "_formatted"] 
                    : formatVolume(row[col] ?? 0);
                // Use color from backend if available, otherwise calculate based on previousValues
                let cls = (row[col + "_color"] !== undefined && row[col + "_color"] !== null && row[col + "_color"] !== "") 
                    ? row[col + "_color"] 
                    : "";
                if (!cls) {
                    // If no color from backend, calculate based on previous value from previousValues
                    const numValue = Number(row[col] ?? 0);
                    const prevValue = prev[col] !== undefined && prev[col] !== null && prev[col] !== "" ? Number(prev[col]) : undefined;
                    cls = getComparisonClass(numValue, prevValue, true);
                }
                tr.appendChild(makeTd(col, formatted, cls));
            });

            // Funding Rate - compare with previous value (same logic as Volume)
            const funding = row.funding_rate ?? 0;
            const fundNumValue = Number(funding);
            const fundingFormatted = !isNaN(fundNumValue) ? fundNumValue.toFixed(4) : String(funding);
            const prevFunding = prev.funding_rate !== undefined && prev.funding_rate !== null && prev.funding_rate !== "" ? Number(prev.funding_rate) : undefined;
            const fundClass = getComparisonClass(fundNumValue, prevFunding, false);
            tr.appendChild(makeTd("funding_rate", fundingFormatted, fundClass));

            // Open Interest - use formatted value and color from backend (reference implementation)
            const oiFormatted = (row.open_interest_formatted !== undefined && row.open_interest_formatted !== null && row.open_interest_formatted !== "") 
                ? row.open_interest_formatted 
                : formatVolume(row.open_interest ?? 0);
            let oiCls = (row.open_interest_color !== undefined && row.open_interest_color !== null && row.open_interest_color !== "") 
                ? row.open_interest_color 
                : "";
            if (!oiCls) {
                // If no color from backend, calculate based on previous value from previousValues
                const oiValue = row.open_interest != null ? Number(row.open_interest) : 0;
                const prevOI = prev.open_interest !== undefined && prev.open_interest !== null && prev.open_interest !== "" ? Number(prev.open_interest) : undefined;
                oiCls = getComparisonClass(oiValue, prevOI, true);
            }
            tr.appendChild(makeTd("open_interest", oiFormatted, oiCls));

            // Timestamp
            tr.appendChild(makeTd("ts", row.ts));

            screenerTableBody.appendChild(tr);
            
            // Store current values as previous for next update - ensure they are numbers
            // Only update if we have valid numeric values
            const storeValue = (val) => {
                const num = Number(val);
                return (!isNaN(num) && num !== null && num !== undefined) ? num : 0;
            };
            
            // Store ALL values for proper comparison
            previousValues.set(symbol, {
                // Price
                price: storeValue(row.price),
                // Change values
                change_5m: storeValue(row.change_5m),
                change_15m: storeValue(row.change_15m),
                change_1h: storeValue(row.change_1h),
                change_8h: storeValue(row.change_8h),
                change_1d: storeValue(row.change_1d),
                // OI Change values
                oi_change_5m: storeValue(row.oi_change_5m),
                oi_change_15m: storeValue(row.oi_change_15m),
                oi_change_1h: storeValue(row.oi_change_1h),
                oi_change_8h: storeValue(row.oi_change_8h),
                oi_change_1d: storeValue(row.oi_change_1d),
                // Volatility values
                volatility_5m: storeValue(row.volatility_5m),
                volatility_15m: storeValue(row.volatility_15m),
                volatility_1h: storeValue(row.volatility_1h),
                // Ticks values
                ticks_5m: storeValue(row.ticks_5m),
                ticks_15m: storeValue(row.ticks_15m),
                ticks_1h: storeValue(row.ticks_1h),
                // Vdelta values
                vdelta_5m: storeValue(row.vdelta_5m),
                vdelta_15m: storeValue(row.vdelta_15m),
                vdelta_1h: storeValue(row.vdelta_1h),
                vdelta_8h: storeValue(row.vdelta_8h),
                vdelta_1d: storeValue(row.vdelta_1d),
                // Volume values
                volume_5m: storeValue(row.volume_5m),
                volume_15m: storeValue(row.volume_15m),
                volume_1h: storeValue(row.volume_1h),
                volume_8h: storeValue(row.volume_8h),
                volume_1d: storeValue(row.volume_1d),
                // Funding rate
                funding_rate: storeValue(row.funding_rate),
                // Open Interest
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
        const rows = Array.from(screenerTableBody.querySelectorAll("tbody tr"));
        
        // Helper to parse formatted values
        const parseFormattedValue = (text) => {
            if (!text) return 0;
            text = text.trim().replace('%', '');
            
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
        
        rows.forEach((tr, index) => {
            const symbolCell = tr.querySelector('td[data-column="symbol"] a');
            if (!symbolCell) return;
            const symbol = symbolCell.textContent.trim();
            
            // Get previous row for comparison
            const prevRow = index > 0 ? rows[index - 1] : null;
            
            // Apply colors to all cells based on comparison with previous row (same logic as Volume)
            const applyColorToCell = (col, cell, isPositiveOnly = true) => {
                if (!cell) return;
                const currentText = cell.textContent.trim();
                const currentValue = parseFormattedValue(currentText);
                
                if (prevRow) {
                    const prevCell = prevRow.querySelector(`td[data-column="${col}"]`);
                    if (prevCell) {
                        const prevText = prevCell.textContent.trim();
                        const prevValue = parseFormattedValue(prevText);
                        
                        // Compare with previous value (same logic for all columns)
                        const diff = currentValue - prevValue;
                        if (diff > 0.0001) {
                            cell.classList.add("value-up");
                        } else if (diff < -0.0001) {
                            cell.classList.add("value-down");
                        }
                        // If values are equal or very close, no color (white)
                    }
                }
                // If no previous row, no color (white) - same for all columns
            };
            
            // Apply colors to all cells based on comparison with previous row (same logic as Volume)
            // Price
            const priceCell = tr.querySelector(`td[data-column="price"]`);
            applyColorToCell("price", priceCell, true);
            
            // Change columns
            ["change_5m", "change_15m", "change_1h", "change_8h", "change_1d"].forEach((col) => {
                const cell = tr.querySelector(`td[data-column="${col}"]`);
                applyColorToCell(col, cell, false);
            });
            
            // OI Change columns
            ["oi_change_5m", "oi_change_15m", "oi_change_1h", "oi_change_8h", "oi_change_1d"].forEach((col) => {
                const cell = tr.querySelector(`td[data-column="${col}"]`);
                applyColorToCell(col, cell, false);
            });
            
            // Volatility columns
            ["volatility_5m", "volatility_15m", "volatility_1h"].forEach((col) => {
                const cell = tr.querySelector(`td[data-column="${col}"]`);
                applyColorToCell(col, cell, true);
            });
            
            // Ticks columns
            ["ticks_5m", "ticks_15m", "ticks_1h"].forEach((col) => {
                const cell = tr.querySelector(`td[data-column="${col}"]`);
                applyColorToCell(col, cell, true);
            });
            
            // Volume columns
            ["volume_5m", "volume_15m", "volume_1h", "volume_8h", "volume_1d"].forEach((col) => {
                const cell = tr.querySelector(`td[data-column="${col}"]`);
                applyColorToCell(col, cell, true);
            });
            
            // Vdelta columns
            ["vdelta_5m", "vdelta_15m", "vdelta_1h", "vdelta_8h", "vdelta_1d"].forEach((col) => {
                const cell = tr.querySelector(`td[data-column="${col}"]`);
                applyColorToCell(col, cell, false);
            });
            
            // Funding Rate
            const fundingCell = tr.querySelector(`td[data-column="funding_rate"]`);
            applyColorToCell("funding_rate", fundingCell, false);
            
            // Open Interest
            const oiCell = tr.querySelector(`td[data-column="open_interest"]`);
            applyColorToCell("open_interest", oiCell, true);
            
            // Store values for next update
            const getValue = (col) => {
                const cell = tr.querySelector(`td[data-column="${col}"]`);
                if (!cell) return 0;
                return parseFormattedValue(cell.textContent);
            };
            
            const getVdeltaValue = (col) => {
                const cell = tr.querySelector(`td[data-column="${col}"]`);
                if (!cell) return 0;
                let text = cell.textContent.trim();
                
                if (text.endsWith('K')) {
                    return parseFloat(text.replace('K', '')) * 1000;
                }
                if (text.endsWith('M')) {
                    return parseFloat(text.replace('M', '')) * 1000000;
                }
                
                const parsed = parseFloat(text);
                return isNaN(parsed) ? 0 : parsed;
            };
            
            previousValues.set(symbol, {
                // Price
                price: getValue("price"),
                // Change values
                change_5m: getValue("change_5m"),
                change_15m: getValue("change_15m"),
                change_1h: getValue("change_1h"),
                change_8h: getValue("change_8h"),
                change_1d: getValue("change_1d"),
                // OI Change values
                oi_change_5m: getValue("oi_change_5m"),
                oi_change_15m: getValue("oi_change_15m"),
                oi_change_1h: getValue("oi_change_1h"),
                oi_change_8h: getValue("oi_change_8h"),
                oi_change_1d: getValue("oi_change_1d"),
                // Volatility values
                volatility_5m: getValue("volatility_5m"),
                volatility_15m: getValue("volatility_15m"),
                volatility_1h: getValue("volatility_1h"),
                // Ticks values
                ticks_5m: getValue("ticks_5m"),
                ticks_15m: getValue("ticks_15m"),
                ticks_1h: getValue("ticks_1h"),
                // Vdelta values
                vdelta_5m: getVdeltaValue("vdelta_5m"),
                vdelta_15m: getVdeltaValue("vdelta_15m"),
                vdelta_1h: getVdeltaValue("vdelta_1h"),
                vdelta_8h: getVdeltaValue("vdelta_8h"),
                vdelta_1d: getVdeltaValue("vdelta_1d"),
                // Volume values
                volume_5m: getValue("volume_5m"),
                volume_15m: getValue("volume_15m"),
                volume_1h: getValue("volume_1h"),
                volume_8h: getValue("volume_8h"),
                volume_1d: getValue("volume_1d"),
                // Funding rate
                funding_rate: getValue("funding_rate"),
                // Open Interest
                open_interest: getValue("open_interest"),
            });
        });
    }

    // Initialize main screener auto-refresh if we are on the list page.
    if (screenerTableBody) {
        // Initialize previous values from server-rendered table FIRST
        // This must happen before any updates to ensure colors work on first refresh
        initializePreviousValues();
        
        // Apply column visibility IMMEDIATELY on page load (for server-rendered HTML)
        applyColumnVisibility();
        
        // Build settings panel
        buildSettingsPanel();
        attachToggleButton();
        setupTableSorting();
        // Sync scrollbars
        syncScrollbars();
        
        // Start auto-refresh immediately - previousValues is already initialized
        // Use requestAnimationFrame for optimal timing (runs before next paint)
        requestAnimationFrame(() => {
            // Re-initialize to be sure (in case DOM wasn't ready)
            initializePreviousValues();
            // Start refresh immediately
            refreshScreener();
            // Then continue with interval
            setInterval(refreshScreener, autoRefreshIntervalMs);
        });
        
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
                // Preserve language prefix from current URL (e.g., /ru/, /en/, etc.)
                const currentPath = window.location.pathname;
                const langPrefix = currentPath.match(/^\/(ru|en|es|he)\//)?.[1];
                const apiPath = langPrefix ? `/${langPrefix}/api/symbol/` : "/api/symbol/";
                const resp = await fetch(`${apiPath}${encodeURIComponent(symbol)}/`);
                if (!resp.ok) return;
                const data = await resp.json();
                renderSymbolDetail(data);
            } catch (e) {
                // Silently fail - will retry on next interval
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
                td.textContent = "No data.";
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
