import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Send, User, Bot, Loader2, Sparkles } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from './Sidebar';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

const ChatInterface = () => {
    const { token } = useAuth();
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [currentConversationId, setCurrentConversationId] = useState(null);
    const messagesContainerRef = useRef(null);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        if (messagesContainerRef.current) {
            const { scrollHeight, clientHeight } = messagesContainerRef.current;
            messagesContainerRef.current.scrollTo({
                top: scrollHeight - clientHeight,
                behavior: 'smooth'
            });
        }
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const loadConversation = async (conversationId) => {
        try {
            const response = await fetch(`http://localhost:8002/conversations/${conversationId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setMessages(data.messages.map(msg => ({
                    role: msg.role,
                    content: msg.content
                })));
                setCurrentConversationId(conversationId);
            }
        } catch (error) {
            console.error('Failed to load conversation:', error);
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setCurrentConversationId(null);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8002/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    conversation_id: currentConversationId,
                    message: input
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to send message');
            }

            // Get conversation ID from response headers
            const conversationId = response.headers.get('X-Conversation-ID');
            if (conversationId && !currentConversationId) {
                setCurrentConversationId(conversationId);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = { role: 'assistant', content: '' };

            setMessages(prev => [...prev, assistantMessage]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                assistantMessage.content += chunk;

                setMessages(prev => {
                    const newMessages = [...prev];
                    newMessages[newMessages.length - 1] = { ...assistantMessage };
                    return newMessages;
                });
            }

        } catch (error) {
            console.error('Error:', error);
            setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-background text-foreground font-sans overflow-hidden">
            {/* Sidebar */}
            <Sidebar
                currentConversationId={currentConversationId}
                onSelectConversation={loadConversation}
                onNewChat={handleNewChat}
            />

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col relative overflow-hidden">
                {/* Background Gradients */}
                <div className="absolute top-[-20%] right-[-10%] w-[500px] h-[500px] bg-primary/20 rounded-full blur-[100px] pointer-events-none" />
                <div className="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-sky-500/10 rounded-full blur-[80px] pointer-events-none" />

                {/* Header */}
                <header className="absolute top-0 w-full z-10 border-b border-white/10 bg-background/80 backdrop-blur-md px-6 py-4 flex items-center justify-between shadow-sm">
                    <div className="flex items-center gap-2">
                        <div className="p-2 bg-gradient-to-tr from-primary to-sky-500 rounded-xl shadow-lg shadow-primary/20">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-lg font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
                            SmargeAI
                        </span>
                    </div>
                    <div className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-medium text-primary-foreground/90">
                        Gemini 2.5 Flash
                    </div>
                </header>

                {/* Messages Area */}
                <div
                    ref={messagesContainerRef}
                    className="flex-1 overflow-y-auto px-4 pt-24 pb-32 space-y-8 scroll-smooth"
                >
                    {messages.length === 0 ? (
                        <div className="flex items-center justify-center h-full">
                            <div className="text-center space-y-4">
                                <div className="p-4 bg-gradient-to-tr from-primary to-sky-500 rounded-2xl shadow-lg shadow-primary/20 inline-block">
                                    <Sparkles className="w-12 h-12 text-white" />
                                </div>
                                <h2 className="text-2xl font-bold text-white">Start a new conversation</h2>
                                <p className="text-slate-400">Ask me anything!</p>
                            </div>
                        </div>
                    ) : (
                        messages.map((msg, index) => (
                            <div
                                key={index}
                                className={cn(
                                    "flex w-full items-start gap-4 mx-auto max-w-4xl animate-slide-up",
                                    msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                                )}
                            >
                                {/* Avatar */}
                                <div className={cn(
                                    "w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg ring-1 ring-white/10",
                                    msg.role === 'user'
                                        ? "bg-gradient-to-br from-indigo-500 to-purple-600"
                                        : "bg-gradient-to-br from-slate-700 to-slate-800"
                                )}>
                                    {msg.role === 'user' ? <User size={18} className="text-white" /> : <Bot size={18} className="text-sky-400" />}
                                </div>

                                {/* Content */}
                                <div className={cn(
                                    "rounded-2xl px-6 py-4 max-w-[85%] shadow-xl backdrop-blur-sm transition-all duration-200",
                                    msg.role === 'user'
                                        ? "bg-primary text-white rounded-tr-sm"
                                        : "bg-slate-800/50 border border-white/5 text-slate-100 rounded-tl-sm"
                                )}>
                                    <ReactMarkdown
                                        components={{
                                            code({ node, inline, className, children, ...props }) {
                                                const match = /language-(\w+)/.exec(className || '')
                                                return !inline && match ? (
                                                    <div className="relative group my-4 rounded-lg overflow-hidden border border-white/10 shadow-2xl">
                                                        <div className="absolute top-0 left-0 w-full px-4 py-2 bg-slate-900/50 border-b border-white/5 flex items-center justify-between">
                                                            <span className="text-xs font-mono text-slate-400">{match[1]}</span>
                                                        </div>
                                                        <SyntaxHighlighter
                                                            style={vscDarkPlus}
                                                            language={match[1]}
                                                            PreTag="div"
                                                            customStyle={{ margin: 0, paddingTop: '2.5rem', background: '#0f172a' }}
                                                            {...props}
                                                        >
                                                            {String(children).replace(/\n$/, '')}
                                                        </SyntaxHighlighter>
                                                    </div>
                                                ) : (
                                                    <code className={cn(
                                                        "px-1.5 py-0.5 rounded font-mono text-sm border",
                                                        msg.role === 'user'
                                                            ? "bg-white/20 border-white/20 text-white"
                                                            : "bg-slate-900/60 border-white/10 text-sky-300"
                                                    )} {...props}>
                                                        {children}
                                                    </code>
                                                )
                                            },
                                            p: ({ children }) => <p className="leading-7 mb-4 last:mb-0">{children}</p>,
                                            ul: ({ children }) => <ul className="list-disc pl-4 mb-4 space-y-2">{children}</ul>,
                                            ol: ({ children }) => <ol className="list-decimal pl-4 mb-4 space-y-2">{children}</ol>,
                                        }}
                                    >
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>
                            </div>
                        ))
                    )}

                    {isLoading && (
                        <div className="flex w-full items-start gap-4 mx-auto max-w-4xl">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center shrink-0 shadow-lg ring-1 ring-white/10">
                                <Bot size={18} className="text-sky-400" />
                            </div>
                            <div className="bg-slate-800/50 border border-white/5 rounded-2xl rounded-tl-sm px-6 py-4 shadow-xl backdrop-blur-sm">
                                <div className="flex items-center gap-2">
                                    <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
                                    <span className="text-sm text-slate-400 animate-pulse">SmargeAI is thinking...</span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="absolute bottom-0 w-full p-6 bg-gradient-to-t from-background via-background/90 to-transparent">
                    <div className="max-w-4xl mx-auto">
                        <form onSubmit={handleSubmit} className="relative group">
                            <div className="absolute -inset-0.5 bg-gradient-to-r from-primary to-sky-500 rounded-full opacity-30 group-hover:opacity-100 transition duration-500 blur"></div>
                            <div className="relative flex items-center gap-2 bg-slate-900/90 rounded-full p-2 pl-6 border border-white/10 shadow-2xl">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Ask anything..."
                                    disabled={isLoading}
                                    className="flex-1 bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none py-3"
                                />
                                <button
                                    type="submit"
                                    disabled={isLoading || !input.trim()}
                                    className="p-3 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-primary/25"
                                >
                                    <Send size={20} />
                                </button>
                            </div>
                        </form>
                        <p className="text-center text-xs text-muted-foreground mt-4">
                            Powered by Google Gemini 2.5 Flash • Designed by Antigravity
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
