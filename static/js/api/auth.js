const authAPI = {
    login(username, password, role, remember = false) {
        return api.post('/auth/login', { username, password, role, remember });
    },
    
    logout() {
        return api.post('/auth/logout');
    },
    
    register(data) {
        return api.post('/auth/register', data);
    },
    
    getCurrentUser() {
        return api.get('/auth/me');
    }
};

