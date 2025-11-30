const doctorAPI = {
    getDashboard() {
        return api.get('/doctor/dashboard');
    },
    
    getAppointments(status = '') {
        const params = status ? `?status=${status}` : '';
        return api.get(`/doctor/appointments${params}`);
    },
    
    getAppointment(id) {
        return api.get(`/doctor/appointments/${id}`);
    },
    
    updateAppointmentStatus(id, status) {
        return api.put(`/doctor/appointments/${id}/status`, { status });
    },
    
    addTreatment(appointmentId, data) {
        return api.post(`/doctor/appointments/${appointmentId}/treatment`, data);
    },
    
    updateTreatment(treatmentId, data) {
        return api.put(`/doctor/treatments/${treatmentId}`, data);
    },
    
    getPatients() {
        return api.get('/doctor/patients');
    },
    
    getPatientHistory(patientId) {
        return api.get(`/doctor/patients/${patientId}/history`);
    },
    
    getAvailability() {
        return api.get('/doctor/availability');
    },
    
    setAvailability(data) {
        return api.post('/doctor/availability', data);
    },
    
    deleteAvailability(id) {
        return api.delete(`/doctor/availability/${id}`);
    }
};

