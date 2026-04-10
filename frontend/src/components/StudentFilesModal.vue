<template>
    <div class="modal-overlay" @click.self="$emit('close')">
        <div class="modal">
            <div class="modal-header">
                <div>
                    <h3>{{ student.student_name }}</h3>
                    <p class="urn">{{ student.student_urn }}</p>
                </div>
                <button class="close-btn" @click="$emit('close')">✕</button>
            </div>
            
            <div class="modal-content">
                <div v-if="loading" class="loading">
                    <div class="spinner"></div>
                </div>
                
                <div v-else-if="files.length === 0" class="empty">
                    <p>No files found</p>
                </div>
                
                <div v-else class="files-list">
                    <div 
                        v-for="file in files" 
                        :key="file.filename"
                        class="file-item"
                    >
                        <div class="file-info">
                            <h4>{{ file.filename }}</h4>
                            <p class="version-count">{{ file.versions.length }} version(s)</p>
                        </div>
                        
                        <button 
                            class="btn btn-primary btn-sm"
                            @click="downloadFile(file.filename)"
                            :disabled="downloading"
                        >
                            ⬇ Download Latest
                        </button>
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
        
        onMounted(() => {
            loadFiles()
        })
        
        const loadFiles = async () => {
            loading.value = true
            try {
                const response = await api.getStudentFiles(props.student.student_urn)
                files.value = response.data.files || []
            } catch (error) {
                console.error('Failed to load files', error)
            } finally {
                loading.value = false
            }
        }
        
        const downloadFile = (filename) => {
            emit('download', props.student.student_urn, filename)
        }
        
        return {
            files,
            loading,
            downloading,
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
    background: rgba(0, 0, 0, 0.8);
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
    border-radius: 1rem;
    width: 90%;
    max-width: 600px;
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
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.modal-header h3 {
    margin: 0;
    margin-bottom: 0.5rem;
    text-transform: capitalize;
}

.urn {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0;
    font-family: monospace;
}

.close-btn {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    transition: color 0.3s ease;
}

.close-btn:hover {
    color: var(--text-primary);
}

.modal-content {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
}

.loading, .empty {
    text-align: center;
    padding: 2rem 0;
}

.files-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.file-item {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
}

.file-info {
    flex: 1;
}

.file-info h4 {
    margin: 0;
    margin-bottom: 0.25rem;
    word-break: break-word;
}

.version-count {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.btn {
    white-space: nowrap;
}
</style>
