<template>
    <div class="app">
        <Toast v-for="(toast, i) in toasts" :key="i" :type="toast.type" :message="toast.message" />
        
        <div v-if="!user" class="auth-container">
            <div v-if="!authStep" class="role-selection">
                <div class="backdrop"></div>
                <div class="content">
                    <div class="logo">VC LMS</div>
                    <h1>Select your Role</h1>
                    <p class="subtitle">Access the Version Control Learning Management System</p>
                    
                    <div class="role-buttons">
                        <button class="role-card" @click="selectRole('admin')">
                            <div class="role-title">Administrator</div>
                            <div class="role-description">Full system access and control</div>
                        </button>
                        <button class="role-card" @click="selectRole('student')">
                            <div class="role-title">Student</div>
                            <div class="role-description">View and manage submissions</div>
                        </button>
                    </div>
                </div>
            </div>
            
            <AdminLogin v-else-if="authStep === 'admin'" @login="handleAdminLogin" @back="authStep = null" />
            <StudentLogin v-else-if="authStep === 'student'" @login="handleStudentLogin" @back="authStep = null" />
        </div>
        
        <div v-else class="main-container">
            <AdminDashboard v-if="user.role === 'admin'" :token="token" @logout="logout" />
            <StudentDashboard v-else-if="user.role === 'student'" :token="token" @logout="logout" />
        </div>
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from './services/api'
import AdminLogin from './views/AdminLogin.vue'
import AdminDashboard from './views/AdminDashboard.vue'
import StudentLogin from './views/StudentLogin.vue'
import StudentDashboard from './views/StudentDashboard.vue'
import Toast from './components/Toast.vue'

export default {
    name: 'App',
    components: {
        AdminLogin,
        AdminDashboard,
        StudentLogin,
        StudentDashboard,
        Toast
    },
    setup() {
        const user = ref(null)
        const token = ref(null)
        const authStep = ref(null)
        const toasts = ref([])
        
        onMounted(() => {
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
                showToast('Logged in successfully', 'success')
            } catch (error) {
                showToast('Login failed: Invalid credentials', 'error')
            }
        }

        const handleStudentLogin = async (studentName, studentUrn) => {
            try {
                const response = await api.studentLogin(studentName, studentUrn)
                token.value = response.data.access_token
                user.value = { role: 'student', studentId: studentName, studentUrn }
                localStorage.setItem('token', token.value)
                authStep.value = null
                showToast('Logged in successfully', 'success')
            } catch (error) {
                showToast('Login failed: Invalid student name or URN', 'error')
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
    position: relative;
    background: var(--bg-primary);
}

.backdrop {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
}

.role-selection {
    text-align: center;
    max-width: 900px;
    width: 100%;
    position: relative;
    z-index: 1;
}

.content {
    padding: 2rem;
}

.logo {
    font-size: 3.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1.5rem;
    letter-spacing: 2px;
}

.role-selection h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
    font-weight: 700;
}

.subtitle {
    color: var(--text-secondary);
    font-size: 1rem;
    margin-bottom: 3rem;
}

.role-buttons {
    display: flex;
    gap: 2rem;
    justify-content: center;
    flex-wrap: wrap;
}

.role-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 2rem;
    cursor: pointer;
    transition: border-color 0.3s ease;
    flex: 1;
    min-width: 280px;
    max-width: 350px;
}

.role-card:hover {
    border-color: var(--accent-color);
}

.role-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.75rem;
}

.role-description {
    font-size: 0.95rem;
    color: var(--text-secondary);
}

.main-container {
    min-height: 100vh;
    background: var(--bg-primary);
}
</style>
