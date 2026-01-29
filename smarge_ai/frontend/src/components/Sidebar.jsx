import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, MessageSquare, Trash2, Edit2, LogOut, User } from 'lucide-react';

const Sidebar = ({ currentConversationId, onSelectConversation, onNewChat }) => {
    const { user, logout, token } = useAuth();
    const [conversations, setConversations] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchConversations();
    }, []);

    const fetchConversations = async () => {
        try {
            const response = await fetch('http://localhost:8002/conversations', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setConversations(data);
            }
        } catch (error) {
            console.error('Failed to fetch conversations:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteConversation = async (conversationId, e) => {
        e.stopPropagation();

        if (!confirm('Are you sure you want to delete this conversation?')) {
            return;
        }

        try {
            const response = await fetch(`http://localhost:8002/conversations/${conversationId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                setConversations(conversations.filter(c => c.id !== conversationId));
                if (currentConversationId === conversationId) {
                    onNewChat();
                }
            }
        } catch (error) {
            console.error('Failed to delete conversation:', error);
        }
    };

    const handleNewChat = () => {
        onNewChat();
        fetchConversations(); // Refresh list
    };

    return (
        <div className="w-64 bg-slate-900/50 border-r border-white/10 flex flex-col h-screen backdrop-blur-md">
            {/* Header */}
            <div className="p-4 border-b border-white/10">
                <button
                    onClick={handleNewChat}
                    className="w-full flex items-center gap-2 px-4 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-all shadow-lg shadow-primary/25"
                >
                    <Plus size={20} />
                    <span className="font-medium">New Chat</span>
                </button>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {loading ? (
                    <div className="text-center text-slate-500 py-8">Loading...</div>
                ) : conversations.length === 0 ? (
                    <div className="text-center text-slate-500 py-8 text-sm">
                        No conversations yet.<br />Start a new chat!
                    </div>
                ) : (
                    conversations.map((conv) => (
                        <div
                            key={conv.id}
                            onClick={() => onSelectConversation(conv.id)}
                            className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all ${currentConversationId === conv.id
                                    ? 'bg-primary/20 border border-primary/30'
                                    : 'hover:bg-slate-800/50 border border-transparent'
                                }`}
                        >
                            <MessageSquare size={16} className="text-slate-400 shrink-0" />
                            <span className="flex-1 text-sm text-slate-300 truncate">
                                {conv.title}
                            </span>
                            <button
                                onClick={(e) => handleDeleteConversation(conv.id, e)}
                                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded transition-all"
                            >
                                <Trash2 size={14} className="text-red-400" />
                            </button>
                        </div>
                    ))
                )}
            </div>

            {/* User Profile */}
            <div className="p-4 border-t border-white/10">
                <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-sky-500 flex items-center justify-center">
                        <User size={16} className="text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-white truncate">
                            {user?.username}
                        </div>
                        <div className="text-xs text-slate-400 truncate">
                            {user?.email}
                        </div>
                    </div>
                </div>
                <button
                    onClick={logout}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-slate-800/50 rounded-lg transition-all"
                >
                    <LogOut size={16} />
                    <span>Logout</span>
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
