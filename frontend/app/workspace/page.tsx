"use client";

import { useState, useEffect } from "react";
import HistorySidebar from "@/components/dashboard/HistorySidebar";
import MagicUpload from "@/components/dashboard/MagicUpload";
import DashboardRenderer from "@/components/dashboard/DashboardRenderer";
import ChatPanel from "@/components/dashboard/ChatPanel";
import WorkspaceGraphics from "@/components/dashboard/WorkspaceGraphics";
import WorkspaceLoading from "@/components/dashboard/WorkspaceLoading";
import { motion } from "framer-motion";
import { MessageSquareText } from "lucide-react";
import { api } from "@/services/api";

export default function WorkspacePage() {
    const [loading, setLoading] = useState(true);
    const [sessions, setSessions] = useState<any[]>([]);
    const [viewState, setViewState] = useState("loading"); // loading, empty, dashboard, new_upload, error
    const [dashboardData, setDashboardData] = useState<any[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const [currentUser, setCurrentUser] = useState<any>(null);

    // Chat State
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [triggeredQuery, setTriggeredQuery] = useState<string | undefined>(undefined);

    // 1. Fetch History on Load
    useEffect(() => {
        const loadHistory = async () => {
            try {
                const [history, user] = await Promise.all([
                    api.getHistory(),
                    api.getMe(),
                ]);
                setSessions(history);
                setCurrentUser(user);

                if (history.length > 0) {
                    // Auto-load the most recent session
                    const lastSessionId = history[0].session_id;
                    console.log("Restoring last session:", lastSessionId);
                    await loadDashboard(lastSessionId);
                } else {
                    setViewState("empty");
                }
            } catch (err) {
                console.error("Failed to load history:", err);
                setViewState("empty"); // Fallback
            } finally {
                setLoading(false);
            }
        };

        loadHistory();
    }, []);

    const handleNewAnalysis = () => {
        setViewState("new_upload");
        setDashboardData([]);
        setCurrentSessionId(null);
    };

    const handleUpload = async (file: File) => {
        // file is the File object from MagicUpload
        // We let MagicUpload handle the error catching for UI state
        console.log("Uploading file...", file.name);

        // 1. Upload & Analyze
        const session = await api.uploadFile(file);
        console.log("Session created:", session);

        // 2. Refresh History
        setSessions(prev => [session, ...prev]);
        setCurrentSessionId(session.session_id);

        // 3. Fetch Generated Dashboard
        await loadDashboard(session.session_id);

        setViewState("dashboard");
        setTimeout(() => setIsChatOpen(true), 1500); // Auto-open chat after upload
    };

    const loadDashboard = async (sessionId: number, retryCount = 0) => {
        try {
            setCurrentSessionId(sessionId);
            // setDashboardData([]); // Removed to prevent flicker during polling

            const uiOutput = await api.getDashboard(sessionId);
            console.log("UI Agent Output:", uiOutput);

            // Check if backend is still processing
            const isProcessing = uiOutput.components.some((c: any) =>
                c.type === "kpi" && c.title === "Analysis in Progress"
            );

            if (isProcessing && retryCount < 10) {
                console.log(`Dashboard still processing, retrying... (${retryCount + 1}/10)`);
                // Only set loading if we aren't already in new_upload or dashboard
                if (viewState !== "new_upload") setViewState("loading");
                setTimeout(() => loadDashboard(sessionId, retryCount + 1), 3000);
                return;
            }

            setDashboardData(uiOutput.components);
            setViewState("dashboard");
            setErrorMsg(null);
        } catch (err: any) {
            console.error("Failed to load dashboard:", err);

            // Handle "Processing" error if the backend throws it (case-by-case)
            if (err.message?.includes("PROCESSING") && retryCount < 10) {
                console.log("Session is PROCESSING, retrying...");
                setTimeout(() => loadDashboard(sessionId, retryCount + 1), 3000);
                return;
            }

            setErrorMsg(err.message || "Failed to generate dashboard.");
            setViewState("error");
        }
    };

    const handleSelectSession = (id: number) => {
        console.log("Loading session", id);
        loadDashboard(id);
    };

    const handleDeleteSession = async (id: number) => {
        try {
            await api.deleteSession(id);
            const updatedSessions = sessions.filter(s => s.session_id !== id);
            setSessions(updatedSessions);

            // If we deleted the active session, pick a new one or go to empty state
            if (id === currentSessionId) {
                if (updatedSessions.length > 0) {
                    handleSelectSession(updatedSessions[0].session_id);
                } else {
                    setViewState("empty");
                    setCurrentSessionId(null);
                    setDashboardData([]);
                }
            }
        } catch (err: any) {
            console.error("Failed to delete session:", err);
            alert("Failed to delete session: " + err.message);
        }
    };

    if (loading) {
        return <WorkspaceLoading />;
    }

    // --- SCENARIO A: NEW USER (Empty State) ---
    if (viewState === "empty" || viewState === "new_upload") {
        return (
            <div className="min-h-screen bg-black flex flex-col md:flex-row">
                {/* Sidebar always visible in workspace */}
                <HistorySidebar
                    sessions={sessions}
                    onNewAnalysis={handleNewAnalysis}
                    onSelectSession={handleSelectSession}
                    onDeleteSession={handleDeleteSession}
                    activeSessionId={currentSessionId}
                    user={currentUser}
                />

                <main className="flex-1 md:ml-64 flex flex-col items-center justify-center p-6 relative">

                    {/* Background Grid & Graphics */}
                    <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />
                    <WorkspaceGraphics />

                    <div className="z-10 w-full max-w-4xl">
                        {/* Back button if cancelling new upload? (Optional) */}
                        {viewState === "new_upload" && sessions.length > 3 && (
                            <button
                                onClick={() => {
                                    // Go back to latest session if available
                                    if (sessions.length > 0) handleSelectSession(sessions[0].session_id);
                                    else setViewState("empty");
                                }}
                                className="text-gray-500 hover:text-white mb-8 text-sm flex items-center gap-2"
                            >
                                &larr; Back to Dashboard
                            </button>
                        )}

                        <div className="text-center mb-12">
                            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 tracking-tight">
                                {viewState === "empty" ? "Welcome to DECIDER AI" : "New Analysis"}
                            </h1>
                            <p className="text-xl text-gray-400">
                                {viewState === "empty" ? "Let's turn your data into decisions." : "Upload a new dataset to begin."}
                            </p>
                        </div>

                        <MagicUpload onUpload={handleUpload} />
                    </div>
                </main>
            </div>
        );
    }

    // --- SCENARIO B: RETURNING USER (Dashboard) ---
    return (
        <div className="min-h-screen flex relative overflow-hidden">
            <HistorySidebar
                sessions={sessions}
                onNewAnalysis={handleNewAnalysis}
                onSelectSession={handleSelectSession}
                onDeleteSession={handleDeleteSession}
                activeSessionId={currentSessionId}
                user={currentUser}
            />

            <main className={`
        flex-1 md:ml-64 p-8 text-white min-h-screen transition-all duration-300
        ${isChatOpen ? 'mr-96' : ''} // Push content when chat is open
      `}>
                <div className="max-w-7xl mx-auto">
                    <header className="mb-8 flex items-center justify-between">
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight">Executive Dashboard</h2>
                            <p className="text-gray-400 mt-1">Real-time insights from your sales data.</p>
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setIsChatOpen(!isChatOpen)}
                                className={`
                            flex items-center gap-2 px-4 py-2 rounded-lg text-sm border transition-all
                            ${isChatOpen
                                        ? "bg-blue-600 border-blue-500 text-white"
                                        : "bg-white/5 hover:bg-white/10 border-white/10 text-white"
                                    }
                        `}
                            >
                                <MessageSquareText className="w-4 h-4" />
                                {isChatOpen ? "Close Assistant" : "Ask AI Assistant"}
                            </button>

                            <button className="bg-white/5 hover:bg-white/10 text-white px-4 py-2 rounded-lg text-sm border border-white/10">
                                Export
                            </button>
                        </div>
                    </header>

                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        key={dashboardData.length} // Force re-render animation on data change
                    >
                        {viewState === "loading" ? (
                            <div className="flex flex-col items-center justify-center h-64 border border-dashed border-white/10 rounded-2xl text-gray-500">
                                <div className="text-lg animate-pulse">Loading Workspace...</div>
                            </div>
                        ) : dashboardData.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-64 border border-dashed border-white/10 rounded-2xl text-gray-500 text-center px-4">
                                {viewState === "error" ? (
                                    <>
                                        <div className="text-lg text-red-400">Analysis Error</div>
                                        <div className="text-xs mt-2 max-w-md">{errorMsg || "The AI agent encountered an issue. Please try a different dataset."}</div>
                                    </>
                                ) : (
                                    <>
                                        <div className="text-lg">No Insights Generated</div>
                                        <div className="text-xs mt-2 max-w-md">The analysis completed but no significant patterns were identified to visualize. Try asking the AI Analyst a specific question.</div>
                                    </>
                                )}
                            </div>
                        ) : (
                            /* DYNAMIC RENDERER */
                            <DashboardRenderer
                                components={dashboardData}
                                onDrilldown={(query) => {
                                    console.log("Drilldown:", query);
                                    setIsChatOpen(true);
                                    setTriggeredQuery(query);
                                    setTimeout(() => setTriggeredQuery(undefined), 1000);
                                }}
                            />
                        )}

                    </motion.div>
                </div>
            </main>

            {/* CHAT PANEL */}
            <ChatPanel
                isOpen={isChatOpen}
                onClose={() => setIsChatOpen(false)}
                sessionId={currentSessionId} // Pass ID to chat
                triggeredQuery={triggeredQuery}
            />

        </div>
    );
}
