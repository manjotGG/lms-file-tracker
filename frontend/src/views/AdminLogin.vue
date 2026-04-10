<template>
    <div class="login-container">
        <div class="login-card">
            <button class="back-btn" @click="$emit('back')">← Back</button>
            
            <h2>Admin Login</h2>
            
            <form @submit.prevent="handleLogin">
                <div class="form-group">
                    <label>Username</label>
                    <input 
                        v-model="username" 
                        type="text" 
                        placeholder="Enter username"
                        required
                    >
                </div>
                
                <div class="form-group">
                    <label>Password</label>
                    <input 
                        v-model="password" 
                        type="password" 
                        placeholder="Enter password"
                        required
                    >
                </div>
                
                <button 
                    type="submit" 
                    class="btn btn-primary"
                    :disabled="loading"
                >
                    {{ loading ? 'Logging in...' : 'Login' }}
                </button>
            </form>
        </div>
    </div>
</template>

<script>
import { ref } from 'vue'

export default {
    name: 'AdminLogin',
    emits: ['login', 'back'],
    setup(props, { emit }) {
        const username = ref('')
        const password = ref('')
        const loading = ref(false)
        
        const handleLogin = async () => {
            loading.value = true
            try {
                emit('login', username.value, password.value)
            } finally {
                loading.value = false
            }
        }
        
        return {
            username,
            password,
            loading,
            handleLogin
        }
    }
}
</script>

<style scoped>
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 2rem;
}

.login-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 1rem;
    padding: 2.5rem;
    width: 100%;
    max-width: 400px;
    position: relative;
}

.back-btn {
    position: absolute;
    top: 1.5rem;
    left: 1.5rem;
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 1rem;
    transition: color 0.3s ease;
}

.back-btn:hover {
    color: var(--text-primary);
}

h2 {
    font-size: 1.75rem;
    margin-bottom: 2rem;
    text-align: center;
}

.form-group {
    margin-bottom: 1.5rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text-secondary);
}

input {
    width: 100%;
}

.btn {
    width: 100%;
    margin-top: 1rem;
}
</style>
