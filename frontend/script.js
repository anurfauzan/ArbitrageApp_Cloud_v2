// ArbitrageApp_Cloud/frontend/script.js
document.addEventListener('DOMContentLoaded', () => {
    const opportunitiesTableBody = document.getElementById('opportunitiesTableBody');
    const noOpportunitiesMessage = document.getElementById('noOpportunitiesMessage');
    const connectionStatus = document.getElementById('connectionStatus');

    const websocketUrl = 'wss://arbitrageapp-cloud-v2.onrender.com';

    let ws;
    let reconnectInterval = 5000;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 10;

    function connectWebSocket() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            return;
        }

        connectionStatus.textContent = 'Menghubungkan...';
        connectionStatus.className = 'status-offline';

        ws = new WebSocket(websocketUrl);

        ws.onopen = () => {
            console.log('Connected to backend WebSocket');
            connectionStatus.textContent = 'Online';
            connectionStatus.className = 'status-online';
            reconnectAttempts = 0;
            noOpportunitiesMessage.style.display = 'block'; 
            opportunitiesTableBody.innerHTML = ''; 
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'arbitrage_opportunities') {
                updateOpportunitiesTable(data.data);
            }
        };

        ws.onclose = () => {
            console.log('Disconnected from backend WebSocket');
            connectionStatus.textContent = 'Offline';
            connectionStatus.className = 'status-offline';
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                console.log(`Attempting to reconnect in ${reconnectInterval / 1000} seconds... (Attempt ${reconnectAttempts})`);
                setTimeout(connectWebSocket, reconnectInterval);
            } else {
                console.error('Max reconnect attempts reached. Please check backend server.');
                connectionStatus.textContent = 'Gagal Koneksi';
                connectionStatus.className = 'status-offline';
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket Error:', error);
        };
    }

    function updateOpportunitiesTable(opportunities) {
        opportunitiesTableBody.innerHTML = '';
        if (opportunities.length === 0) {
            noOpportunitiesMessage.style.display = 'block';
        } else {
            noOpportunitiesMessage.style.display = 'none';
            opportunities.forEach(opportunity => {
                const row = opportunitiesTableBody.insertRow();
                row.insertCell().textContent = opportunity.symbol;
                row.insertCell().textContent = opportunity.buy_exchange;
                row.insertCell().textContent = opportunity.buy_price.toFixed(8);
                row.insertCell().textContent = opportunity.sell_exchange;
                row.insertCell().textContent = opportunity.sell_price.toFixed(8);
                
                const profitPercentageCell = row.insertCell();
                profitPercentageCell.textContent = opportunity.net_profit_percent.toFixed(4) + '%';
                profitPercentageCell.style.color = opportunity.net_profit_percent > 0 ? '#4CAF50' : '#f44336';

                const profitUsdCell = row.insertCell();
                profitUsdCell.textContent = '$' + opportunity.gross_profit_usd.toFixed(4);
                profitUsdCell.style.color = opportunity.gross_profit_usd > 0 ? '#4CAF50' : '#f44336';
            });
        }
    }

    connectWebSocket();
});
