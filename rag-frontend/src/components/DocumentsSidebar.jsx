import { useDocuments } from "../../hooks/ragApiHooks";


const UploadDocumentWidget = ({
    onUploadDocument,
    isLoading,
    error
}) => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef(null);

    const handleFileSelect = (e) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0])
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setIsDragging(false)
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setSelectedFile(e.dataTransfer.files[0]);
        }
    };

    const handleUploadClick = async () => {
        if (!selectedFile) return;
        await onUploadDocument(selectedFile);
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    return (
        <div>
            <h3 className='upload-title'>
                <UpCloud/> Upload New Document
            </h3>
            {!selectedFile ? (
                <div
                    className='upload-drag empty'
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={fileInputRef.current?.click()}
                >
                    <input 
                        type='file'
                        className='file-input'
                        ref={fileInputRef}
                        onChange={handleFileSelect}
                    />
                </div>
            ) : (
                <div className='upload-drag full'>

                </div>
            )}
            <button
                className='upload-btn'
                disabled={!selectedFile || isLoading || error}
                onClick={handleUploadClick}
            >
                {isLoading ? (
                    <span>Uploading file...</span>
                ) : (
                    <span>Upload file</span>
                )}
            </button>
        </div>
    );
};


const DocumentCard = ({
    document,
    onDeleteDocument,
    loading
}) => {
    const color = key%2;
    return (
        <div className={`document-card ${color}`}>
            <h4 className="filename" title={document.filename}>{document.filename}</h4>
            <div className='document-metadata'>
                <span className="file-size">{`${document.filesize} KB, `}</span>
                <span className="num-chunks">{`${document.num_chunks} chunks.`}</span>
                <span className="upload-time">{`Uploaded ${document.uploadTime}`}</span>
            </div>

            <button
                className="document delete btn"
                onClick={() => {onDeleteDocument(document.documentId)}}
                disabled={loading}
            >
                &times;
            </button>
        </div>
    );
};


const DocumentsList = ({
    documents,
    onDeleteDocument,
    loading
}) => {
    if(!documents || documents.length===0){
        return (
            <div className='no-documents-found'>
                <p>No documents found.</p>
            </div>
        );
    }

    return (
        <div className='documents-list'>
            {documents.map((document)=>(
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

export const DocumentsSidebar = ({}) => {
    const {documents, loading, error, setError, uploadDocument, getDocument, deleteDocument, clearDocuments} = useDocuments();
    return (
        <div className='documents-sidebar'>
            <div className='documents-scrollbar'>
                <DocumentsList
                    documents={documents}
                    onGetDocument={getDocument}
                    onDeleteDocument={deleteDocument}
                />
            </div>

            <div className='documents-status-card'>
                {error && <div className='documents error-alert'>
                        <span className='error-message'>{error}</span>
                        <button
                            className='close-error-btn'
                            onClick={()=>setError(null)}
                            aria-label="Close error"
                        >
                            &times;
                        </button>
                    </div>}
                {loading && <div className='documents-loading'>Loading changes...</div> }
            </div>
            {documents.length > 0 && <div className="clear-documents">
                <button className="clear-documents btn" onClick={clearDocuments}>
                    Clear All Documents
                </button>
            </div>}
            <UploadDocumentWidget
                onUploadDocument={uploadDocument}
                isLoading={loading}
                error = {error}
            />
        </div>
    );
}