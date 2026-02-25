"use client";

import { useState, useRef, useEffect } from "react";
import { Send, X, Sparkles, Bot, User, ChevronRight, ChevronLeft } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion, AnimatePresence } from "framer-motion";

import { api } from "@/services/api";

export default function ChatPanel({ isOpen, onClose, sessionId, triggeredQuery }: { isOpen: boolean, onClose: () => void, sessionId: number | null, triggeredQuery?: string }) {
    const [query, setQuery] = useState("");
    const [messages, setMessages] = useState<any[]>([]);
    const [isTyping, setIsTyping] = useState(false);
    const [historyLoading, setHistoryLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isTyping]);

    // Load chat history from DB whenever the active session changes
    useEffect(() => {
        if (!sessionId) {
            setMessages([]);
            return;
        }
        const loadHistory = async () => {
            setHistoryLoading(true);
            try {
                const history = await api.getSessionMessages(sessionId);
                if (history && history.length > 0) {
                    setMessages(history.map((m: any) => ({ role: m.role, content: m.content })));
                } else {
                    // No messages yet — show default greeting
                    setMessages([{ role: "assistant", content: "Hello! I've analyzed your data. Ask me anything about it." }]);
                }
            } catch (err) {
                console.error("Failed to load chat history:", err);
                setMessages([{ role: "assistant", content: "Hello! I've analyzed your data. Ask me anything about it." }]);
            } finally {
                setHistoryLoading(false);
            }
        };
        loadHistory();
    }, [sessionId]); // Re-runs every time you switch sessions

    // Handle Triggered Query (Drilldown)
    useEffect(() => {
        if (triggeredQuery && isOpen) {
            handleSend(triggeredQuery);
        }
    }, [triggeredQuery, isOpen]);

    const handleSend = async (overrideQuery?: string) => {
        const textToSend = overrideQuery || query;
        if (!textToSend.trim()) return;

        if (!sessionId) {
            alert("No active session! Please upload a file first.");
            return;
        }

        // Add User Message
        const newMsgs = [...messages, { role: "user", content: textToSend }];
        setMessages(newMsgs);

        if (!overrideQuery) setQuery(""); // Clear input if manual typing
        setIsTyping(true);

        try {
            // Call Real Backend API
            const result = await api.chat(sessionId, textToSend);
            setMessages(prev => [...prev, { role: "assistant", content: result.response }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: "assistant", content: "**Error:** Failed to connect to AI Agent. Please try again." }]);
            console.error(err);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ x: 400, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: 400, opacity: 0 }}
                    transition={{ type: "spring", damping: 25, stiffness: 200 }}
                    className="w-96 fixed right-0 top-0 bottom-0 bg-zinc-950/95 backdrop-blur-xl border-l border-white/10 flex flex-col z-30 shadow-2xl"
                >
                    {/* Header */}
                    <div className="p-4 border-b border-white/5 flex items-center justify-between">
                        <div className="flex items-center gap-2 text-white font-medium">
                            <Sparkles className="w-4 h-4 text-blue-500" />
                            AI Analyst
                        </div>
                        <button
                            onClick={onClose}
                            className="p-1 hover:bg-white/10 rounded-md transition-colors"
                        >
                            <X className="w-5 h-5 text-gray-400" />
                        </button>
                    </div>

                    {/* Messages Area */}
                    <div
                        ref={scrollRef}
                        className="flex-1 overflow-y-auto p-4 space-y-6"
                    >
                        {historyLoading ? (
                            <div className="flex items-center justify-center h-16 text-gray-500 text-sm">
                                <div className="w-4 h-4 border-t-2 border-blue-500 rounded-full animate-spin mr-2" />
                                Loading history...
                            </div>
                        ) : null}
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>

                                {/* Avatar */}
                                <div className={`
                  w-8 h-8 rounded-full flex items-center justify-center shrink-0
                  ${msg.role === "assistant" ? "bg-blue-600/20 text-blue-400" : "bg-zinc-800 text-gray-400"}
                `}>
                                    {msg.role === "assistant" ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                                </div>

                                {/* Bubble */}
                                <div className={`
                  max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed
                  ${msg.role === "assistant"
                                        ? "bg-zinc-900 border border-white/5 text-gray-300"
                                        : "bg-blue-600 text-white"
                                    }
                `}>
                                    {msg.role === "assistant" ? (
                                        <div className="prose prose-invert prose-sm max-w-none">
                                            <ReactMarkdown
                                                remarkPlugins={[remarkGfm]}
                                                components={{
                                                    p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                                                    ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2" {...props} />,
                                                    li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                                                    strong: ({ node, ...props }) => <strong className="text-white font-semibold" {...props} />,
                                                    table: ({ node, ...props }) => (
                                                        <div className="overflow-x-auto my-2 rounded-lg border border-white/10">
                                                            <table className="w-full text-left text-xs text-gray-300" {...props} />
                                                        </div>
                                                    ),
                                                    thead: ({ node, ...props }) => <thead className="bg-white/10 text-white uppercase font-semibold" {...props} />,
                                                    tbody: ({ node, ...props }) => <tbody className="divide-y divide-white/5" {...props} />,
                                                    tr: ({ node, ...props }) => <tr className="hover:bg-white/5 transition-colors" {...props} />,
                                                    th: ({ node, ...props }) => <th className="px-3 py-2 whitespace-nowrap" {...props} />,
                                                    td: ({ node, ...props }) => <td className="px-3 py-2 whitespace-nowrap" {...props} />,
                                                }}
                                            >
                                                {msg.content}
                                            </ReactMarkdown>
                                        </div>
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                            </div>
                        ))}

                        {isTyping && (
                            <div className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-blue-600/20 text-blue-400 flex items-center justify-center shrink-0">
                                    <Bot className="w-4 h-4" />
                                </div>
                                <div className="bg-zinc-900 border border-white/5 rounded-2xl px-4 py-3 flex items-center gap-1">
                                    <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0s" }} />
                                    <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                                    <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }} />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Input Area */}
                    <div className="p-4 border-t border-white/5 bg-zinc-950">
                        <div className="relative">
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                                placeholder="Ask about your data..."
                                className="w-full bg-zinc-900 border border-white/10 text-white rounded-xl py-3 pl-4 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-gray-600"
                            />
                            <button
                                onClick={() => handleSend()}
                                disabled={!query.trim() || isTyping}
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </div>
                        <div className="text-center mt-2">
                            <p className="text-[10px] text-gray-600">
                                AI can make mistakes. Check important info.
                            </p>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
