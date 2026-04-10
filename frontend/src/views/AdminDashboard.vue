<template>
    <div class="admin-dashboard">
        <nav class="navbar">
            <div class="nav-content">
                <div class="logo">📚 LMS Admin</div>
                <button class="btn btn-secondary btn-sm" @click="$emit('logout')">Logout</button>
            </div>
        </nav>
        
        <div class="container">
            <div class="search-section">
                <h2>Search Students</h2>
                <div class="search-inputs">
                    <input 
                        v-model="searchName" 
                        type="text" 
                        placeholder="Search by name (e.g., john)"
                        @input="debouncedSearch"
                    >
                    <input 
                        v-model="searchUrn" 
                        type="text" 
                        placeholder="Search by URN (e.g., S12345)"
                        @input="debouncedSearch"
                    >
                </div>
            </div>
            
            <div v-if="loading" class="loading">
                <div class="spinner"></div>
                <p>Loading...</p>
            </div>
            
            <div v-else-if="students.length === 0 && searched" class="empty">
                <p>No students found</p>
            </div>
            
            <div v-else class="students-grid">
                <div 
                    v-for="student in students" 
                    :key="student.student_urn"
                    class="student-card"
                    @click="selectStudent(student)"
                >
                    <div class="student-info">
                        <h3>{{ student.student_name }}</h3>
                        <p class="urn">{{ student.student_urn }}</p>
                        <p class="file-count">{{ student.file_count }} file(s)</p>
                    </div>
                </div>
            </div>
        </div>
        
        <StudentFilesModal 
            v-if="selectedStudent"
            :student="selectedStudent"
            :token="token"
            @close="selectedStudent = null"
            @download="handleDownload"
        />
    </div>
</template>

<script>
import { ref } from 'vue'
import api from '../services/api'
import StudentFilesModal from '../components/StudentFilesModal.vue'

export default {
    name: 'AdminDashboard',
    components: {
        StudentFilesModal
    },
    props: {
        token: String
    },
    emits: ['logout'],
    setup() {
        const searchName = ref('')
        const searchUrn = ref('')
        const students = ref([])
        const loading = ref(false)
        const searched = ref(false)
        const selectedStudent = ref(null)
        let searchTimeout
        
        const performSearch = async () => {
            if (!searchName.value && !searchUrn.value) {
                students.value = []
                searched.value = false
                return
            }
            
            loading.value = true
            try {
                const response = await api.searchStudents(
                    searchName.value || null,
                    searchUrn.value || null
                )
                students.value = response.data.students || []
                searched.value = true
            } catch (error) {
                students.value = []
                searched.value = true
            } finally {
                loading.value = false
            }
        }
        
        const debouncedSearch = () => {
            clearTimeout(searchTimeout)
            searchTimeout = setTimeout(performSearch, 300)
        }
        
        const selectStudent = (student) => {
            selectedStudent.value = student
        }
        
        const handleDownload = async (student_urn, filename) => {
            try {
                const blob = await api.adminDownload(student_urn, filename)
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = filename
                a.click()
                URL.revokeObjectURL(url)
            } catch (error) {
                console.error('Download failed', error)
            }
        }
        
        return {
            searchName,
            searchUrn,
            students,
            loading,
            searched,
            selectedStudent,
            debouncedSearch,
            selectStudent,
            handleDownload
        }
    }
}
</script>

<style scoped>
.admin-dashboard {
    min-height: 100vh;
}

.navbar {
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    padding: 1.5rem 0;
    sticky: 0;
    top: 0;
    z-index: 100;
}

.nav-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: 700;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.search-section {
    margin-bottom: 3rem;
}

.search-section h2 {
    margin-bottom: 1.5rem;
    font-size: 1.5rem;
}

.search-inputs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}

@media (max-width: 768px) {
    .search-inputs {
        grid-template-columns: 1fr;
    }
}

.loading, .empty {
    text-align: center;
    padding: 3rem 0;
}

.students-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
}

.student-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.75rem;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
}

.student-card:hover {
    border-color: var(--accent-color);
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.1);
    transform: translateY(-2px);
}

.student-info h3 {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    text-transform: capitalize;
}

.urn {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
    font-family: monospace;
}

.file-count {
    color: var(--accent-color);
    font-weight: 600;
}
</style>
