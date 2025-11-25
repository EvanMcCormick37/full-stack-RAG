import axios from 'axios';

const API_BASE_URL = ''; //Replace with VITE_BASE_URL for dev mode
const API_PREFIX = import.meta.env.VITE_API_PREFIX;
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
            `${API_PREFIX}/documents/`,
            formData,
            {
                headers: {'Content-Type': 'multipart/form-data'}
            }
        );
    },

    listDocuments: () => apiClient.get(`${API_PREFIX}/documents/`),

    getDocument: (documentId) => apiClient.get(`${API_PREFIX}/documents/${documentId}`),

    deleteAllDocuments: (confirmed=true) => apiClient.delete(`${API_PREFIX}/documents/`,
        {params: {confirm: confirmed}}
    ),

    deleteDocument: (documentId) => apiClient.delete(`${API_PREFIX}/documents/${documentId}`),

    query: (queryRequest) => apiClient.post(`${API_PREFIX}/query/`, queryRequest)
};