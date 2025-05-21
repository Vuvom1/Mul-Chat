class SSEHandler {
    constructor(options = {}) {
        this.onMessageCallback = options.onMessage || this.defaultMessageHandler;
        this.onConnectCallback = options.onConnect || (() => console.log('SSE connected'));
        this.onErrorCallback = options.onError || ((error) => console.error('SSE error:', error));
        this.autoReconnect = options.autoReconnect !== false;
        this.reconnectInterval = options.reconnectInterval || 5000;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.reconnectAttempts = 0;
        
        this.eventSource = null;
    }
    
    connect() {
        if (this.eventSource) {
            this.disconnect();
        }
        
        try {
            this.eventSource = new EventSource('/sse');
            
            this.eventSource.onopen = () => {
                console.log('SSE connection established');
                this.reconnectAttempts = 0;
                this.onConnectCallback();
            };
            
            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing SSE message:', error);
                }
            };
            
            this.eventSource.onerror = (error) => {
                this.onErrorCallback(error);
                
                if (this.autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
                    console.log(`SSE connection error. Reconnecting in ${this.reconnectInterval/1000}s...`);
                    this.eventSource.close();
                    this.reconnectAttempts++;
                    setTimeout(() => this.connect(), this.reconnectInterval);
                } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                    console.error('Max SSE reconnection attempts reached');
                }
            };
        } catch (error) {
            console.error('Failed to create EventSource:', error);
        }
    }
    
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
    
    handleMessage(data) {
        // Ignore ping messages
        if (data.type === 'ping') {
            return;
        }
        
        this.onMessageCallback(data);
    }
    
    defaultMessageHandler(data) {
        console.log('SSE message received:', data);
    }
}

// Usage:
// const sseHandler = new SSEHandler({
//     onMessage: (data) => {
//         // Handle the message
//         if (data.type === 'chat') {
//             appendChatMessage(data);
//         }
//     }
// });
// sseHandler.connect();