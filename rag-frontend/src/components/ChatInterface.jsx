import { useEffect, useRef } from "react";
import { useQuery } from "../../hooks/ragApiHooks";


export const MessageList = ({messageHistory}) => {
    return (
        <div className='message-list'>
            {
                messageHistory.map(
                    (msg, idx)=>(
                    <div key={idx} className = {`message msg-${msg.role}`}>
                        <div className='role'>
                            {msg.role}
                        </div>
                        <div className = 'content'>                    
                            {msg.content}
                        </div>
                        <div className = 'timestamp'>
                            {new Date(msg.timestamp).toLocaleTimeString([],{ hour: '2-digit', minute: '2-digit' })}
                        </div>
                    </div>
                    )
                )
            }
        </div>
    )
};


export const QueryInput = ({
    onQuery,
    onClearMessageHistory,
    disabled
}) => {
    const [inputValue, setInputValue] = useState('');

    const handleInputChange = (e) => {
        setInputValue(e.target.value);
    };

    const handleSend = () => {
        if (!disabled) {
            onQuery(inputValue);
            setInputValue('');
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    };

    const handleClear = () => {
        if (!disabled) {
            onClearMessageHistory();
            setInputValue('');
        }
    };

    return (
        <div className='query-input-container'>
            <button
                className='clear-button'
                onClick={handleClear}
                disabled={disabled}
                title='Clear Conversation'>
            </button>
            <input
                className='text-input'
                type='text'
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Query the RAG model..."
                disabled={disabled}
            />
            <button
                className='send-button'
                onClick={handleSend}
                disabled={disabled || !inputValue.trim()}
            >
                Send
            </button>
        </div>
    );
};


export const ChatInterface = () => {
    const bottomRef = useRef(null);
    const {messageHistory, context, loading, error, setError, query, clearMessageHistory} = useQuery();

    const handleQuery = (userQuestion) => {
        query({
            question: userQuestion,
            style: 'distracted',
            return_context: false
        });
    };

    useEffect(() => {
        bottomRef?.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messageHistory, loading]);

    return (
        <div className='chat-interface'>
            <MessageList messageHistory={messageHistory}/>
            <div ref={bottomRef} className='chat status-card'>
                {loading && <div className='loading'>Thinking...</div>}
                {error && 
                    <div className='chat error-alert'>
                        <span className='error-message'>{error}</span>
                        <button
                            className='close-error-btn'
                            onClick={()=>setError(null)}
                            aria-label="Close error"
                        >
                            &times;
                        </button>
                    </div>
                }
            </div>
            <div className='query-input'>
                <QueryInput
                    onQuery={handleQuery}
                    onClearMessageHistory={clearMessageHistory}
                    disabled={loading}
                />
            </div>
        </div>
    );
}