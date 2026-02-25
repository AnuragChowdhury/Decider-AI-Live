"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, FileSpreadsheet, Loader2, Sparkles, Bot, BrainCircuit, LayoutDashboard } from "lucide-react";

export default function MagicUpload({ onUpload }: { onUpload: (file: File) => Promise<void> }) {
    const [isHovering, setIsHovering] = useState(false);
    const [uploadStatus, setUploadStatus] = useState<"idle" | "processing">("idle");
    const [progressMessage, setProgressMessage] = useState("Initializing...");
    const [activeAgent, setActiveAgent] = useState<"Validator" | "Analyst" | "Architect">("Validator");

    // Handling file selection
    const handleFile = async (files: FileList | null) => {
        if (!files || files.length === 0) return;
        const file = files[0];

        setIsHovering(false);
        setUploadStatus("processing");

        // Start the "Fake" Progress Simulation (Visuals only, while real request waits)
        const stopSimulation = startProgressSimulation();

        try {
            // --- REAL API CALL ---
            await onUpload(file);
            // If successful, the parent component will unmount this or redirect, 
            // so we don't need a "Done" state here.
        } catch (error) {
            console.error(error);
            setUploadStatus("idle"); // Reset on error
            alert("Upload failed. Please try again.");
        } finally {
            stopSimulation();
        }
    };

    // --- Progress Simulation Logic ---
    const startProgressSimulation = () => {
        let step = 0;
        const steps = [
            { msg: "Validation Agent: Checking data integrity...", agent: "Validator" },
            { msg: "Validation Agent: Standardizing date formats...", agent: "Validator" },
            { msg: "Analytics Agent: Calculating KPIs...", agent: "Analyst" },
            { msg: "Analytics Agent: Detecting anomalies...", agent: "Analyst" },
            { msg: "Analytics Agent: Forecasting future trends...", agent: "Analyst" },
            { msg: "UI Agent: Designing your dashboard layout...", agent: "Architect" },
            { msg: "UI Agent: Choosing the best charts...", agent: "Architect" },
            { msg: "Finalizing: Good things take time...", agent: "Architect" }
        ];

        // Initial state
        setProgressMessage(steps[0].msg);
        setActiveAgent(steps[0].agent as any);

        const interval = setInterval(() => {
            step++;
            if (step < steps.length) {
                setProgressMessage(steps[step].msg);
                setActiveAgent(steps[step].agent as any);
            }
        }, 2000); // Change message every 2 seconds

        return () => clearInterval(interval);
    };

    return (
        <div className="w-full max-w-2xl mx-auto">
            <AnimatePresence mode="wait">

                {/* IDLE / HOVER STATE */}
                {uploadStatus === "idle" && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="relative"
                    >
                        <div
                            onDragOver={(e) => { e.preventDefault(); setIsHovering(true); }}
                            onDragLeave={() => setIsHovering(false)}
                            onDrop={(e) => { e.preventDefault(); handleFile(e.dataTransfer.files); }}
                            className={`
                                relative group cursor-pointer
                                border-2 border-dashed rounded-3xl p-12
                                flex flex-col items-center justify-center text-center
                                transition-all duration-300 ease-out
                                ${isHovering
                                    ? "border-blue-500 bg-blue-500/5 scale-[1.02]"
                                    : "border-white/10 hover:border-white/20 hover:bg-white/5 bg-black"
                                }
                            `}
                        >
                            <input
                                type="file"
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                onChange={(e) => handleFile(e.target.files)}
                                accept=".csv,.xlsx"
                            />

                            {/* Animated Glow Effect */}
                            <div className={`
                                absolute w-24 h-24 rounded-full bg-blue-500/20 blur-xl transition-all duration-500
                                ${isHovering ? "scale-150 opacity-80" : "scale-100 opacity-0"}
                            `} />

                            <div className="z-10 bg-zinc-900/50 p-6 rounded-full border border-white/10 mb-6">
                                <UploadCloud className={`w-10 h-10 ${isHovering ? 'text-blue-400' : 'text-gray-400'}`} />
                            </div>

                            <h3 className="text-2xl font-bold text-white mb-2">
                                Upload Information
                            </h3>
                            <p className="text-gray-400 mb-6">
                                Drag & drop your CSV or Excel file here
                            </p>

                            <div className="flex items-center gap-4 text-xs text-gray-500 font-mono">
                                <span className="flex items-center gap-1.5 border border-white/10 px-2 py-1 rounded">
                                    <FileSpreadsheet className="w-3 h-3" /> .CSV
                                </span>
                                <span className="flex items-center gap-1.5 border border-white/10 px-2 py-1 rounded">
                                    <FileSpreadsheet className="w-3 h-3" /> .XLSX
                                </span>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* PROCESSING STATE (Replaces Old Progress/Done Screens) */}
                {uploadStatus === "processing" && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="bg-zinc-900 border border-white/10 rounded-2xl p-8 max-w-md mx-auto relative overflow-hidden"
                    >
                        {/* Pulse Background */}
                        <div className="absolute inset-0 bg-blue-500/5 animate-pulse" />

                        <div className="flex flex-col items-center text-center space-y-8 relative z-10">

                            {/* Agent Icon Animation */}
                            <div className="relative w-20 h-20 flex items-center justify-center">
                                {/* Ring 1 */}
                                <div className="absolute inset-0 border-2 border-blue-500/30 rounded-full animate-[spin_3s_linear_infinite]" />
                                {/* Ring 2 */}
                                <div className="absolute inset-2 border-2 border-purple-500/30 rounded-full animate-[spin_4s_linear_infinite_reverse]" />

                                <div className="bg-zinc-950 p-3 rounded-full border border-white/10 shadow-xl">
                                    <AnimatePresence mode="wait">
                                        {activeAgent === "Validator" && (
                                            <motion.div key="valid" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
                                                <Sparkles className="w-8 h-8 text-green-400" />
                                            </motion.div>
                                        )}
                                        {activeAgent === "Analyst" && (
                                            <motion.div key="analyst" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
                                                <BrainCircuit className="w-8 h-8 text-purple-400" />
                                            </motion.div>
                                        )}
                                        {activeAgent === "Architect" && (
                                            <motion.div key="arch" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
                                                <LayoutDashboard className="w-8 h-8 text-blue-400" />
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <h3 className="text-xl font-medium text-white">
                                    Working on your data...
                                </h3>
                                <motion.p
                                    key={progressMessage}
                                    initial={{ opacity: 0, y: 5 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="text-sm text-blue-300/80 font-mono h-6"
                                >
                                    {progressMessage}
                                </motion.p>
                            </div>

                            {/* Simple Progress Bar */}
                            <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                                    initial={{ width: "0%" }}
                                    animate={{ width: "100%" }}
                                    transition={{ duration: 15, ease: "linear" }}
                                />
                            </div>
                        </div>
                    </motion.div>
                )}

            </AnimatePresence>
        </div>
    );
}
