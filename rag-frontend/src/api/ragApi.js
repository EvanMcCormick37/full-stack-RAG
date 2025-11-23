import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {'Content-Type': 'application/json'}
});

export const ragApi = {
    healthCheck: () => apiClient.get('/health'),

    uploadDocument: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post(
            '/api/v1/documents/',
            formData,
            {
                headers: {'Content-Type': 'multipart/form-data'}
            }
        );
    },

    listDocuments: () => apiClient.get('/api/v1/documents/'),

    getDocument: (documentId) => apiClient.get(`/api/v1/documents/${documentId}`),

    deleteAllDocuments: (confirmed=true) => apiClient.delete('/api/v1/documents/',
        params={confirm: confirmed}
    ),

    deleteDocument: (documentId) => apiClient.delete(`/api/v1/documents/${documentId}`),

    query: (queryRequest) => apiClient.post('/api/v1/query/', queryRequest)
};