import { useState, useRef } from "react";
import { useDocuments } from "../hooks/ragApiHooks";
import { CloudUpload, FileText, Trash2, HardDrive } from "lucide-react";

const UploadDocumentWidget = ({ onUploadDocument, isLoading, error }) => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef(null);

    const handleFileSelect = (e) => {
        if (e.target.files && e.target.files[0]) setSelectedFile(e.target.files[0]);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) setSelectedFile(e.dataTransfer.files[0]);
    };

    const handleUploadClick = async () => {
        if (!selectedFile) return;
        await onUploadDocument(selectedFile);
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    return (
        <div className="p-4 border-t border-white/10 bg-zinc-900/50">
            <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <CloudUpload size={14} /> Upload Distraction
            </h3>
            
            <div
                className={`
                    relative border-2 border-dashed rounded-xl p-4 text-center transition-all duration-200 cursor-pointer
                    ${isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800'}
                    ${selectedFile ? 'border-solid border-blue-500/50 bg-zinc-800' : ''}
                `}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input 
                    type='file' 
                    className='hidden' 
                    ref={fileInputRef} 
                    onChange={handleFileSelect} 
                />
                
                {!selectedFile ? (
                    <div className="flex flex-col items-center gap-2 text-zinc-400">
                        <CloudUpload size={24} />
                        <span className="text-xs font-medium">Click or drag PDF here</span>
                    </div>
                ) : (
                    <div className="flex items-center gap-3 text-left">
                        <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
                            <FileText size={20} />
                        </div>
                        <div className="overflow-hidden">
                            <p className="text-xs font-medium text-zinc-200 truncate w-32">{selectedFile.name}</p>
                            <p className="text-[10px] text-zinc-500">Ready to upload</p>
                        </div>
                    </div>
                )}
            </div>

            <button
                className={`
                    w-full mt-3 py-2 px-4 rounded-lg text-sm font-medium transition-all
                    ${!selectedFile || isLoading 
                        ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' 
                        : 'bg-blue-600 text-white hover:bg-blue-500 shadow-lg shadow-blue-900/20'}
                `}
                disabled={!selectedFile || isLoading || error}
                onClick={handleUploadClick}
            >
                {isLoading ? 'Uploading...' : 'Upload File'}
            </button>
        </div>
    );
};

const DocumentCard = ({ document, onDeleteDocument, loading }) => {
    return (
        <div className="group flex items-center justify-between p-3 rounded-lg hover:bg-zinc-800/50 border border-transparent hover:border-white/5 transition-all mb-1">
            <div className="flex items-center gap-3 overflow-hidden">
                <div className="min-w-[32px] h-8 flex items-center justify-center bg-zinc-800 rounded-md text-zinc-400 group-hover:text-blue-400 group-hover:bg-blue-500/10 transition-colors">
                    <FileText size={16} />
                </div>
                <div className="flex flex-col min-w-0">
                    <h4 className="text-sm font-medium text-zinc-300 truncate" title={document.filename}>
                        {document.filename}
                    </h4>
                    <div className="flex items-center gap-2 text-[10px] text-zinc-500">
                        <span>{document.file_size} KB</span>
                        <span className="w-1 h-1 rounded-full bg-zinc-600"></span>
                        <span>{document.num_chunks} chunks</span>
                    </div>
                </div>
            </div>

            <button
                className="p-1.5 text-zinc-500 hover:text-red-400 hover:bg-red-400/10 rounded-md opacity-0 group-hover:opacity-100 transition-all"
                onClick={() => onDeleteDocument(document.document_id)}
                disabled={loading}
                title="Delete Document"
            >
                <Trash2 size={14} />
            </button>
        </div>
    );
};

const DocumentsList = ({ documents, onDeleteDocument, loading }) => {
    if (!documents || documents.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-32 text-zinc-600 px-6 text-center border-2 border-dashed border-zinc-800 rounded-xl mx-4 mt-4">
                <HardDrive size={24} className="mb-2 opacity-50" />
                <p className="text-xs">No distractions indexed.</p>
            </div>
        );
    }

    return (
        <div className="px-2 py-2 space-y-1">
            {documents.map((document) => (
                <DocumentCard
                    key={document.documentId}
                    document={document}
                    onDeleteDocument={onDeleteDocument}
                    loading={loading}
                />
            ))}
        </div>
    );
};

const DocumentsSidebar = () => {
    const { documents, loading, error, setError, uploadDocument, getDocument, deleteDocument, clearDocuments } = useDocuments();
    
    return (
        <div className="flex flex-col h-full">
            <div className="p-4 border-b border-white/10">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    Distractions
                </h2>
                <p className="text-xs text-zinc-500 mt-1">Give the LLM something fun to think about.</p>
            </div>

            <div className="flex-1 overflow-y-auto scrollbar-thin">
                <DocumentsList
                    documents={documents}
                    onGetDocument={getDocument}
                    onDeleteDocument={deleteDocument}
                    loading={loading}
                />
            </div>

            <div className="px-4">
                {error && (
                    <div className="mb-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center justify-between text-xs text-red-400">
                        <span className="truncate">{error}</span>
                        <button onClick={() => setError(null)}>&times;</button>
                    </div>
                )}
                
                {documents.length > 0 && (
                    <button 
                        className="w-full py-2 text-xs text-red-400 hover:bg-red-400/5 rounded-lg transition-colors mb-2" 
                        onClick={clearDocuments}
                    >
                        Clear All Documents
                    </button>
                )}
            </div>

            <UploadDocumentWidget
                onUploadDocument={uploadDocument}
                isLoading={loading}
                error={error}
            />
        </div>
    );
};

export default DocumentsSidebar;