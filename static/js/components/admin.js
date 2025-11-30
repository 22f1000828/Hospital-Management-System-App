const AdminDashboard = {
    data() {
        return {
            stats: null,
            loading: true
        };
    },
    async mounted() {
        try {
            this.stats = await adminAPI.getDashboard();
        } catch (error) {
            window.appInstance.showError('Failed to load dashboard');
        } finally {
            this.loading = false;
        }
    },
    template: `
        <div class="container-fluid p-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Admin Dashboard</h2>
                <div class="btn-group">
                    <router-link to="/admin/doctors" class="btn btn-outline-primary">Doctors</router-link>
                    <router-link to="/admin/patients" class="btn btn-outline-primary">Patients</router-link>
                    <router-link to="/admin/appointments" class="btn btn-outline-primary">Appointments</router-link>
                </div>
            </div>
            <div v-if="loading" class="text-center">
                <div class="spinner-border" role="status"></div>
            </div>
            <div v-else-if="stats" class="row">
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-primary">
                        <div class="card-body">
                            <h5 class="card-title">Total Patients</h5>
                            <h2>{{ stats.total_patients }}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-success">
                        <div class="card-body">
                            <h5 class="card-title">Total Doctors</h5>
                            <h2>{{ stats.total_doctors }}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-info">
                        <div class="card-body">
                            <h5 class="card-title">Total Appointments</h5>
                            <h2>{{ stats.total_appointments }}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-4">
                    <div class="card text-white bg-warning">
                        <div class="card-body">
                            <h5 class="card-title">Upcoming</h5>
                            <h2>{{ stats.upcoming_appointments }}</h2>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

const AdminDoctors = {
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
                const result = await adminAPI.getDoctors(this.search, this.specialization_id);
                this.doctors = result.doctors;
            } catch (error) {
                window.appInstance.showError('Failed to load doctors');
            } finally {
                this.loading = false;
            }
        },
        async deleteDoctor(id) {
            if (!confirm('Are you sure you want to delete this doctor? This action cannot be undone.')) return;
            try {
                await adminAPI.deleteDoctor(id);
                window.appInstance.showSuccess('Doctor deleted');
                await this.loadDoctors();
            } catch (error) {
                window.appInstance.showError('Failed to delete doctor');
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
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Doctors</h2>
                <router-link to="/admin/doctors/add" class="btn btn-primary">Add Doctor</router-link>
            </div>
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
            <div v-else class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Specialization</th>
                            <th>Phone</th>
                            <th>Email</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="doctor in doctors" :key="doctor.id">
                            <td>{{ doctor.full_name }}</td>
                            <td>{{ doctor.specialization || 'N/A' }}</td>
                            <td>{{ doctor.phone }}</td>
                            <td>{{ doctor.email }}</td>
                            <td>
                                <router-link :to="'/admin/doctors/edit/' + doctor.id" class="btn btn-sm btn-primary me-2">Edit</router-link>
                                <button @click="deleteDoctor(doctor.id)" class="btn btn-sm btn-danger">Delete</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `
};

const AdminAddDoctor = {
    data() {
        return {
            form: {
                username: '',
                password: 'doctor123',
                email: '',
                first_name: '',
                last_name: '',
                specialization_id: null,
                phone: '',
                license_number: ''
            },
            departments: [],
            loading: false
        };
    },
    async mounted() {
        await this.loadDepartments();
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
        async handleSubmit() {
            this.loading = true;
            try {
                const result = await adminAPI.addDoctor(this.form);
                window.appInstance.showSuccess(`Doctor added successfully. Password: ${result.password}`);
                this.$router.push('/admin/doctors');
            } catch (error) {
                window.appInstance.showError(error.error || 'Failed to add doctor');
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Add Doctor</h2>
            <div class="card">
                <div class="card-body">
                    <form @submit.prevent="handleSubmit">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">First Name *</label>
                                <input v-model="form.first_name" type="text" class="form-control" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Last Name *</label>
                                <input v-model="form.last_name" type="text" class="form-control" required>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Username *</label>
                                <input v-model="form.username" type="text" class="form-control" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Email *</label>
                                <input v-model="form.email" type="email" class="form-control" required>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Password (default: doctor123)</label>
                                <input v-model="form.password" type="password" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Phone *</label>
                                <input v-model="form.phone" type="tel" class="form-control" required>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Specialization *</label>
                                <select v-model="form.specialization_id" class="form-select" required>
                                    <option :value="null">Select Specialization</option>
                                    <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">License Number</label>
                                <input v-model="form.license_number" type="text" class="form-control">
                            </div>
                        </div>
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary" :disabled="loading">
                                {{ loading ? 'Adding...' : 'Add Doctor' }}
                            </button>
                            <router-link to="/admin/doctors" class="btn btn-secondary">Cancel</router-link>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `
};

const AdminEditDoctor = {
    data() {
        return {
            form: {
                username: '',
                email: '',
                password: '',
                first_name: '',
                last_name: '',
                specialization_id: null,
                phone: '',
                license_number: ''
            },
            departments: [],
            loading: false,
            doctorId: null
        };
    },
    async mounted() {
        this.doctorId = this.$route.params.id;
        await this.loadDepartments();
        await this.loadDoctor();
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
        async loadDoctor() {
            try {
                const result = await adminAPI.getDoctors();
                const doctor = result.doctors.find(d => d.id == this.doctorId);
                if (doctor) {
                    this.form = {
                        username: doctor.username || '',
                        email: doctor.email || '',
                        password: '',
                        first_name: doctor.first_name || '',
                        last_name: doctor.last_name || '',
                        specialization_id: doctor.specialization_id || null,
                        phone: doctor.phone || '',
                        license_number: doctor.license_number || ''
                    };
                }
            } catch (error) {
                window.appInstance.showError('Failed to load doctor');
            }
        },
        async handleSubmit() {
            this.loading = true;
            try {
                await adminAPI.updateDoctor(this.doctorId, this.form);
                window.appInstance.showSuccess('Doctor updated successfully');
                this.$router.push('/admin/doctors');
            } catch (error) {
                window.appInstance.showError(error.error || 'Failed to update doctor');
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Edit Doctor</h2>
            <div class="card">
                <div class="card-body">
                    <form @submit.prevent="handleSubmit">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">First Name *</label>
                                <input v-model="form.first_name" type="text" class="form-control" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Last Name *</label>
                                <input v-model="form.last_name" type="text" class="form-control" required>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Username *</label>
                                <input v-model="form.username" type="text" class="form-control" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Email *</label>
                                <input v-model="form.email" type="email" class="form-control" required>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Password (leave blank to keep current)</label>
                                <input v-model="form.password" type="password" class="form-control">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Phone *</label>
                                <input v-model="form.phone" type="tel" class="form-control" required>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Specialization *</label>
                                <select v-model="form.specialization_id" class="form-select" required>
                                    <option :value="null">Select Specialization</option>
                                    <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
                                </select>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">License Number</label>
                                <input v-model="form.license_number" type="text" class="form-control">
                            </div>
                        </div>
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary" :disabled="loading">
                                {{ loading ? 'Updating...' : 'Update Doctor' }}
                            </button>
                            <router-link to="/admin/doctors" class="btn btn-secondary">Cancel</router-link>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `
};

const AdminPatients = {
    data() {
        return {
            patients: [],
            search: '',
            loading: true
        };
    },
    async mounted() {
        await this.loadPatients();
    },
    methods: {
        async loadPatients() {
            this.loading = true;
            try {
                const result = await adminAPI.getPatients(this.search);
                this.patients = result.patients;
            } catch (error) {
                window.appInstance.showError('Failed to load patients');
            } finally {
                this.loading = false;
            }
        },
        async deletePatient(id) {
            if (!confirm('Are you sure you want to delete this patient? This action cannot be undone.')) return;
            try {
                await adminAPI.deletePatient(id);
                window.appInstance.showSuccess('Patient deleted');
                await this.loadPatients();
            } catch (error) {
                window.appInstance.showError('Failed to delete patient');
            }
        },
        viewHistory(id) {
            this.$router.push(`/admin/patients/${id}/history`);
        }
    },
    watch: {
        search() {
            this.loadPatients();
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Patients</h2>
            <div class="card mb-4">
                <div class="card-body">
                    <input v-model="search" type="text" class="form-control" placeholder="Search patients...">
                </div>
            </div>
            <div v-if="loading" class="text-center">
                <div class="spinner-border" role="status"></div>
            </div>
            <div v-else class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Phone</th>
                            <th>Email</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="patient in patients" :key="patient.id">
                            <td>{{ patient.full_name }}</td>
                            <td>{{ patient.phone }}</td>
                            <td>{{ patient.email }}</td>
                            <td>
                                <button @click="viewHistory(patient.id)" class="btn btn-sm btn-info me-2">View History</button>
                                <button @click="deletePatient(patient.id)" class="btn btn-sm btn-danger">Delete</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `
};

const AdminAppointments = {
    data() {
        return {
            appointments: [],
            search: '',
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
                const result = await adminAPI.getAppointments(this.search, this.status);
                this.appointments = result.appointments;
            } catch (error) {
                window.appInstance.showError('Failed to load appointments');
            } finally {
                this.loading = false;
            }
        }
    },
    watch: {
        search() {
            this.loadAppointments();
        },
        status() {
            this.loadAppointments();
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Appointments</h2>
            <div class="card mb-4">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <input v-model="search" type="text" class="form-control" placeholder="Search...">
                        </div>
                        <div class="col-md-4">
                            <select v-model="status" class="form-select">
                                <option value="">All Status</option>
                                <option value="Booked">Booked</option>
                                <option value="Completed">Completed</option>
                                <option value="Cancelled">Cancelled</option>
                            </select>
                        </div>
                    </div>
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
                            <th>Doctor</th>
                            <th>Patient</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="apt in appointments" :key="apt.id">
                            <td>{{ apt.appointment_date }}</td>
                            <td>{{ apt.appointment_time }}</td>
                            <td>{{ apt.doctor ? apt.doctor.full_name : 'N/A' }}</td>
                            <td>{{ apt.patient ? apt.patient.full_name : 'N/A' }}</td>
                            <td>
                                <span class="badge" :class="{
                                    'bg-success': apt.status === 'Completed',
                                    'bg-warning': apt.status === 'Booked',
                                    'bg-danger': apt.status === 'Cancelled'
                                }">{{ apt.status }}</span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `
};

const AdminPatientHistory = {
    data() {
        return {
            patient: null,
            appointments: [],
            loading: true
        };
    },
    async mounted() {
        await this.loadHistory();
    },
    methods: {
        async loadHistory() {
            this.loading = true;
            try {
                const patientId = this.$route.params.id;
                const result = await adminAPI.getPatientHistory(patientId);
                this.patient = result.patient;
                this.appointments = result.appointments;
            } catch (error) {
                window.appInstance.showError('Failed to load patient history');
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
        <div class="container-fluid p-4">
            <h2 class="mb-4">Patient History</h2>
            <div v-if="loading" class="text-center">
                <div class="spinner-border" role="status"></div>
            </div>
            <div v-else-if="patient">
                <div class="card mb-4">
                    <div class="card-body">
                        <h5>{{ patient.full_name }}</h5>
                        <p>Email: {{ patient.email }}</p>
                        <p>Phone: {{ patient.phone }}</p>
                    </div>
                </div>
                <div class="table-responsive">
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
                <router-link to="/admin/patients" class="btn btn-secondary mt-3">Back</router-link>
            </div>
        </div>
    `
};

window.AdminDashboard = AdminDashboard;
window.AdminDoctors = AdminDoctors;
window.AdminAddDoctor = AdminAddDoctor;
window.AdminEditDoctor = AdminEditDoctor;
window.AdminPatients = AdminPatients;
window.AdminAppointments = AdminAppointments;
window.AdminPatientHistory = AdminPatientHistory;

