const { createApp } = Vue;
const { createRouter, createWebHistory } = VueRouter;

const routes = [
    { path: '/', name: 'Home', component: 'HomePage' },
    { path: '/login', name: 'Login', component: 'LoginPage' },
    { path: '/login/admin', name: 'AdminLogin', component: 'AdminLoginPage' },
    { path: '/login/doctor', name: 'DoctorLogin', component: 'DoctorLoginPage' },
    { path: '/login/patient', name: 'PatientLogin', component: 'PatientLoginPage' },
    { path: '/register', name: 'Register', component: 'RegisterPage' },
    { path: '/admin/dashboard', name: 'AdminDashboard', component: 'AdminDashboard', meta: { requiresAuth: true, role: 'Admin' } },
    { path: '/admin/doctors', name: 'AdminDoctors', component: 'AdminDoctors', meta: { requiresAuth: true, role: 'Admin' } },
    { path: '/admin/doctors/add', name: 'AdminAddDoctor', component: 'AdminAddDoctor', meta: { requiresAuth: true, role: 'Admin' } },
    { path: '/admin/doctors/edit/:id', name: 'AdminEditDoctor', component: 'AdminEditDoctor', meta: { requiresAuth: true, role: 'Admin' } },
    { path: '/admin/patients', name: 'AdminPatients', component: 'AdminPatients', meta: { requiresAuth: true, role: 'Admin' } },
    { path: '/admin/appointments', name: 'AdminAppointments', component: 'AdminAppointments', meta: { requiresAuth: true, role: 'Admin' } },
    { path: '/doctor/dashboard', name: 'DoctorDashboard', component: 'DoctorDashboard', meta: { requiresAuth: true, role: 'Doctor' } },
    { path: '/doctor/appointments', name: 'DoctorAppointments', component: 'DoctorAppointments', meta: { requiresAuth: true, role: 'Doctor' } },
    { path: '/doctor/availability', name: 'DoctorAvailability', component: 'DoctorAvailability', meta: { requiresAuth: true, role: 'Doctor' } },
    { path: '/patient/dashboard', name: 'PatientDashboard', component: 'PatientDashboard', meta: { requiresAuth: true, role: 'Patient' } },
    { path: '/patient/doctors', name: 'PatientDoctors', component: 'PatientDoctors', meta: { requiresAuth: true, role: 'Patient' } },
    { path: '/patient/book/:id', name: 'PatientBookAppointment', component: 'PatientBookAppointment', meta: { requiresAuth: true, role: 'Patient' } },
    { path: '/patient/appointments', name: 'PatientAppointments', component: 'PatientAppointments', meta: { requiresAuth: true, role: 'Patient' } },
    { path: '/patient/appointments/:id', name: 'PatientAppointmentDetail', component: 'PatientAppointmentDetail', meta: { requiresAuth: true, role: 'Patient' } },
    { path: '/patient/appointments/reschedule/:id', name: 'PatientRescheduleAppointment', component: 'PatientRescheduleAppointment', meta: { requiresAuth: true, role: 'Patient' } },
    { path: '/patient/history', name: 'PatientHistory', component: 'PatientHistory', meta: { requiresAuth: true, role: 'Patient' } },
    { path: '/admin/patients/:id/history', name: 'AdminPatientHistory', component: 'AdminPatientHistory', meta: { requiresAuth: true, role: 'Admin' } },
    { path: '/doctor/appointments/:id', name: 'DoctorAppointmentDetail', component: 'DoctorAppointmentDetail', meta: { requiresAuth: true, role: 'Doctor' } }
];

const router = createRouter({
    history: createWebHistory(),
    routes: routes.map(route => ({
        path: route.path,
        name: route.name,
        meta: route.meta,
        component: window[route.component] || { template: '<div>Component not found: ' + route.component + '</div>' }
    }))
});

router.beforeEach(async (to, from, next) => {
    if (to.meta.requiresAuth) {
        try {
            const user = await authAPI.getCurrentUser();
            if (!user) {
                next('/');
                return;
            }
            if (to.meta.role && user.role !== to.meta.role) {
                const dashboardRoute = {
                    'Admin': '/admin/dashboard',
                    'Doctor': '/doctor/dashboard',
                    'Patient': '/patient/dashboard'
                }[user.role] || '/';
                next(dashboardRoute);
                return;
            }
        } catch (error) {
            next('/');
            return;
        }
    }
    next();
});

const app = createApp({
    data() {
        return {
            user: null,
            loading: false,
            error: null,
            success: null
        };
    },
    async mounted() {
        await this.checkAuth();
    },
    methods: {
        async checkAuth() {
            try {
                this.user = await authAPI.getCurrentUser();
            } catch (error) {
                this.user = null;
            }
        },
        async login(username, password, role) {
            try {
                const result = await authAPI.login(username, password, role);
                this.user = result.user;
                this.showSuccess('Login successful');
                this.$router.push(result.redirect);
            } catch (error) {
                this.showError(error.error || 'Login failed');
                throw error;
            }
        },
        async logout() {
            try {
                await authAPI.logout();
                this.user = null;
                this.$router.push('/');
            } catch (error) {
                this.showError('Logout failed');
            }
        },
        showError(message) {
            this.error = message;
            setTimeout(() => this.error = null, 5000);
        },
        showSuccess(message) {
            this.success = message;
            setTimeout(() => this.success = null, 5000);
        }
    },
    provide() {
        return {
            app: this
        };
    }
});

app.use(router);

app.mixin({
    computed: {
        app() {
            return window.appInstance || this.$root;
        }
    }
});

const vm = app.mount('#app');
window.appInstance = vm;
