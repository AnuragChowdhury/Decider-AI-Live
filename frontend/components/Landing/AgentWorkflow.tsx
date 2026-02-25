import { motion } from "framer-motion";
import { Database, Search, Brain, BarChart, ExternalLink } from "lucide-react";

// Agent Nodes
const agents = [
    { id: "ingest", label: "Data Ingestion", icon: Database, color: "bg-blue-500", x: 0, y: 50 },
    { id: "validate", label: "Validation Agent", icon: Search, color: "bg-amber-500", x: 100, y: 50 },
    { id: "analytics", label: "Analytics Agent", icon: BarChart, color: "bg-green-500", x: 200, y: 0 },
    { id: "reasoning", label: "Reasoning Agent", icon: Brain, color: "bg-purple-500", x: 200, y: 100 },
    { id: "dashboard", label: "User Dashboard", icon: ExternalLink, color: "bg-indigo-500", x: 300, y: 50 },
];

export default function AgentWorkflow() {
    return (
        <div className="relative w-full h-[400px] flex items-center justify-center overflow-hidden bg-zinc-900/50 rounded-3xl border border-white/5 shadow-2xl backdrop-blur-sm">
            <div className="absolute inset-0 bg-grid-white/[0.02] bg-[length:20px_20px]" />

            {/* SVG Container for Lines */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
                <motion.path
                    d="M 150 200 L 250 200 L 350 150 L 450 200"
                    fill="transparent"
                    stroke="url(#gradient)"
                    strokeWidth="2"
                    initial={{ pathLength: 0, opacity: 0 }}
                    animate={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                />
                <motion.path
                    d="M 250 200 L 350 250 L 450 200"
                    fill="transparent"
                    stroke="url(#gradient)"
                    strokeWidth="2"
                    initial={{ pathLength: 0, opacity: 0 }}
                    animate={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 2, delay: 1, repeat: Infinity, ease: "linear" }}
                />
                <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#3b82f6" stopOpacity="0" />
                        <stop offset="50%" stopColor="#8b5cf6" stopOpacity="1" />
                        <stop offset="100%" stopColor="#ec4899" stopOpacity="0" />
                    </linearGradient>
                </defs>
            </svg>

            {/* Nodes */}
            <div className="relative z-10 flex gap-8 md:gap-16 items-center">
                {agents.map((agent, index) => (
                    <motion.div
                        key={agent.id}
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.2, type: "spring" }}
                        className="flex flex-col items-center gap-3 relative group"
                    >
                        <div className={`w-16 h-16 rounded-2xl ${agent.color} bg-opacity-10 border border-${agent.color.replace('bg-', '')}/20 flex items-center justify-center relative overflow-hidden group-hover:border-white/40 transition-colors duration-500`}>
                            {/* Pulse Effect */}
                            <motion.div
                                className={`absolute inset-0 ${agent.color} opacity-20`}
                                animate={{ scale: [1, 2, 1], opacity: [0.2, 0, 0.2] }}
                                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                            />
                            <agent.icon className={`w-8 h-8 text-white relative z-10 transition-transform duration-500 group-hover:scale-110`} />
                        </div>

                        <div className="absolute -bottom-10 text-center w-32">
                            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em] group-hover:text-white transition-colors">{agent.label}</span>
                        </div>

                        {/* Neural Pulse Channels */}
                        {index < agents.length - 1 && (
                            <div className="absolute top-8 left-16 w-16 h-px bg-white/5">
                                <motion.div
                                    className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-500 to-transparent blur-[2px]"
                                    animate={{
                                        x: [-32, 64],
                                        opacity: [0, 1, 0]
                                    }}
                                    transition={{
                                        duration: 1.5,
                                        repeat: Infinity,
                                        ease: "circIn",
                                        delay: index * 0.3
                                    }}
                                />
                            </div>
                        )}
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
