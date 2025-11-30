const HomePage = {
    template: `
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8 text-center">
                    <h1 class="display-4 mb-4">Hospital Management System</h1>
                    <p class="lead mb-4">Welcome to our comprehensive hospital management platform</p>
                    <div class="d-grid gap-2 d-md-block">
                        <router-link to="/login/admin" class="btn btn-primary btn-lg me-2 mb-2">Admin Login</router-link>
                        <router-link to="/login/doctor" class="btn btn-success btn-lg me-2 mb-2">Doctor Login</router-link>
                        <router-link to="/login/patient" class="btn btn-info btn-lg me-2 mb-2">Patient Login</router-link>
                        <router-link to="/register" class="btn btn-outline-primary btn-lg">Register as Patient</router-link>
                    </div>
                </div>
            </div>
        </div>
    `
};

const LoginPage = {
    data() {
        return {
            username: '',
            password: '',
            role: 'Patient',
            remember: false,
            loading: false
        };
    },
    computed: {
        app() {
            return window.appInstance;
        }
    },
    methods: {
        async handleLogin() {
            this.loading = true;
            try {
                await window.appInstance.login(this.username, this.password, this.role);
            } catch (error) {
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-5">
                    <div class="card shadow">
                        <div class="card-body p-5">
                            <h2 class="text-center mb-4">Login</h2>
                            <div v-if="app.error" class="alert alert-danger">{{ app.error }}</div>
                            <form @submit.prevent="handleLogin">
                                <div class="mb-3">
                                    <label class="form-label">Role</label>
                                    <select v-model="role" class="form-select" required>
                                        <option value="Patient">Patient</option>
                                        <option value="Doctor">Doctor</option>
                                        <option value="Admin">Admin</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Username</label>
                                    <input v-model="username" type="text" class="form-control" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Password</label>
                                    <input v-model="password" type="password" class="form-control" required>
                                </div>
                                <div class="mb-3 form-check">
                                    <input v-model="remember" type="checkbox" class="form-check-input" id="remember">
                                    <label class="form-check-label" for="remember">Remember me</label>
                                </div>
                                <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                                    {{ loading ? 'Logging in...' : 'Login' }}
                                </button>
                            </form>
                            <div class="text-center mt-3">
                                <router-link to="/register">Don't have an account? Register</router-link>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

const AdminLoginPage = {
    data() {
        return {
            username: '',
            password: '',
            remember: false,
            loading: false
        };
    },
    computed: {
        app() {
            return window.appInstance;
        }
    },
    methods: {
        async handleLogin() {
            this.loading = true;
            try {
                await window.appInstance.login(this.username, this.password, 'Admin');
            } catch (error) {
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-5">
                    <div class="card shadow border-primary">
                        <div class="card-body p-5">
                            <h2 class="text-center mb-4 text-primary">Admin Login</h2>
                            <div v-if="app.error" class="alert alert-danger">{{ app.error }}</div>
                            <form @submit.prevent="handleLogin">
                                <div class="mb-3">
                                    <label class="form-label">Username</label>
                                    <input v-model="username" type="text" class="form-control" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Password</label>
                                    <input v-model="password" type="password" class="form-control" required>
                                </div>
                                <div class="mb-3 form-check">
                                    <input v-model="remember" type="checkbox" class="form-check-input" id="remember">
                                    <label class="form-check-label" for="remember">Remember me</label>
                                </div>
                                <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                                    {{ loading ? 'Logging in...' : 'Login as Admin' }}
                                </button>
                            </form>
                            <div class="text-center mt-3">
                                <router-link to="/login">Other Login Options</router-link>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

const DoctorLoginPage = {
    data() {
        return {
            username: '',
            password: '',
            remember: false,
            loading: false
        };
    },
    computed: {
        app() {
            return window.appInstance;
        }
    },
    methods: {
        async handleLogin() {
            this.loading = true;
            try {
                await window.appInstance.login(this.username, this.password, 'Doctor');
            } catch (error) {
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-5">
                    <div class="card shadow border-success">
                        <div class="card-body p-5">
                            <h2 class="text-center mb-4 text-success">Doctor Login</h2>
                            <div v-if="app.error" class="alert alert-danger">{{ app.error }}</div>
                            <form @submit.prevent="handleLogin">
                                <div class="mb-3">
                                    <label class="form-label">Username</label>
                                    <input v-model="username" type="text" class="form-control" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Password</label>
                                    <input v-model="password" type="password" class="form-control" required>
                                </div>
                                <div class="mb-3 form-check">
                                    <input v-model="remember" type="checkbox" class="form-check-input" id="remember">
                                    <label class="form-check-label" for="remember">Remember me</label>
                                </div>
                                <button type="submit" class="btn btn-success w-100" :disabled="loading">
                                    {{ loading ? 'Logging in...' : 'Login as Doctor' }}
                                </button>
                            </form>
                            <div class="text-center mt-3">
                                <router-link to="/login">Other Login Options</router-link>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

const PatientLoginPage = {
    data() {
        return {
            username: '',
            password: '',
            remember: false,
            loading: false
        };
    },
    computed: {
        app() {
            return window.appInstance;
        }
    },
    methods: {
        async handleLogin() {
            this.loading = true;
            try {
                await window.appInstance.login(this.username, this.password, 'Patient');
            } catch (error) {
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-5">
                    <div class="card shadow border-info">
                        <div class="card-body p-5">
                            <h2 class="text-center mb-4 text-info">Patient Login</h2>
                            <div v-if="app.error" class="alert alert-danger">{{ app.error }}</div>
                            <form @submit.prevent="handleLogin">
                                <div class="mb-3">
                                    <label class="form-label">Username</label>
                                    <input v-model="username" type="text" class="form-control" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Password</label>
                                    <input v-model="password" type="password" class="form-control" required>
                                </div>
                                <div class="mb-3 form-check">
                                    <input v-model="remember" type="checkbox" class="form-check-input" id="remember">
                                    <label class="form-check-label" for="remember">Remember me</label>
                                </div>
                                <button type="submit" class="btn btn-info w-100" :disabled="loading">
                                    {{ loading ? 'Logging in...' : 'Login as Patient' }}
                                </button>
                            </form>
                            <div class="text-center mt-3">
                                <router-link to="/register">Don't have an account? Register</router-link>
                                <span class="mx-2">|</span>
                                <router-link to="/login">Other Login Options</router-link>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

const RegisterPage = {
    data() {
        return {
            form: {
                username: '',
                password: '',
                email: '',
                first_name: '',
                last_name: '',
                phone: '',
                date_of_birth: '',
                address: '',
                emergency_contact_name: '',
                emergency_contact_phone: ''
            },
            loading: false
        };
    },
    methods: {
        async handleRegister() {
            this.loading = true;
            try {
                const result = await authAPI.register(this.form);
                window.appInstance.user = result.user;
                window.appInstance.showSuccess('Registration successful');
                this.$router.push(result.redirect);
            } catch (error) {
                window.appInstance.showError(error.error || 'Registration failed');
            } finally {
                this.loading = false;
            }
        }
    },
    template: `
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card shadow">
                        <div class="card-body p-5">
                            <h2 class="text-center mb-4">Patient Registration</h2>
                            <div v-if="app.error" class="alert alert-danger">{{ app.error }}</div>
                            <form @submit.prevent="handleRegister">
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
                                <div class="mb-3">
                                    <label class="form-label">Username *</label>
                                    <input v-model="form.username" type="text" class="form-control" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Email *</label>
                                    <input v-model="form.email" type="email" class="form-control" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Password *</label>
                                    <input v-model="form.password" type="password" class="form-control" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Phone *</label>
                                    <input v-model="form.phone" type="tel" class="form-control" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Date of Birth</label>
                                    <input v-model="form.date_of_birth" type="date" class="form-control">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Address</label>
                                    <textarea v-model="form.address" class="form-control" rows="2"></textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Emergency Contact Name</label>
                                    <input v-model="form.emergency_contact_name" type="text" class="form-control">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Emergency Contact Phone</label>
                                    <input v-model="form.emergency_contact_phone" type="tel" class="form-control">
                                </div>
                                <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                                    {{ loading ? 'Registering...' : 'Register' }}
                                </button>
                            </form>
                            <div class="text-center mt-3">
                                <router-link to="/login">Already have an account? Login</router-link>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

window.HomePage = HomePage;
window.LoginPage = LoginPage;
window.AdminLoginPage = AdminLoginPage;
window.DoctorLoginPage = DoctorLoginPage;
window.PatientLoginPage = PatientLoginPage;
window.RegisterPage = RegisterPage;

