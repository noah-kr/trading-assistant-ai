/* ============================================================
   Trading Assistant - Main JavaScript
   Handles: Tabs, Chat, Portfolio, Market data, Charts
   ============================================================ */

// ---- Tab navigation ----
document.querySelectorAll(".nav-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
        document.querySelectorAll(".nav-tab").forEach((t) => t.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
        tab.classList.add("active");
        const target = tab.dataset.tab;
        document.getElementById("tab-" + target).classList.add("active");

        // Auto-load data when switching tabs
        if (target === "portfolio") loadPortfolio();
        if (target === "market") loadMarketLists();
    });
});

// ---- Logout ----
document.getElementById("logout-btn").addEventListener("click", async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
});

// ---- Theme toggle ----
const themeToggleBtn = document.getElementById("theme-toggle");

function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
    // ☀ for dark mode (click to go light), ☽ for light mode (click to go dark)
    if (themeToggleBtn) themeToggleBtn.innerHTML = theme === "dark" ? "&#9790;" : "&#9728;";
}

// Initialise from storage
applyTheme(localStorage.getItem("theme") || "dark");

if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme") || "dark";
        applyTheme(current === "dark" ? "light" : "dark");
    });
}

// Helper: get current chart colors from CSS variables
function chartColors() {
    const s = getComputedStyle(document.documentElement);
    return {
        grid: s.getPropertyValue("--chart-grid").trim() || "#2d3044",
        text: s.getPropertyValue("--chart-text").trim() || "#9ca3af",
        legend: s.getPropertyValue("--chart-legend").trim() || "#e8e8e8",
    };
}

// ============================================================
//  CHAT
// ============================================================
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const forceModeToggle = document.getElementById("force-mode-toggle");

// Load history on page load
(async () => {
    try {
        const res = await fetch("/api/chat/history");
        if (res.ok) {
            const history = await res.json();
            history.forEach((m) => appendMessage(m.role, m.content));
        }
    } catch (e) { /* ignore */ }
})();

chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (!msg) return;

    appendMessage("user", msg);
    chatInput.value = "";
    sendBtn.disabled = true;

    // Show typing indicator
    const typingEl = appendMessage("assistant", "Thinking...");
    typingEl.classList.add("typing-indicator");

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: msg,
                force_mode: forceModeToggle.checked,
            }),
        });
        const data = await res.json();
        typingEl.remove();

        if (!res.ok) {
            appendMessage("assistant", "Error: " + (data.error || "Something went wrong."));
        } else {
            const answer = data.response || "";
            // Check if the response contains a chart command
            const chartCmd = parseChartCommand(answer);
            if (chartCmd) {
                appendMessage("assistant", answer);
                showStockChart(chartCmd.symbol, chartCmd.period, chartCmd.timeframe);
            } else {
                appendMessage("assistant", answer);
            }
        }
    } catch (err) {
        typingEl.remove();
        appendMessage("assistant", "Network error. Please try again.");
    }

    sendBtn.disabled = false;
    chatInput.focus();
});

function appendMessage(role, content) {
    const div = document.createElement("div");
    div.className = "message " + role;
    const inner = document.createElement("div");
    inner.className = "message-content";
    inner.textContent = content;
    div.appendChild(inner);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
}

function parseChartCommand(text) {
    // The draw_chart_agent returns JSON like {"type": "SHOW_STOCK_CHART", "symbol": "AAPL", ...}
    try {
        const match = text.match(/\{[^}]*"type"\s*:\s*"SHOW_STOCK_CHART"[^}]*\}/);
        if (match) {
            const obj = JSON.parse(match[0]);
            return {
                symbol: obj.symbol || "AAPL",
                period: obj.period || "1y",
                timeframe: obj.timeframe || "daily",
            };
        }
    } catch (e) { /* not a chart command */ }
    return null;
}

// ============================================================
//  CHART MODAL (from chat)
// ============================================================
let chartInstance = null;

document.getElementById("chart-modal-close").addEventListener("click", () => {
    document.getElementById("chart-modal").style.display = "none";
    if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
});

async function showStockChart(symbol, period, timeframe) {
    const modal = document.getElementById("chart-modal");
    const titleEl = document.getElementById("chart-title");
    titleEl.textContent = symbol.toUpperCase() + " - " + timeframe + " (" + period + ")";
    modal.style.display = "flex";

    try {
        const res = await fetch(`/api/market/stock/${symbol}?timeframe=${timeframe}&period=${period}`);
        const data = await res.json();

        if (data.error) {
            titleEl.textContent = "Error: " + data.error;
            return;
        }

        const points = (data.data || []).reverse(); // oldest first for chart
        const labels = points.map((p) => p.date);
        const prices = points.map((p) => p.close);

        const ctx = document.getElementById("stock-chart").getContext("2d");
        if (chartInstance) chartInstance.destroy();

        chartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels,
                datasets: [{
                    label: symbol.toUpperCase() + " Close",
                    data: prices,
                    borderColor: "#3b82f6",
                    backgroundColor: "rgba(59,130,246,0.1)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    borderWidth: 2,
                }],
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: chartColors().legend } } },
                scales: {
                    x: { ticks: { color: chartColors().text, maxTicksLimit: 12 }, grid: { color: chartColors().grid } },
                    y: { ticks: { color: chartColors().text }, grid: { color: chartColors().grid } },
                },
            },
        });
    } catch (err) {
        titleEl.textContent = "Failed to load chart data.";
    }
}

// ============================================================
//  PORTFOLIO
// ============================================================
let portfolioChart = null;

async function loadPortfolio() {
    // Positions
    try {
        const res = await fetch("/api/portfolio");
        const data = await res.json();

        if (data.error) {
            document.getElementById("portfolio-summary").innerHTML =
                `<p style="color:var(--red);">${data.error}</p>`;
            return;
        }

        const positions = Array.isArray(data) ? data : (data.positions || []);

        // Summary
        let totalValue = 0;
        let totalPL = 0;
        positions.forEach((p) => {
            totalValue += parseFloat(p.market_value || 0);
            totalPL += parseFloat(p.unrealized_pl || 0);
        });

        const cash = parseFloat(data.cash || 0);
        const equity = parseFloat(data.equity || 0);
        const buyingPower = parseFloat(data.buying_power || 0);

        const summaryEl = document.getElementById("portfolio-summary");
        summaryEl.innerHTML = `
            <div class="summary-card">
                <div class="label">Cash</div>
                <div class="value">$${cash.toFixed(2)}</div>
            </div>
            <div class="summary-card">
                <div class="label">Positions</div>
                <div class="value">${positions.length}</div>
            </div>
            <div class="summary-card">
                <div class="label">Market Value</div>
                <div class="value">$${totalValue.toFixed(2)}</div>
            </div>
            <div class="summary-card">
                <div class="label">Unrealized P&L</div>
                <div class="value ${totalPL >= 0 ? 'positive' : 'negative'}">
                    ${totalPL >= 0 ? '+' : ''}$${totalPL.toFixed(2)}
                </div>
            </div>
            <div class="summary-card">
                <div class="label">Equity</div>
                <div class="value">$${equity.toFixed(2)}</div>
            </div>
            <div class="summary-card">
                <div class="label">Buying Power</div>
                <div class="value">$${buyingPower.toFixed(2)}</div>
            </div>
        `;

        // Table
        const tbody = document.querySelector("#portfolio-table tbody");
        tbody.innerHTML = "";
        positions.forEach((p) => {
            const pl = parseFloat(p.unrealized_pl || 0);
            const row = document.createElement("tr");
            row.innerHTML = `
                <td style="font-weight:600;color:var(--accent);">${p.symbol}</td>
                <td>${p.qty}</td>
                <td>$${parseFloat(p.market_value || 0).toFixed(2)}</td>
                <td>$${parseFloat(p.avg_entry_price || 0).toFixed(2)}</td>
                <td>$${parseFloat(p.current_price || 0).toFixed(2)}</td>
                <td class="${pl >= 0 ? 'positive' : 'negative'}">
                    ${pl >= 0 ? '+' : ''}$${pl.toFixed(2)}
                </td>
            `;
            tbody.appendChild(row);
        });

        // Pie chart
        if (positions.length > 0) {
            const labels = positions.map((p) => p.symbol);
            const values = positions.map((p) => parseFloat(p.market_value || 0));
            const colors = generateColors(positions.length);

            const ctx = document.getElementById("portfolio-chart").getContext("2d");
            if (portfolioChart) portfolioChart.destroy();

            portfolioChart = new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels,
                    datasets: [{ data: values, backgroundColor: colors, borderWidth: 0 }],
                },
                options: {
                    responsive: true,
                    plugins: { legend: { position: "right", labels: { color: chartColors().legend, padding: 12 } } },
                },
            });
        }
    } catch (err) {
        document.getElementById("portfolio-summary").innerHTML =
            `<p style="color:var(--red);">Failed to load portfolio.</p>`;
    }

    // Pending orders
    try {
        const res = await fetch("/api/trade/orders");
        const orders = await res.json();
        const tbody = document.querySelector("#orders-table tbody");
        tbody.innerHTML = "";

        const orderList = Array.isArray(orders) ? orders : (orders.orders || []);
        if (orderList.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="color:var(--text-muted);">No pending orders</td></tr>';
        }

        orderList.forEach((o) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td style="font-weight:600;">${o.symbol}</td>
                <td>${o.side}</td>
                <td>${o.qty || o.notional || "-"}</td>
                <td>${o.type || "market"}</td>
                <td>${o.status}</td>
                <td><button class="btn btn-danger btn-small" onclick="cancelOrder('${o.id}')">Cancel</button></td>
            `;
            tbody.appendChild(row);
        });
    } catch (err) { /* ignore */ }
}

async function cancelOrder(orderId) {
    try {
        const res = await fetch(`/api/trade/orders/${orderId}`, { method: "DELETE" });
        const data = await res.json();
        if (data.error) alert(data.error);
        else loadPortfolio();
    } catch (err) {
        alert("Failed to cancel order.");
    }
}

// Refresh button
document.getElementById("refresh-portfolio").addEventListener("click", loadPortfolio);

// Deposit form
document.getElementById("deposit-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const amount = parseFloat(document.getElementById("deposit-amount").value);
    const msgEl = document.getElementById("deposit-msg");

    try {
        const res = await fetch("/api/funding/deposit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ amount }),
        });
        const data = await res.json();
        msgEl.style.display = "block";

        if (data.error) {
            msgEl.className = "info-msg error";
            msgEl.textContent = data.error;
        } else {
            msgEl.className = "info-msg success";
            msgEl.textContent = `Deposit of $${amount.toFixed(2)} submitted (${data.status}). It might take up to an hour until the funds are visible in your account.`;
            document.getElementById("deposit-amount").value = "";
            // Refresh portfolio after a short delay (sandbox settles quickly)
            setTimeout(loadPortfolio, 2000);
        }
    } catch (err) {
        msgEl.style.display = "block";
        msgEl.className = "info-msg error";
        msgEl.textContent = "Network error.";
    }
});

// ============================================================
//  MARKET DATA
// ============================================================
let marketListsLoaded = false;

function loadMarketLists() {
    if (marketListsLoaded) return;
    marketListsLoaded = true;

    // ETFs
    fetch("/api/market/etfs")
        .then((r) => r.json())
        .then((etfs) => {
            const el = document.getElementById("etf-list");
            el.innerHTML = "";
            etfs.forEach((e) => {
                el.innerHTML += `
                    <div class="list-item">
                        <span class="symbol">${e.symbol}</span>
                        <span class="name">${e.name}</span>
                        <span class="price" style="color:var(--text-muted);">${e.category}</span>
                    </div>`;
            });
        })
        .catch(() => {
            document.getElementById("etf-list").innerHTML = "<p>Failed to load ETFs.</p>";
        });

    // Cryptos
    fetch("/api/market/cryptos")
        .then((r) => r.json())
        .then((cryptos) => {
            const el = document.getElementById("crypto-list");
            el.innerHTML = "";
            cryptos.forEach((c) => {
                el.innerHTML += `
                    <div class="list-item">
                        <span class="symbol">${c.base}</span>
                        <span class="name">${c.name}</span>
                        <span class="price">${c.symbol}</span>
                    </div>`;
            });
        })
        .catch(() => {
            document.getElementById("crypto-list").innerHTML = "<p>Failed to load cryptos.</p>";
        });
}

// NASDAQ 100 - loaded on demand
document.getElementById("load-nasdaq100").addEventListener("click", async () => {
    const el = document.getElementById("nasdaq100-list");
    el.innerHTML = "<p>Loading NASDAQ 100...</p>";

    try {
        const res = await fetch("/api/market/nasdaq100");
        const stocks = await res.json();

        if (!Array.isArray(stocks)) {
            el.innerHTML = `<p style="color:var(--red);">${stocks.error || "Failed to load."}</p>`;
            return;
        }

        el.innerHTML = "";
        stocks.forEach((s) => {
            const change = s.percent_change;
            const changeClass = change >= 0 ? "positive" : "negative";
            el.innerHTML += `
                <div class="list-item">
                    <span class="symbol">${s.symbol}</span>
                    <span class="name">${s.name || ""}</span>
                    <span class="price">$${(s.last_sale || 0).toFixed(2)}
                        <span class="${changeClass}" style="font-size:0.8rem;">
                            ${change >= 0 ? "+" : ""}${(change || 0).toFixed(2)}%
                        </span>
                    </span>
                </div>`;
        });
    } catch (err) {
        el.innerHTML = "<p style='color:var(--red);'>Failed to load NASDAQ 100.</p>";
    }
});

// Stock lookup chart
let marketChartInstance = null;

document.getElementById("stock-lookup-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const symbol = document.getElementById("stock-symbol-input").value.trim().toUpperCase();
    const timeframe = document.getElementById("stock-timeframe").value;
    const period = document.getElementById("stock-period").value;

    if (!symbol) return;

    try {
        const res = await fetch(`/api/market/stock/${symbol}?timeframe=${timeframe}&period=${period}`);
        const data = await res.json();

        if (data.error) {
            alert("Error: " + data.error);
            return;
        }

        const points = (data.data || []).reverse();
        const labels = points.map((p) => p.date);
        const closes = points.map((p) => p.close);
        const highs = points.map((p) => p.high);
        const lows = points.map((p) => p.low);

        const ctx = document.getElementById("market-stock-chart").getContext("2d");
        if (marketChartInstance) marketChartInstance.destroy();

        marketChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels,
                datasets: [
                    {
                        label: symbol + " Close",
                        data: closes,
                        borderColor: "#3b82f6",
                        backgroundColor: "rgba(59,130,246,0.08)",
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                        borderWidth: 2,
                    },
                    {
                        label: "High",
                        data: highs,
                        borderColor: "rgba(16,185,129,0.4)",
                        borderWidth: 1,
                        pointRadius: 0,
                        borderDash: [4, 4],
                        fill: false,
                    },
                    {
                        label: "Low",
                        data: lows,
                        borderColor: "rgba(239,68,68,0.4)",
                        borderWidth: 1,
                        pointRadius: 0,
                        borderDash: [4, 4],
                        fill: false,
                    },
                ],
            },
            options: {
                responsive: true,
                interaction: { mode: "index", intersect: false },
                plugins: { legend: { labels: { color: chartColors().legend } } },
                scales: {
                    x: { ticks: { color: chartColors().text, maxTicksLimit: 15 }, grid: { color: chartColors().grid } },
                    y: { ticks: { color: chartColors().text }, grid: { color: chartColors().grid } },
                },
            },
        });
    } catch (err) {
        alert("Failed to load stock data.");
    }
});

// ============================================================
//  HELPERS
// ============================================================
function generateColors(n) {
    const base = [
        "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
        "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1",
        "#14b8a6", "#e11d48", "#a855f7", "#0ea5e9", "#65a30d",
    ];
    const colors = [];
    for (let i = 0; i < n; i++) colors.push(base[i % base.length]);
    return colors;
}
