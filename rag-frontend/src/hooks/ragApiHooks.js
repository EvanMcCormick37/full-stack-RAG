import { useState, useEffect } from "react";
import { ragApi } from "../api/ragApi";

export const useDocuments = () => {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchDocuments = async () => {
        setLoading(true);
        try{
            const response = await ragApi.listDocuments();
            setDocuments(response.documents ?? []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const uploadDocument = async (file) => {
        setLoading(true);
        try {
            const { response } = await ragApi.uploadDocument(file);
            await fetchDocuments();
            return response;
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const getDocument = async (documentId) => {
        setLoading(true);
        try {
            const { response } = await ragApi.getDocument(documentId);
            return response;
        } catch (err) {
            setError(err.message);
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
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const clearDocuments = async () => {
        setLoading(true);
        try{
            const response = await ragApi.deleteAllDocuments();
            await fetchDocuments();
            return response;
        } catch (err) {
            setError(err.message);
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
            setMessageHistory(prev => ([
                ...prev, {
                    role: 'llm',
                    content: response.answer,
                    context: response.context || null,
                    timestamp: new Date()
                }
            ]));
            setContext(response.context || null);
        } catch (err) {
            setError(err.message);
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