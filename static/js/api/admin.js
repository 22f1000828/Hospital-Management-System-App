const adminAPI = {
    getDashboard() {
        return api.get('/admin/dashboard');
    },
    
    getDoctors(search = '', specialization_id = null) {
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (specialization_id) params.append('specialization_id', specialization_id);
        return api.get(`/admin/doctors?${params.toString()}`);
    },
    
    addDoctor(data) {
        return api.post('/admin/doctors', data);
    },
    
    updateDoctor(id, data) {
        return api.put(`/admin/doctors/${id}`, data);
    },
    
    deactivateDoctor(id) {
        return api.post(`/admin/doctors/${id}/deactivate`);
    },
    
    getPatients(search = '') {
        const params = search ? `?search=${encodeURIComponent(search)}` : '';
        return api.get(`/admin/patients${params}`);
    },
    
    deactivatePatient(id) {
        return api.post(`/admin/patients/${id}/deactivate`);
    },
    
    getAppointments(search = '', status = '') {
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (status) params.append('status', status);
        return api.get(`/admin/appointments?${params.toString()}`);
    },
    
    getPatientHistory(patientId) {
        return api.get(`/admin/patients/${patientId}/history`);
    }
    
    // temp = null;
};

