import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Add token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

export default {
    // Auth endpoints
    adminLogin: (username, password) => 
        api.post('/auth/admin/login', { username, password }),
    
    studentLogin: (student_name, student_urn) => 
        api.post('/auth/student/login', { student_name, student_urn }),
    
    verifyToken: () => 
        api.get('/auth/verify'),
    
    // Student endpoints
    uploadFile: (file, comment) => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('comment', comment)
        return api.post('/files/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
    },
    
    getMyFiles: () => 
        api.get('/files/my'),
    
    downloadLatest: (filename) => 
        api.get('/files/my/latest', { 
            params: { filename },
            responseType: 'blob'
        }),
    
    // Admin endpoints
    searchStudents: (student_name, student_urn) => 
        api.get('/files/admin/search', {
            params: { student_name, student_urn }
        }),
    
    getStudentFiles: (student_urn, sort = 'latest') => 
        api.get('/files/admin/files', {
            params: { student_urn, sort }
        }),
    
    adminDownload: (student_urn, filename) => 
        api.get('/files/admin/download', {
            params: { student_urn, filename },
            responseType: 'blob'
        }),
    
    getRecentUploads: () => 
        api.get('/files/admin/recent')
}
