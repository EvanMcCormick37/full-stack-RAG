import axios from 'axios';
import { sessionId } from '../utils/session'

const API_BASE_URL = import.meta.env.VITE_BASE_URL || '';
const API_KEY = import.meta.env.VITE_API_KEY;

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
        'API-Key': API_KEY,
        'Session-ID': sessionId()
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

    listDocuments: () => apiClient.get('/api/v1.1/documents/'),

    getDocument: (documentId) => apiClient.get(`/api/v1.1/documents/${documentId}`),

    deleteAllDocuments: (confirmed=true) => apiClient.delete('/api/v1.1/documents/'),

    deleteDocument: (documentId) => apiClient.delete(`/api/v1.1/documents/${documentId}`),

    query: (queryRequest) => apiClient.post('/api/v1.1/query/', queryRequest)
};