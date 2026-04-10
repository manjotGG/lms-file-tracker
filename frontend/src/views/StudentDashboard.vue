<template>
    <div class="student-dashboard">
        <nav class="navbar">
            <div class="nav-content">
                <div class="logo">📚 LMS Student</div>
                <button class="btn btn-secondary btn-sm" @click="$emit('logout')">Logout</button>
            </div>
        </nav>
        
        <div class="container">
            <div class="upload-section">
                <h2>Upload New File</h2>
                <div class="upload-card">
                    <div class="file-input-wrapper">
                        <input 
                            ref="fileInput"
                            type="file" 
                            @change="handleFileSelect"
                            style="display: none"
                        >
                        <button 
                            type="button"
                            class="btn btn-primary"
                            @click="$refs.fileInput.click()"
                            :disabled="uploading"
                        >
                            📁 Choose File
                        </button>
                    </div>
                    
                    <div v-if="selectedFile" class="file-info">
                        <p>{{ selectedFile.name }}</p>
                        <input 
                            v-model="comment" 
                            type="text" 
                            placeholder="Add a comment (optional)"
                        >
                        <button 
                            class="btn btn-primary"
                            @click="uploadFile"
                            :disabled="uploading"
                        >
                            {{ uploading ? 'Uploading...' : 'Upload' }}
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="files-section">
                <h2>Your Files</h2>
                
                <div v-if="loading" class="loading">
                    <div class="spinner"></div>
                    <p>Loading files...</p>
                </div>
                
                <div v-else-if="files.length === 0" class="empty">
                    <p>No files uploaded yet</p>
                </div>
                
                <div v-else class="files-list">
                    <div 
                        v-for="file in files" 
                        :key="file.filename"
                        class="file-item"
                    >
                        <div class="file-header">
                            <h3>{{ file.filename }}</h3>
                            <span class="version-badge">{{ file.versions.length }} version(s)</span>
                        </div>
                        
                        <div class="versions">
                            <div 
                                v-for="(version, idx) in file.versions.slice().reverse()" 
                                :key="idx"
                                class="version-item"
                            >
                                <div class="version-info">
                                    <span class="version-number">v{{ version.version }}</span>
                                    <span class="upload-date">{{ formatDate(version.uploaded_at) }}</span>
                                    <p v-if="version.comment" class="comment">{{ version.comment }}</p>
                                </div>
                                <button 
                                    v-if="idx === 0"
                                    class="btn btn-sm btn-primary"
                                    @click="downloadFile(file.filename)"
                                    :disabled="downloading"
                                >
                                    ⬇ Download
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '../services/api'

export default {
    name: 'StudentDashboard',
    props: {
        token: String
    },
    emits: ['logout'],
    setup() {
        const files = ref([])
        const loading = ref(true)
        const uploading = ref(false)
        const downloading = ref(false)
        const selectedFile = ref(null)
        const comment = ref('')
        const fileInput = ref(null)
        
        onMounted(() => {
            loadFiles()
        })
        
        const loadFiles = async () => {
            loading.value = true
            try {
                const response = await api.getMyFiles()
                files.value = response.data.files || []
            } catch (error) {
                console.error('Failed to load files', error)
            } finally {
                loading.value = false
            }
        }
        
        const handleFileSelect = (event) => {
            selectedFile.value = event.target.files[0]
        }
        
        const uploadFile = async () => {
            if (!selectedFile.value) return
            
            uploading.value = true
            try {
                await api.uploadFile(selectedFile.value, comment.value)
                selectedFile.value = null
                comment.value = ''
                await loadFiles()
            } catch (error) {
                console.error('Upload failed', error)
            } finally {
                uploading.value = false
            }
        }
        
        const downloadFile = async (filename) => {
            downloading.value = true
            try {
                const blob = await api.downloadLatest(filename)
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = filename
                a.click()
                URL.revokeObjectURL(url)
            } catch (error) {
                console.error('Download failed', error)
            } finally {
                downloading.value = false
            }
        }
        
        const formatDate = (dateString) => {
            if (!dateString) return ''
            const date = new Date(dateString)
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
        
        return {
            files,
            loading,
            uploading,
            downloading,
            selectedFile,
            comment,
            fileInput,
            handleFileSelect,
            uploadFile,
            downloadFile,
            formatDate
        }
    }
}
</script>

<style scoped>
.student-dashboard {
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
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem;
}

.upload-section, .files-section {
    margin-bottom: 3rem;
}

h2 {
    margin-bottom: 1.5rem;
    font-size: 1.5rem;
}

.upload-card {
    background: var(--bg-secondary);
    border: 2px dashed var(--border-color);
    border-radius: 0.75rem;
    padding: 2rem;
    text-align: center;
    transition: all 0.3s ease;
}

.upload-card:hover {
    border-color: var(--accent-color);
}

.file-input-wrapper {
    margin-bottom: 1rem;
}

.file-info {
    margin-top: 1.5rem;
    text-align: left;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.file-info p {
    background: var(--bg-tertiary);
    padding: 0.75rem;
    border-radius: 0.5rem;
    word-break: break-all;
}

.file-info input {
    width: 100%;
}

.file-info .btn {
    width: 100%;
}

.loading, .empty {
    text-align: center;
    padding: 2rem 0;
}

.files-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.file-item {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.75rem;
    overflow: hidden;
}

.file-header {
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.file-header h3 {
    margin: 0;
    word-break: break-word;
}

.version-badge {
    background: var(--accent-color);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 2rem;
    font-size: 0.8rem;
    white-space: nowrap;
}

.versions {
    padding: 1.5rem;
}

.version-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 1rem;
    background: var(--bg-tertiary);
    border-radius: 0.5rem;
    margin-bottom: 0.75rem;
}

.version-item:last-child {
    margin-bottom: 0;
}

.version-info {
    flex: 1;
}

.version-number {
    display: inline-block;
    background: var(--accent-color);
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.85rem;
    font-weight: 600;
    margin-right: 0.75rem;
}

.upload-date {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.comment {
    margin-top: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.btn {
    white-space: nowrap;
}
</style>
