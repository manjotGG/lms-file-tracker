<template>
    <div class="modal-overlay" @click.self="$emit('close')">
        <div class="modal">
            <div class="modal-header">
                <div>
                    <h3>{{ student.student_name }}</h3>
                    <p class="urn">{{ student.student_urn }}</p>
                </div>
                <button class="close-btn" @click="$emit('close')">Close</button>
            </div>
            
            <div class="modal-content">
                <div v-if="loading" class="loading">
                    <div class="spinner"></div>
                </div>
                
                <div v-else-if="files.length === 0" class="empty">
                    <p>No files found</p>
                </div>
                
                <div v-else>
                    <div class="sort-section">
                        <label for="sort-dropdown">Sort by Upload Time:</label>
                        <select 
                            id="sort-dropdown"
                            v-model="sortOrder" 
                            class="sort-dropdown"
                        >
                            <option value="latest">Latest First</option>
                            <option value="oldest">Oldest First</option>
                        </select>
                    </div>
                    
                    <div class="files-list">
                        <div 
                            v-for="file in sortedFiles" 
                            :key="file.filename"
                            class="file-item"
                        >
                            <div class="file-info">
                                <h4>{{ file.filename }}</h4>
                                <p class="version-count">{{ file.versions.length }} version(s)</p>
                                <p class="upload-time">{{ formatUploadTime(file.latest_upload) }}</p>
                            </div>
                            
                            <button 
                                class="btn btn-primary btn-sm"
                                @click="downloadFile(file.filename)"
                                :disabled="downloading"
                            >
                                Download Latest
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import api from '../services/api'

export default {
    name: 'StudentFilesModal',
    props: {
        student: Object,
        token: String
    },
    emits: ['close', 'download'],
    setup(props, { emit }) {
        const files = ref([])
        const loading = ref(true)
        const downloading = ref(false)
        const sortOrder = ref('latest')
        
        onMounted(() => {
            loadFiles()
        })
        
        const loadFiles = async () => {
            loading.value = true
            try {
                const response = await api.getStudentFiles(props.student.student_urn)
                files.value = response.data.files || []
                // Add latest_upload field for each file
                files.value.forEach(file => {
                    if (file.versions && file.versions.length > 0) {
                        file.latest_upload = file.versions[0].uploaded_at
                    }
                })
            } catch (error) {
                console.error('Failed to load files', error)
            } finally {
                loading.value = false
            }
        }
        
        const sortedFiles = computed(() => {
            let sorted = [...files.value]
            
            if (sortOrder.value === 'latest') {
                // Latest First - Descending order
                sorted.sort((a, b) => {
                    const dateA = a.latest_upload ? new Date(a.latest_upload) : new Date(0)
                    const dateB = b.latest_upload ? new Date(b.latest_upload) : new Date(0)
                    return dateB - dateA
                })
            } else {
                // Oldest First - Ascending order
                sorted.sort((a, b) => {
                    const dateA = a.latest_upload ? new Date(a.latest_upload) : new Date(0)
                    const dateB = b.latest_upload ? new Date(b.latest_upload) : new Date(0)
                    return dateA - dateB
                })
            }
            
            return sorted
        })
        
        const formatUploadTime = (dateString) => {
            if (!dateString) return ''
            const date = new Date(dateString)
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
        
        const downloadFile = (filename) => {
            emit('download', props.student.student_urn, filename)
        }
        
        return {
            files,
            loading,
            downloading,
            sortOrder,
            sortedFiles,
            formatUploadTime,
            downloadFile
        }
    }
}
</script>

<style scoped>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

.modal {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    width: 90%;
    max-width: 650px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    animation: slideUp 0.3s ease;
}

@keyframes slideUp {
    from {
        transform: translateY(30px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

.modal-header {
    padding: 2rem;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.modal-header h3 {
    margin: 0;
    margin-bottom: 0.5rem;
    text-transform: capitalize;
    color: var(--text-primary);
    font-weight: 700;
    font-size: 1.3rem;
}

.urn {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0;
    font-family: monospace;
}

.close-btn {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    font-size: 0.9rem;
    cursor: pointer;
    padding: 0.5rem 1rem;
    border-radius: 0.4rem;
    transition: border-color 0.2s ease;
    font-weight: 600;
}

.close-btn:hover {
    border-color: var(--accent-color);
}

.modal-content {
    flex: 1;
    overflow-y: auto;
    padding: 2rem;
}

.sort-section {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border-color);
}

.sort-section label {
    color: var(--text-primary);
    font-weight: 600;
    font-size: 0.95rem;
    white-space: nowrap;
}

.sort-dropdown {
    padding: 0.5rem 1rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 0.4rem;
    color: var(--text-primary);
    font-size: 0.9rem;
    cursor: pointer;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    font-weight: 500;
}

.sort-dropdown:hover {
    border-color: var(--accent-color);
}

.sort-dropdown:focus {
    outline: none;
    border-color: var(--accent-color);
    box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.1);
}

.loading, .empty {
    text-align: center;
    padding: 2rem 0;
    color: var(--text-secondary);
}

.files-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.file-item {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 0.4rem;
    padding: 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    transition: border-color 0.2s ease;
}

.file-item:hover {
    border-color: var(--accent-color);
}

.file-info {
    flex: 1;
}

.file-info h4 {
    margin: 0;
    margin-bottom: 0.25rem;
    word-break: break-word;
    color: var(--text-primary);
    font-weight: 700;
}

.version-count {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.upload-time {
    margin: 0.25rem 0 0 0;
    color: var(--text-secondary);
    font-size: 0.85rem;
}

.btn {
    white-space: nowrap;
}
</style>

