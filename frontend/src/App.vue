<template>
    <div class="app">
        <Toast v-for="(toast, i) in toasts" :key="i" :type="toast.type" :message="toast.message" />
        
        <div v-if="!user" class="auth-container">
            <div v-if="!authStep" class="role-selection">
                <div class="logo">LMS</div>
                <h1>Choose your role</h1>
                <div class="role-buttons">
                    <button class="btn btn-primary role-btn" @click="selectRole('admin')">
                        <span class="role-icon">👨‍💼</span>
                        Administrator
                    </button>
                    <button class="btn btn-secondary role-btn" @click="selectRole('student')">
                        <span class="role-icon">👨‍🎓</span>
                        Student
                    </button>
                </div>
            </div>
            
            <AdminLogin v-else-if="authStep === 'admin'" @login="handleAdminLogin" @back="authStep = null" />
            <StudentLogin v-else-if="authStep === 'student'" @login="handleStudentLogin" @back="authStep = null" />
        </div>
        
        <div v-else class="main-container">
            <AdminDashboard v-if="user.role === 'admin'" :token="token" @logout="logout" />
            <StudentDashboard v-else :token="token" @logout="logout" />
        </div>
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from './services/api'
import AdminLogin from './views/AdminLogin.vue'
import StudentLogin from './views/StudentLogin.vue'
import AdminDashboard from './views/AdminDashboard.vue'
import StudentDashboard from './views/StudentDashboard.vue'
import Toast from './components/Toast.vue'

export default {
    name: 'App',
    components: {
        AdminLogin,
        StudentLogin,
        AdminDashboard,
        StudentDashboard,
        Toast
    },
    setup() {
        const user = ref(null)
        const token = ref(null)
        const authStep = ref(null)
        const toasts = ref([])
        
        onMounted(() => {
            // Check if token exists in localStorage
            const savedToken = localStorage.getItem('token')
            if (savedToken) {
                verifyToken(savedToken)
            }
        })
        
        const verifyToken = async (tokenToVerify) => {
            try {
                const response = await api.verifyToken()
                user.value = response.data.user
                token.value = tokenToVerify
            } catch (error) {
                localStorage.removeItem('token')
            }
        }
        
        const handleAdminLogin = async (username, password) => {
            try {
                const response = await api.adminLogin(username, password)
                token.value = response.data.access_token
                user.value = { role: response.data.role }
                localStorage.setItem('token', token.value)
                authStep.value = null
                showToast('Logged in successfully!', 'success')
            } catch (error) {
                showToast('Login failed: Invalid credentials', 'error')
            }
        }
        
        const handleStudentLogin = async (student_name, student_urn) => {
            try {
                const response = await api.studentLogin(student_name, student_urn)
                token.value = response.data.access_token
                user.value = { role: response.data.role, student_name, student_urn }
                localStorage.setItem('token', token.value)
                authStep.value = null
                showToast('Logged in successfully!', 'success')
            } catch (error) {
                showToast('Login failed: Please check your details', 'error')
            }
        }
        
        const logout = () => {
            user.value = null
            token.value = null
            authStep.value = null
            localStorage.removeItem('token')
            showToast('Logged out', 'success')
        }
        
        const selectRole = (role) => {
            authStep.value = role
        }
        
        const showToast = (message, type = 'info') => {
            const id = Date.now()
            toasts.value.push({ id, message, type })
            setTimeout(() => {
                toasts.value = toasts.value.filter(t => t.id !== id)
            }, 3000)
        }
        
        return {
            user,
            token,
            authStep,
            toasts,
            handleAdminLogin,
            handleStudentLogin,
            logout,
            selectRole
        }
    }
}
</script>

<style scoped>
.app {
    min-height: 100vh;
    background: var(--bg-primary);
}

.auth-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
}

.role-selection {
    text-align: center;
    max-width: 400px;
    width: 100%;
}

.logo {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent-color), var(--accent-hover));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 2rem;
    letter-spacing: 2px;
}

.role-selection h1 {
    font-size: 2rem;
    margin-bottom: 3rem;
    color: var(--text-primary);
}

.role-buttons {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.role-btn {
    padding: 1.5rem;
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.role-icon {
    font-size: 1.5rem;
}

.main-container {
    min-height: 100vh;
}
</style>
