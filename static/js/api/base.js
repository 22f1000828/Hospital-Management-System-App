const API_BASE = '/api';

const api = {
    async request(method, endpoint, data = null, options = {}) {
        const config = {
            method,
            url: `${API_BASE}${endpoint}`,
            headers: options.headers || {
                'Content-Type': 'application/json',
            },
            withCredentials: true,
            responseType: options.responseType || 'json'
        };
        
        if (data) {
            config.data = data;
        }
        
        try {
            const response = await axios(config);
            if (options.responseType === 'blob') {
                const blob = new Blob([response.data], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                const filename = endpoint.split('/').pop();
                link.setAttribute('download', filename);
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
                return { success: true };
            }
            return response.data;
        } catch (err) {
            if (err.response) {
                throw err.response.data;
            }
            throw { error: 'Network error' };
        }
    },
    
    get(endpoint) {
        return this.request('GET', endpoint);
    },
    
    post(endpoint, data) {
        return this.request('POST', endpoint, data);
    },
    
    put(endpoint, data) {
        return this.request('PUT', endpoint, data);
    },
    
    delete(endpoint) {
        return this.request('DELETE', endpoint);
    }
};

