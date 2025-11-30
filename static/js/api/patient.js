const patientAPI = {
    getDashboard() {
        return api.get('/patient/dashboard');
    },
    
    getProfile() {
        return api.get('/patient/profile');
    },
    
    updateProfile(data) {
        return api.put('/patient/profile', data);
    },
    
    getDoctors(search = '', specialization_id = null) {
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (specialization_id) params.append('specialization_id', specialization_id);
        return api.get(`/patient/doctors?${params.toString()}`);
    },
    
    getDoctorAvailability(doctorId, date) {
        return api.get(`/patient/doctors/${doctorId}/availability?date=${date}`);
    },
    
    bookAppointment(data) {
        return api.post('/patient/appointments', data);
    },
    
    getAppointments() {
        return api.get('/patient/appointments');
    },
    
    getAppointment(id) {
        return api.get(`/patient/appointments/${id}`);
    },
    
    cancelAppointment(id) {
        return api.post(`/patient/appointments/${id}/cancel`);
    },
    
    rescheduleAppointment(id, data) {
        return api.put(`/patient/appointments/${id}`, data);
    },
    
    getHistory() {
        return api.get('/patient/history');
    },
    
    exportHistory() {
        return api.post('/patient/history/export');
    },
    
    listExports() {
        return api.get('/patient/exports');
    },
    
    downloadExport(filename) {
        return api.get(`/patient/exports/${filename}`, null, { responseType: 'blob' });
    }
    
    // old way - keeping for reference
    // downloadExportOld(filename) {
    //     return api.request('GET', `/patient/exports/${filename}`, null, { responseType: 'blob' });
    // }
};

