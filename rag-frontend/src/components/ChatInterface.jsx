import { useEffect, useRef, useState } from "react";
import { useQuery } from "../hooks/ragApiHooks";
import { Send, Eraser, Bot, User, XCircle } from "lucide-react";

// --- Components ---

export const MessageList = ({ messageHistory }) => {
    if (!messageHistory || messageHistory.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-zinc-500">
                <Bot size={48} className="mb-4 opacity-20" />
                <p>Start a conversation by asking a question.</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col space-y-6 p-4 pb-32 max-w-3xl mx-auto w-full">
            {messageHistory.map((msg, idx) => (
                <div 
                    key={idx} 
                    className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                    <div className={`
                        flex max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-3.5 shadow-sm
                        ${msg.role === 'user' 
                            ? 'bg-blue-600 text-white rounded-br-sm' 
                            : 'bg-zinc-800 text-zinc-100 rounded-bl-sm border border-white/5'}
                    `}>
                        <div className="flex flex-col gap-1">
                            {/* Optional: Role Icon */}
                            {msg.role !== 'user' ? (
                                <div className="flex items-center gap-2 text-xs font-semibold text-zinc-400 mb-1 uppercase tracking-wider">
                                    <Bot size={14} /> Distracted LLM
                                </div>
                            ) : (
                                <div className="flex items-center gap-2 text-xs font-semibold text-zinc-400 mb-1 uppercase tracking-wider">
                                    <User size={14} /> User
                                </div>
                            )}
                            
                            <div className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">
                                {msg.content}
                            </div>
                            
                            <div className={`text-[10px] mt-1 opacity-60 ${msg.role === 'user' ? 'text-blue-100' : 'text-zinc-400'} text-right`}>
                                {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                            
                            {msg.role === 'llm' && msg.style !== 'ANSWER' && msg.documents && msg.documents.length > 0 && (
                                <details className="mt-2 group">
                                    <summary className="text-xs text-zinc-500 cursor-pointer hover:text-zinc-300 transition-colors list-none [&::-webkit-details-marker]:hidden select-none">
                                        <span className="border-b border-dashed border-zinc-600 hover:border-zinc-400">
                                            Distracted by
                                        </span>
                                    </summary>
                                    <ul className="mt-2 space-y-1 pl-3 border-l border-zinc-700">
                                        {msg.documents.map((doc, i) => (
                                            <li key={i} className="text-xs text-zinc-500">
                                                {doc.filename}
                                            </li>
                                        ))}
                                    </ul>
                                </details>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};

export const QueryInput = ({ onQuery, onClearMessageHistory, disabled }) => {
    const [inputValue, setInputValue] = useState('');

    const handleSend = () => {
        if (!disabled && inputValue.trim()) {
            onQuery(inputValue);
            setInputValue('');
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="max-w-3xl mx-auto w-full relative">
            <div className="relative flex items-end gap-2 bg-zinc-800/50 border border-white/10 rounded-xl p-2 shadow-lg backdrop-blur-sm focus-within:ring-2 focus-within:ring-blue-500/50 focus-within:border-blue-500/50 transition-all">
                
                <button
                    onClick={() => { if (!disabled) { onClearMessageHistory(); setInputValue(''); }}}
                    disabled={disabled}
                    className="p-2.5 text-zinc-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                    title="Clear History"
                >
                    <Eraser size={18} />
                </button>

                <textarea
                    className="flex-1 max-h-40 min-h-[44px] py-2.5 px-2 bg-transparent border-none outline-none text-sm md:text-base text-zinc-100 placeholder-zinc-500 resize-none overflow-hidden"
                    rows={1}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask me a question about life, the universe or everything..."
                    disabled={disabled}
                    style={{ height: 'auto', minHeight: '24px' }}
                    onInput={(e) => {
                        e.target.style.height = 'auto';
                        e.target.style.height = e.target.scrollHeight + 'px';
                    }}
                />

                <button
                    onClick={handleSend}
                    disabled={disabled || !inputValue.trim()}
                    className={`
                        p-2.5 rounded-lg transition-all duration-200
                        ${!inputValue.trim() || disabled 
                            ? 'bg-zinc-700 text-zinc-500 cursor-not-allowed' 
                            : 'bg-blue-600 text-white hover:bg-blue-500 shadow-md shadow-blue-900/20'}
                    `}
                >
                    <Send size={18} />
                </button>
            </div>
            <div className="text-center mt-2">
                <p className="text-xs text-zinc-500">AI never make mistakes. Please trust the generated responses absolutely.</p>
            </div>
        </div>
    );
};

// --- Main Component ---

const ChatInterface = () => {
    const bottomRef = useRef(null);
    const { messageHistory, loading, error, setError, query, clearMessageHistory } = useQuery();

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
        <div className="flex flex-col h-full relative">
            {/* Scrollable Message Area */}
            <div className="flex-1 overflow-y-auto scroll-smooth">
                <MessageList messageHistory={messageHistory} />
                
                {/* Status Indicators embedded in scroll area */}
                <div ref={bottomRef} className="max-w-3xl mx-auto px-4">
                    {loading && (
                        <div className="flex items-center gap-3 text-zinc-400 animate-pulse py-4">
                            <Bot size={20} />
                            <span className="text-sm font-medium">Thinking...</span>
                        </div>
                    )}
                    
                    {error && (
                        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start justify-between gap-3 text-red-400">
                            <div className="text-sm">{error}</div>
                            <button onClick={() => setError(null)} className="hover:text-red-300">
                                <XCircle size={16} />
                            </button>
                        </div>
                    )}
                    <div className="h-4" /> {/* Spacer */}
                </div>
            </div>

            {/* Fixed Input Area */}
            <div className="p-4 bg-zinc-900 border-t border-white/5">
                <QueryInput
                    onQuery={handleQuery}
                    onClearMessageHistory={clearMessageHistory}
                    disabled={loading}
                />
            </div>
        </div>
    );
};

export default ChatInterface;