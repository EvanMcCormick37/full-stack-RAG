import axios from 'axios';

const API_BASE_URL = ''; //Replace with VITE_BASE_URL for dev mode
const API_KEY = import.meta.env.VITE_API_KEY;

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
        'API-Key': API_KEY
    }
});

export const ragApi = {
    healthCheck: () => apiClient.get('/health'),

    uploadDocument: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post(
            '/api/v1.1/documents/',
            formData,
            {
                headers: {'Content-Type': 'multipart/form-data'}
            }
        );
    },

    listDocuments: () => apiClient.get('/api/v1.1/documents'),

    getDocument: (documentId) => apiClient.get(`/api/v1.1/documents/${documentId}`),

    deleteAllDocuments: (confirmed=true) => apiClient.delete('/api/v1.1/documents',
        {params: {confirm: confirmed}}
    ),

    deleteDocument: (documentId) => apiClient.delete(`$/api/v1.1/documents/${documentId}`),

    query: (queryRequest) => apiClient.post('/api/v1.1/query', queryRequest)
};