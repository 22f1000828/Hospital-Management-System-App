const DoctorDashboard = {
    data() {
        return {
            dashboard: null,
            loading: true
        };
    },
    async mounted() {
        try {
            this.dashboard = await doctorAPI.getDashboard();
        } catch (error) {
            window.appInstance.showError('Failed to load dashboard');
        } finally {
            this.loading = false;
        }
    },
    template: `
        <div class="container-fluid p-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Doctor Dashboard</h2>
                <div class="btn-group">
                    <router-link to="/doctor/appointments" class="btn btn-outline-primary">Appointments</router-link>
                    <router-link to="/doctor/availability" class="btn btn-outline-primary">Availability</router-link>
                </div>
            </div>
            <div v-if="loading" class="text-center">
                <div class="spinner-border" role="status"></div>
            </div>
            <div v-else-if="dashboard">
                <h4>Today's Appointments</h4>
                <div v-if="dashboard.today_appointments && dashboard.today_appointments.length > 0" class="table-responsive mb-4">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Patient</th>
                                <th>Reason</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="apt in dashboard.today_appointments" :key="apt.id">
                                <td>{{ apt.appointment_time }}</td>
                                <td>{{ apt.patient ? apt.patient.full_name : 'N/A' }}</td>
                                <td>{{ apt.reason || 'N/A' }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div v-else class="alert alert-info mb-4">No appointments scheduled for today.</div>
                <h4>This Week's Appointments</h4>
                <div v-if="dashboard.week_appointments && dashboard.week_appointments.length > 0" class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Time</th>
                                <th>Patient</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="apt in dashboard.week_appointments" :key="apt.id">
                                <td>{{ apt.appointment_date }}</td>
                                <td>{{ apt.appointment_time }}</td>
                                <td>{{ apt.patient ? apt.patient.full_name : 'N/A' }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div v-else class="alert alert-info">No appointments scheduled for this week.</div>
            </div>
        </div>
    `
};

const DoctorAppointments = {
    data() {
        return {
            appointments: [],
            status: '',
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
                const result = await doctorAPI.getAppointments(this.status);
                this.appointments = result.appointments;
            } catch (error) {
                window.appInstance.showError('Failed to load appointments');
            } finally {
                this.loading = false;
            }
        },
        async updateStatus(id, status) {
            try {
                await doctorAPI.updateAppointmentStatus(id, status);
                window.appInstance.showSuccess(`Appointment ${status.toLowerCase()}`);
                await this.loadAppointments();
            } catch (error) {
                window.appInstance.showError(error.error || 'Failed to update status');
            }
        },
        viewAppointment(id) {
            this.$router.push(`/doctor/appointments/${id}`);
        }
    },
    watch: {
        status() {
            this.loadAppointments();
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Appointments</h2>
            <div class="card mb-4">
                <div class="card-body">
                    <select v-model="status" class="form-select">
                        <option value="">All Status</option>
                        <option value="Booked">Booked</option>
                        <option value="Completed">Completed</option>
                        <option value="Cancelled">Cancelled</option>
                    </select>
                </div>
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
                            <th>Patient</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="apt in appointments" :key="apt.id">
                            <td>{{ apt.appointment_date }}</td>
                            <td>{{ apt.appointment_time }}</td>
                            <td>{{ apt.patient ? apt.patient.full_name : 'N/A' }}</td>
                            <td>
                                <span class="badge" :class="{
                                    'bg-success': apt.status === 'Completed',
                                    'bg-warning': apt.status === 'Booked',
                                    'bg-danger': apt.status === 'Cancelled'
                                }">{{ apt.status }}</span>
                            </td>
                            <td>
                                <button @click="viewAppointment(apt.id)" class="btn btn-sm btn-info me-2">View/Add Treatment</button>
                                <button v-if="apt.status === 'Booked'" @click="updateStatus(apt.id, 'Completed')" class="btn btn-sm btn-success me-2">Complete</button>
                                <button v-if="apt.status === 'Booked'" @click="updateStatus(apt.id, 'Cancelled')" class="btn btn-sm btn-danger">Cancel</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `
};

const DoctorAppointmentDetail = {
    data() {
        return {
            appointment: null,
            treatment: {
                diagnosis: '',
                prescription: '',
                notes: ''
            },
            loading: true,
            saving: false
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
                const result = await doctorAPI.getAppointment(appointmentId);
                this.appointment = result;
                if (result.treatment) {
                    this.treatment = {
                        diagnosis: result.treatment.diagnosis || '',
                        prescription: result.treatment.prescription || '',
                        notes: result.treatment.notes || ''
                    };
                }
            } catch (error) {
                window.appInstance.showError('Failed to load appointment');
            } finally {
                this.loading = false;
            }
        },
        async saveTreatment() {
            this.saving = true;
            try {
                if (this.appointment.treatment && this.appointment.treatment.id) {
                    await doctorAPI.updateTreatment(this.appointment.treatment.id, this.treatment);
                    window.appInstance.showSuccess('Treatment updated');
                } else {
                    await doctorAPI.addTreatment(this.appointment.id, this.treatment);
                    window.appInstance.showSuccess('Treatment added');
                }
                await this.loadAppointment();
            } catch (error) {
                window.appInstance.showError(error.error || 'Failed to save treatment');
            } finally {
                this.saving = false;
            }
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Appointment Details</h2>
            <div v-if="loading" class="text-center">
                <div class="spinner-border" role="status"></div>
            </div>
            <div v-else-if="appointment">
                <div class="card mb-4">
                    <div class="card-body">
                        <h5>Patient: {{ appointment.patient ? appointment.patient.full_name : 'N/A' }}</h5>
                        <p>Date: {{ appointment.appointment_date }}</p>
                        <p>Time: {{ appointment.appointment_time }}</p>
                        <p>Status: <span class="badge bg-secondary">{{ appointment.status }}</span></p>
                        <p>Reason: {{ appointment.reason || 'N/A' }}</p>
                    </div>
                </div>
                <div class="card">
                    <div class="card-body">
                        <h5>Treatment</h5>
                        <form @submit.prevent="saveTreatment">
                            <div class="mb-3">
                                <label class="form-label">Diagnosis</label>
                                <textarea v-model="treatment.diagnosis" class="form-control" rows="3"></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Prescription</label>
                                <textarea v-model="treatment.prescription" class="form-control" rows="3"></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Notes</label>
                                <textarea v-model="treatment.notes" class="form-control" rows="3"></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary" :disabled="saving">
                                {{ saving ? 'Saving...' : 'Save Treatment' }}
                            </button>
                            <router-link to="/doctor/appointments" class="btn btn-secondary ms-2">Back</router-link>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `
};

const DoctorAvailability = {
    data() {
        return {
            availabilities: [],
            form: {
                date: '',
                start_time: '',
                end_time: ''
            },
            loading: true
        };
    },
    async mounted() {
        await this.loadAvailability();
    },
    methods: {
        async loadAvailability() {
            this.loading = true;
            try {
                const result = await doctorAPI.getAvailability();
                this.availabilities = result.availabilities;
            } catch (error) {
                window.appInstance.showError('Failed to load availability');
            } finally {
                this.loading = false;
            }
        },
        async addAvailability() {
            try {
                await doctorAPI.setAvailability(this.form);
                window.appInstance.showSuccess('Availability added');
                this.form = { date: '', start_time: '', end_time: '' };
                await this.loadAvailability();
            } catch (error) {
                window.appInstance.showError(error.error || 'Failed to add availability');
            }
        },
        async deleteAvailability(id) {
            if (!confirm('Delete this availability slot?')) return;
            try {
                await doctorAPI.deleteAvailability(id);
                window.appInstance.showSuccess('Availability deleted');
                await this.loadAvailability();
            } catch (error) {
                window.appInstance.showError('Failed to delete availability');
            }
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Manage Availability</h2>
            <div class="card mb-4">
                <div class="card-body">
                    <h5>Add Availability</h5>
                    <div class="row">
                        <div class="col-md-4">
                            <label class="form-label">Date</label>
                            <input v-model="form.date" type="date" class="form-control">
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Start Time</label>
                            <input v-model="form.start_time" type="time" class="form-control">
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">End Time</label>
                            <input v-model="form.end_time" type="time" class="form-control">
                        </div>
                    </div>
                    <button @click="addAvailability" class="btn btn-primary mt-3">Add</button>
                </div>
            </div>
            <div v-if="loading" class="text-center">
                <div class="spinner-border" role="status"></div>
            </div>
            <div v-else class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Start Time</th>
                            <th>End Time</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="avail in availabilities" :key="avail.id">
                            <td>{{ avail.date }}</td>
                            <td>{{ avail.start_time }}</td>
                            <td>{{ avail.end_time }}</td>
                            <td>
                                <button @click="deleteAvailability(avail.id)" class="btn btn-sm btn-danger">Delete</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `
};

window.DoctorDashboard = DoctorDashboard;
window.DoctorAppointments = DoctorAppointments;
window.DoctorAppointmentDetail = DoctorAppointmentDetail;
window.DoctorAvailability = DoctorAvailability;

