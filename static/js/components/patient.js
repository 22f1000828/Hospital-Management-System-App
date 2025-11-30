const PatientDashboard = {
    data() {
        return {
            dashboard: null,
            loading: true
        };
    },
    async mounted() {
        try {
            this.dashboard = await patientAPI.getDashboard();
        } catch (err) {
            window.appInstance.showError('Failed to load dashboard');
        } finally {
            this.loading = false;
        }
    },
    template: `
        <div class="container-fluid p-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Patient Dashboard</h2>
                <div class="btn-group">
                    <router-link to="/patient/doctors" class="btn btn-outline-primary">Find Doctors</router-link>
                    <router-link to="/patient/appointments" class="btn btn-outline-primary">My Appointments</router-link>
                    <router-link to="/patient/history" class="btn btn-outline-primary">History</router-link>
                </div>
            </div>
            <div v-if="loading" class="text-center">
                <div class="spinner-border" role="status"></div>
            </div>
            <div v-else-if="dashboard">
                <h4>Upcoming Appointments</h4>
                <div class="table-responsive mb-4">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Time</th>
                                <th>Doctor</th>
                                <th>Specialization</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="apt in dashboard.upcoming_appointments" :key="apt.id">
                                <td>{{ apt.appointment_date }}</td>
                                <td>{{ apt.appointment_time }}</td>
                                <td>{{ apt.doctor ? apt.doctor.full_name : 'N/A' }}</td>
                                <td>{{ apt.doctor ? apt.doctor.specialization : 'N/A' }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `
};

const PatientDoctors = {
    data() {
        return {
            doctors: [],
            search: '',
            specialization_id: null,
            departments: [],
            loading: true
        };
    },
    async mounted() {
        await this.loadDepartments();
        await this.loadDoctors();
    },
    methods: {
        async loadDepartments() {
            try {
                const result = await commonAPI.getDepartments();
                this.departments = result.departments;
            } catch (error) {
                window.appInstance.showError('Failed to load departments');
            }
        },
        async loadDoctors() {
            this.loading = true;
            try {
                const result = await patientAPI.getDoctors(this.search, this.specialization_id);
                this.doctors = result.doctors;
            } catch (error) {
                window.appInstance.showError('Failed to load doctors');
            } finally {
                this.loading = false;
            }
        }
    },
    watch: {
        search() {
            this.loadDoctors();
        },
        specialization_id() {
            this.loadDoctors();
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Find Doctors</h2>
            <div class="card mb-4">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <input v-model="search" type="text" class="form-control" placeholder="Search doctors...">
                        </div>
                        <div class="col-md-4">
                            <select v-model="specialization_id" class="form-select">
                                <option :value="null">All Specializations</option>
                                <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
            <div v-if="loading" class="text-center">
                <div class="spinner-border" role="status"></div>
            </div>
            <div v-else class="row">
                <div v-for="doctor in doctors" :key="doctor.id" class="col-md-4 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <h5>{{ doctor.full_name }}</h5>
                            <p class="text-muted">{{ doctor.specialization || 'N/A' }}</p>
                            <p>{{ doctor.phone }}</p>
                            <router-link :to="'/patient/book/' + doctor.id" class="btn btn-primary">Book Appointment</router-link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

const PatientBookAppointment = {
    data() {
        return {
            doctor: null,
            form: {
                appointment_date: '',
                appointment_time: '',
                reason: ''
            },
            available_times: [],
            loading: false,
            loadingTimes: false
        };
    },
    async mounted() {
        await this.loadDoctor();
        const today = new Date().toISOString().split('T')[0];
        this.form.appointment_date = today;
        if (this.form.appointment_date) {
            await this.loadAvailability();
        }
    },
    methods: {
        async loadDoctor() {
            try {
                const doctorId = this.$route.params.id;
                const result = await patientAPI.getDoctors();
                this.doctor = result.doctors.find(d => d.id == doctorId);
                if (!this.doctor) {
                    window.appInstance.showError('Doctor not found');
                    this.$router.push('/patient/doctors');
                }
            } catch (error) {
                window.appInstance.showError('Failed to load doctor');
            }
        },
        async loadAvailability() {
            if (!this.form.appointment_date || !this.doctor) return;
            this.loadingTimes = true;
            try {
                const result = await patientAPI.getDoctorAvailability(this.doctor.id, this.form.appointment_date);
                this.available_times = result.available_times;
            } catch (error) {
                window.appInstance.showError('Failed to load availability');
            } finally {
                this.loadingTimes = false;
            }
        },
        async handleSubmit() {
            this.loading = true;
            try {
                await patientAPI.bookAppointment({
                    doctor_id: this.doctor.id,
                    appointment_date: this.form.appointment_date,
                    appointment_time: this.form.appointment_time,
                    reason: this.form.reason
                });
                window.appInstance.showSuccess('Appointment booked successfully');
                this.$router.push('/patient/dashboard');
            } catch (error) {
                window.appInstance.showError(error.error || 'Failed to book appointment');
            } finally {
                this.loading = false;
            }
        }
    },
    watch: {
        'form.appointment_date'() {
            this.loadAvailability();
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Book Appointment</h2>
            <div v-if="doctor" class="card mb-4">
                <div class="card-body">
                    <h5>Dr. {{ doctor.full_name }}</h5>
                    <p class="text-muted">{{ doctor.specialization || 'N/A' }}</p>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <form @submit.prevent="handleSubmit">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Appointment Date *</label>
                                <input v-model="form.appointment_date" type="date" class="form-control" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Appointment Time *</label>
                                <select v-model="form.appointment_time" class="form-select" required :disabled="loadingTimes">
                                    <option value="">Select Time</option>
                                    <option v-for="time in available_times" :key="time" :value="time">{{ time }}</option>
                                </select>
                                <small v-if="loadingTimes" class="text-muted">Loading available times...</small>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Reason</label>
                            <textarea v-model="form.reason" class="form-control" rows="3"></textarea>
                        </div>
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary" :disabled="loading">
                                {{ loading ? 'Booking...' : 'Book Appointment' }}
                            </button>
                            <router-link to="/patient/doctors" class="btn btn-secondary">Cancel</router-link>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `
};

const PatientAppointments = {
    data() {
        return {
            appointments: [],
            loading: true
        };
    },
    async mounted() {
        await this.loadAppointments();
    },
    methods: {
        async loadAppointments() {
            this.loading = true;
            try {
                const result = await patientAPI.getAppointments();
                this.appointments = result.appointments;
            } catch (error) {
                window.appInstance.showError('Failed to load appointments');
            } finally {
                this.loading = false;
            }
        },
        async cancelAppointment(id) {
            if (!confirm('Cancel this appointment?')) return;
            try {
                await patientAPI.cancelAppointment(id);
                window.appInstance.showSuccess('Appointment cancelled');
                await this.loadAppointments();
            } catch (error) {
                window.appInstance.showError(error.error || 'Failed to cancel appointment');
            }
        },
        rescheduleAppointment(id) {
            this.$router.push(`/patient/appointments/reschedule/${id}`);
        },
        viewTreatment(id) {
            this.$router.push(`/patient/appointments/${id}`);
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">My Appointments</h2>
            <div v-if="loading" class="text-center">
                <div class="spinner-border" role="status"></div>
            </div>
            <div v-else class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Doctor</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="apt in appointments" :key="apt.id">
                            <td>{{ apt.appointment_date }}</td>
                            <td>{{ apt.appointment_time }}</td>
                            <td>{{ apt.doctor ? apt.doctor.full_name : 'N/A' }}</td>
                            <td>
                                <span class="badge" :class="{
                                    'bg-success': apt.status === 'Completed',
                                    'bg-warning': apt.status === 'Booked',
                                    'bg-danger': apt.status === 'Cancelled'
                                }">{{ apt.status }}</span>
                            </td>
                            <td>
                                <button v-if="apt.status === 'Booked'" @click="rescheduleAppointment(apt.id)" class="btn btn-sm btn-warning me-2">Reschedule</button>
                                <button v-if="apt.status === 'Booked'" @click="cancelAppointment(apt.id)" class="btn btn-sm btn-danger me-2">Cancel</button>
                                <button v-if="apt.treatment" @click="viewTreatment(apt.id)" class="btn btn-sm btn-info">View Treatment</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `
};

const PatientAppointmentDetail = {
    data() {
        return {
            appointment: null,
            loading: true
        };
    },
    async mounted() {
        await this.loadAppointment();
    },
    methods: {
        async loadAppointment() {
            this.loading = true;
            try {
                const appointmentId = this.$route.params.id;
                const result = await patientAPI.getAppointment(appointmentId);
                this.appointment = result;
            } catch (error) {
                window.appInstance.showError('Failed to load appointment');
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Appointment Details</h2>
            <div v-if="loading" class="text-center">
                <div class="spinner-border" role="status"></div>
            </div>
            <div v-else-if="appointment" class="card">
                <div class="card-body">
                    <h5>Doctor: {{ appointment.doctor ? appointment.doctor.full_name : 'N/A' }}</h5>
                    <p>Specialization: {{ appointment.doctor ? appointment.doctor.specialization : 'N/A' }}</p>
                    <p>Date: {{ appointment.appointment_date }}</p>
                    <p>Time: {{ appointment.appointment_time }}</p>
                    <p>Status: <span class="badge bg-secondary">{{ appointment.status }}</span></p>
                    <p>Reason: {{ appointment.reason || 'N/A' }}</p>
                    <div v-if="appointment.treatment" class="mt-4">
                        <h5>Treatment</h5>
                        <p><strong>Diagnosis:</strong> {{ appointment.treatment.diagnosis || 'N/A' }}</p>
                        <p><strong>Prescription:</strong> {{ appointment.treatment.prescription || 'N/A' }}</p>
                        <p><strong>Notes:</strong> {{ appointment.treatment.notes || 'N/A' }}</p>
                    </div>
                    <router-link to="/patient/appointments" class="btn btn-secondary mt-3">Back</router-link>
                </div>
            </div>
        </div>
    `
};

const PatientRescheduleAppointment = {
    data() {
        return {
            appointment: null,
            form: {
                appointment_date: '',
                appointment_time: '',
                reason: ''
            },
            available_times: [],
            loading: false,
            loadingTimes: false
        };
    },
    async mounted() {
        await this.loadAppointment();
    },
    methods: {
        async loadAppointment() {
            try {
                const appointmentId = this.$route.params.id;
                const result = await patientAPI.getAppointment(appointmentId);
                this.appointment = result;
                this.form.appointment_date = result.appointment_date;
                this.form.appointment_time = result.appointment_time;
                this.form.reason = result.reason || '';
                if (this.form.appointment_date && result.doctor) {
                    await this.loadAvailability();
                }
            } catch (error) {
                window.appInstance.showError('Failed to load appointment');
            }
        },
        async loadAvailability() {
            if (!this.form.appointment_date || !this.appointment.doctor) return;
            this.loadingTimes = true;
            try {
                const result = await patientAPI.getDoctorAvailability(this.appointment.doctor.id, this.form.appointment_date);
                this.available_times = result.available_times;
            } catch (error) {
                window.appInstance.showError('Failed to load availability');
            } finally {
                this.loadingTimes = false;
            }
        },
        async handleSubmit() {
            this.loading = true;
            try {
                await patientAPI.rescheduleAppointment(this.appointment.id, {
                    appointment_date: this.form.appointment_date,
                    appointment_time: this.form.appointment_time,
                    reason: this.form.reason
                });
                window.appInstance.showSuccess('Appointment rescheduled successfully');
                this.$router.push('/patient/appointments');
            } catch (error) {
                window.appInstance.showError(error.error || 'Failed to reschedule appointment');
            } finally {
                this.loading = false;
            }
        }
    },
    watch: {
        'form.appointment_date'() {
            this.loadAvailability();
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Reschedule Appointment</h2>
            <div v-if="appointment" class="card">
                <div class="card-body">
                    <form @submit.prevent="handleSubmit">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Appointment Date *</label>
                                <input v-model="form.appointment_date" type="date" class="form-control" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Appointment Time *</label>
                                <select v-model="form.appointment_time" class="form-select" required :disabled="loadingTimes">
                                    <option value="">Select Time</option>
                                    <option v-for="time in available_times" :key="time" :value="time">{{ time }}</option>
                                </select>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Reason</label>
                            <textarea v-model="form.reason" class="form-control" rows="3"></textarea>
                        </div>
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary" :disabled="loading">
                                {{ loading ? 'Rescheduling...' : 'Reschedule Appointment' }}
                            </button>
                            <router-link to="/patient/appointments" class="btn btn-secondary">Cancel</router-link>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `
};

const PatientHistory = {
    data() {
        return {
            appointments: [],
            loading: true,
            exporting: false
        };
    },
    async mounted() {
        await this.loadHistory();
    },
    methods: {
        async loadHistory() {
            this.loading = true;
            try {
                const result = await patientAPI.getHistory();
                this.appointments = result.appointments;
            } catch (error) {
                window.appInstance.showError('Failed to load history');
            } finally {
                this.loading = false;
            }
        },
        async exportHistory() {
            this.exporting = true;
            try {
                await patientAPI.exportHistory();
                window.appInstance.showSuccess('Export started. Download will begin shortly...');
                
                let attempts = 0;
                const maxAttempts = 10;
                const checkInterval = 1000;
                
                const checkAndDownload = async () => {
                    attempts++;
                    try {
                        const result = await patientAPI.listExports();
                        if (result.exports && result.exports.length > 0) {
                            const latestExport = result.exports[0];
                            await patientAPI.downloadExport(latestExport.filename);
                            window.appInstance.showSuccess('Download started');
                            this.exporting = false;
                            return;
                        }
                        
                        if (attempts < maxAttempts) {
                            setTimeout(checkAndDownload, checkInterval);
                        } else {
                            window.appInstance.showError('Export timeout. Please try again later.');
                            this.exporting = false;
                        }
                    } catch (error) {
                        if (attempts < maxAttempts) {
                            setTimeout(checkAndDownload, checkInterval);
                        } else {
                            window.appInstance.showError('Failed to download export');
                            this.exporting = false;
                        }
                    }
                };
                
                setTimeout(checkAndDownload, 2000);
            } catch (error) {
                window.appInstance.showError('Failed to start export');
                this.exporting = false;
            }
        }
    },
    template: `
        <div class="container-fluid p-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Treatment History</h2>
                <button @click="exportHistory" class="btn btn-primary" :disabled="exporting">
                    {{ exporting ? 'Exporting & Downloading...' : 'Export & Download CSV' }}
                </button>
            </div>
            
            <div v-if="loading" class="text-center">
                <div class="spinner-border" role="status"></div>
            </div>
            <div v-else class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Doctor</th>
                            <th>Diagnosis</th>
                            <th>Prescription</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="apt in appointments" :key="apt.id">
                            <td>{{ apt.appointment_date }}</td>
                            <td>{{ apt.appointment_time }}</td>
                            <td>{{ apt.doctor ? apt.doctor.full_name : 'N/A' }}</td>
                            <td>{{ apt.treatment ? apt.treatment.diagnosis : 'N/A' }}</td>
                            <td>{{ apt.treatment ? apt.treatment.prescription : 'N/A' }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `
};

window.PatientDashboard = PatientDashboard;
window.PatientDoctors = PatientDoctors;
window.PatientBookAppointment = PatientBookAppointment;
window.PatientAppointments = PatientAppointments;
window.PatientAppointmentDetail = PatientAppointmentDetail;
window.PatientRescheduleAppointment = PatientRescheduleAppointment;
window.PatientHistory = PatientHistory;

