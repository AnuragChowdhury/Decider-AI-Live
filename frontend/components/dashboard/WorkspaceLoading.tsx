"use client";

import { motion } from "framer-motion";
import { Check, X, HelpCircle, Target } from "lucide-react";

const paths = [
    { d: "M 0 100 Q 250 50 500 100 T 1000 100", delay: 0 },
    { d: "M 0 300 Q 250 350 500 300 T 1000 300", delay: 1 },
    { d: "M 0 500 Q 250 450 500 500 T 1000 500", delay: 2 },
    { d: "M 0 700 Q 250 750 500 700 T 1000 700", delay: 0.5 },
    { d: "M 0 900 Q 250 850 500 900 T 1000 900", delay: 1.5 },
];

const nodes = [
    { icon: Check, x: "15%", y: "20%", delay: 0, color: "text-green-500/40" },
    { icon: X, x: "85%", y: "25%", delay: 1, color: "text-red-500/40" },
    { icon: HelpCircle, x: "20%", y: "75%", delay: 2, color: "text-blue-500/40" },
    { icon: Target, x: "80%", y: "80%", delay: 0.5, color: "text-purple-500/40" },
    { icon: Check, x: "50%", y: "15%", delay: 1.5, color: "text-emerald-500/40" },
];

export default function WorkspaceLoading() {
    return (
        <div className="h-screen w-full bg-zinc-950 flex flex-col items-center justify-center relative overflow-hidden">
            {/* Background animated paths */}
            <div className="absolute inset-0 pointer-events-none opacity-20">
                <svg className="w-full h-full" viewBox="0 0 1000 1000" preserveAspectRatio="none font-sans">
                    {paths.map((path, i) => (
                        <motion.path
                            key={i}
                            d={path.d}
                            fill="none"
                            stroke="rgba(59, 130, 246, 0.3)"
                            strokeWidth="1"
                            initial={{ pathLength: 0, opacity: 0 }}
                            animate={{
                                pathLength: [0, 1, 1],
                                opacity: [0, 1, 0]
                            }}
                            transition={{
                                duration: 8,
                                repeat: Infinity,
                                delay: path.delay,
                                ease: "easeInOut"
                            }}
                        />
                    ))}
                </svg>
            </div>

            {/* Floating Decision Nodes */}
            {nodes.map((node, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 0 }}
                    animate={{
                        opacity: [0, 1, 1, 0],
                        y: [-20, -100, -20],
                    }}
                    transition={{
                        duration: 10 + i * 2,
                        repeat: Infinity,
                        ease: "linear",
                        delay: node.delay
                    }}
                    className={`absolute flex items-center gap-3 z-0 ${node.color}`}
                    style={{ left: node.x, top: node.y }}
                >
                    <node.icon className="w-8 h-8 opacity-40 blur-[0.5px]" />
                </motion.div>
            ))}

            {/* Horizontal Scanning Bar */}
            <motion.div
                animate={{
                    top: ["-10%", "110%"],
                    opacity: [0, 0.3, 0.3, 0]
                }}
                transition={{
                    duration: 6,
                    repeat: Infinity,
                    ease: "linear"
                }}
                className="absolute left-0 w-full h-32 bg-gradient-to-b from-transparent via-blue-500/10 to-transparent z-10"
            />

            {/* Central Spinner UI */}
            <div className="relative z-20 flex flex-col items-center gap-8">
                <div className="relative">
                    {/* Outer glowing ring */}
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                        className="w-24 h-24 rounded-full border-t-2 border-b-2 border-blue-500/50 blur-[2px]"
                    />
                    {/* Inner spinning ring */}
                    <motion.div
                        animate={{ rotate: -360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-2 rounded-full border-l-2 border-r-2 border-white/40"
                    />
                    {/* Brand Icon in center */}
                    <div className="absolute inset-0 flex items-center justify-center">
                        <motion.div
                            animate={{ scale: [1, 1.1, 1], opacity: [0.5, 1, 0.5] }}
                            transition={{ duration: 2, repeat: Infinity }}
                            className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20 overflow-hidden"
                        >
                            <img src="/brand-icon.png" alt="Logo" className="w-8 h-8 object-contain" />
                        </motion.div>
                    </div>
                </div>

                <div className="flex flex-col items-center gap-2">
                    <motion.div
                        animate={{ opacity: [0.5, 1, 0.5] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="text-xl font-bold text-white tracking-[0.2em] font-sans uppercase"
                    >
                        Initializing Intelligence
                    </motion.div>
                    <div className="text-sm text-gray-500 font-mono tracking-widest flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                        Loading Workspace...
                    </div>
                </div>
            </div>

            {/* Radial background glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-500/5 rounded-full blur-[120px] pointer-events-none z-0" />
        </div>
    );
}
