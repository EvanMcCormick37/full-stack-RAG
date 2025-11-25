import { useState, useEffect } from "react";
import { ragApi } from "../api-js/ragApi";

export const useDocuments = () => {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchDocuments = async () => {
        setLoading(true);
        try{
            const response = await ragApi.listDocuments();
            setDocuments(response.data.documents ?? []);
        } catch (err) {
            setError(`${err.message} ${err.response?.data?.detail ??''}`);
        } finally {
            setLoading(false);
        }
    };

    const uploadDocument = async (file) => {
        setLoading(true);
        try {
            await ragApi.uploadDocument(file);
            await fetchDocuments();
        } catch (err) {
            setError(`${err.message} ${err.response?.data?.detail ??''}`);
        } finally {
            setLoading(false);
        }
    };

    const getDocument = async (documentId) => {
        setLoading(true);
        try {
            const response = await ragApi.getDocument(documentId);
            return response.data;
        } catch (err) {
            setError(`${err.message} ${err.response?.data?.detail ??''}`);
        } finally {
            setLoading(false);
        }
    }

    const deleteDocument = async (documentId) => {
        setLoading(true);
        try {
            await ragApi.deleteDocument(documentId);
            await fetchDocuments();
        } catch (err) {
            setError(`${err.message} ${err.response?.data?.detail ??''}`);
        } finally {
            setLoading(false);
        }
    };

    const clearDocuments = async () => {
        setLoading(true);
        try{
            await ragApi.deleteAllDocuments();
            await fetchDocuments();
        } catch (err) {
            setError(`${err.message} ${err.response?.data?.detail ??''}`);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        fetchDocuments();
    }, []);

    return {documents, loading, error, setError, uploadDocument, getDocument, deleteDocument, clearDocuments };
};

export const useQuery = () => {
    const [messageHistory, setMessageHistory] = useState([]);
    const [context, setContext] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const query = async (query) => {
        setLoading(true);
        try{
            setMessageHistory(prev => ([
                ...prev, {
                    role: 'user',
                    content: query.question,
                    timestamp: new Date()
                }
            ]))
            const response = await ragApi.query(query);
            const data = response.data;
            setMessageHistory(prev => ([
                ...prev, {
                    role: 'llm',
                    content: data.answer,
                    context: data.context || null,
                    timestamp: new Date()
                }
            ]));
            setContext(response.context || null);
        } catch (err) {
            setError(`${err.message} ${err.response?.data?.detail ??''}`);
        } finally {
            setLoading(false);
        }

    };

    const clearMessageHistory = () => {
        setMessageHistory([]);
        setContext(null);
        setError(null)
    }

    return {messageHistory, context, loading, error, setError, query, clearMessageHistory}
}