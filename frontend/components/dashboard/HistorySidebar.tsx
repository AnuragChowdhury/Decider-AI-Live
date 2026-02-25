"use client";

import { MessageSquare, Plus, Clock, LogOut, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/services/api";

interface User {
    full_name?: string | null;
    email?: string;
    occupation?: string | null;
}

export default function HistorySidebar({
    sessions,
    onSelectSession,
    onNewAnalysis,
    onDeleteSession,
    activeSessionId,
    user,
}: {
    sessions: any[];
    onSelectSession: (id: number) => void;
    onNewAnalysis: () => void;
    onDeleteSession: (id: number) => void;
    activeSessionId: number | null;
    user?: User | null;
}) {
    // Derive display name: full_name → email prefix → "User"
    const displayName = user?.full_name || (user?.email ? user.email.split("@")[0] : "User");
    const displayRole = user?.occupation || "Member";

    // Initials for avatar
    const initials = displayName
        .split(" ")
        .map((w: string) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2);

    return (
        <aside className="w-64 h-screen bg-zinc-950/80 backdrop-blur-xl border-r border-white/5 flex flex-col fixed left-0 top-0 z-20">

            {/* Header */}
            <div className="p-6 border-b border-white/5">
                <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-3">
                    <div className="w-8 h-8 bg-white rounded-xl flex items-center justify-center shadow-lg shadow-white/10 overflow-hidden">
                        <img src="/brand-icon.png" alt="DECIDER AI" className="w-6 h-6 object-contain" />
                    </div>
                    <span className="tracking-widest uppercase text-sm font-black">Decider AI</span>
                </h1>
            </div>

            {/* New Analysis Button */}
            <div className="p-4">
                <button
                    onClick={onNewAnalysis}
                    className="w-full flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white py-3 px-4 rounded-xl font-medium transition-colors shadow-lg shadow-blue-500/20"
                >
                    <Plus className="w-4 h-4" />
                    New Analysis
                </button>
            </div>

            {/* History List */}
            <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
                <p className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 mt-4">
                    Recent History
                </p>

                <AnimatePresence>
                    {sessions && sessions.length > 0 ? (
                        sessions.map((session: any) => {
                            const isActive = activeSessionId === session.session_id;
                            return (
                                <motion.div
                                    key={session.session_id}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    className="group relative"
                                >
                                    <button
                                        onClick={() => onSelectSession(session.session_id)}
                                        className={`w-full text-left flex items-start gap-3 p-3 rounded-lg transition-all pr-10 ${isActive
                                            ? "bg-white/10 text-white"
                                            : "text-gray-400 hover:bg-white/5 hover:text-white"
                                            }`}
                                    >
                                        <MessageSquare className={`w-4 h-4 mt-1 transition-colors ${isActive ? "text-blue-400" : "text-gray-600 group-hover:text-blue-400"}`} />
                                        <div className="overflow-hidden">
                                            <div className="truncate font-medium text-sm">
                                                {session.title || "Untitled Analysis"}
                                            </div>
                                            <div className="text-xs text-gray-600 flex items-center gap-1 mt-1">
                                                <Clock className="w-3 h-3" />
                                                {new Date(session.created_at).toLocaleDateString()}
                                            </div>
                                        </div>
                                    </button>

                                    {/* Delete Button */}
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            if (confirm("Delete this analysis?")) {
                                                onDeleteSession(session.session_id);
                                            }
                                        }}
                                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-md hover:bg-red-500/20 text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                                        title="Delete Session"
                                    >
                                        <X className="w-3.5 h-3.5" />
                                    </button>
                                </motion.div>
                            );
                        })
                    ) : (
                        <div className="px-4 text-sm text-gray-600 italic">
                            No history yet.
                        </div>
                    )}
                </AnimatePresence>
            </div>

            {/* User Footer */}
            <div className="p-4 border-t border-white/5">
                <div className="flex items-center gap-3">
                    {/* Avatar with initials */}
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500 flex items-center justify-center shrink-0">
                        <span className="text-white text-[10px] font-bold">{initials}</span>
                    </div>
                    <div className="text-sm flex-1 min-w-0">
                        <div className="text-white font-medium truncate">{displayName}</div>
                        <div className="text-xs text-gray-500 truncate">{displayRole}</div>
                    </div>
                    {/* Logout Button */}
                    <button
                        onClick={() => api.logout()}
                        title="Logout"
                        className="p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-all shrink-0"
                    >
                        <LogOut className="w-4 h-4" />
                    </button>
                </div>
            </div>

        </aside>
    );
}
