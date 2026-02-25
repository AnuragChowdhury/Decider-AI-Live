"use client";

import { motion } from "framer-motion";
import { Activity, Zap, Shield, Target, TrendingUp, Cpu } from "lucide-react";

const signals = [
    { text: "SIGNAL: WIN VELOCITY", x: "12%", y: "25%", delay: 0, icon: TrendingUp },
    { text: "CORE: DECISION SYNC", x: "82%", y: "18%", delay: 2, icon: Cpu },
    { text: "NODE: PIPELINE FORENSICS", x: "78%", y: "82%", delay: 1, icon: Target },
    { text: "AUTH: ENTERPRISE SHIELD", x: "8%", y: "75%", delay: 3, icon: Shield },
    { text: "DATA: NEURAL INGESTION", x: "45%", y: "12%", delay: 4, icon: Zap },
    { text: "STATUS: AGENT READY", x: "62%", y: "88%", delay: 5, icon: Activity },
];

const GridPulse = ({ delay = 0, duration = 3, top = "50%" }) => (
    <motion.div
        initial={{ left: "-10%", opacity: 0 }}
        animate={{
            left: ["-10%", "110%"],
            opacity: [0, 0.8, 0.8, 0]
        }}
        transition={{
            duration,
            repeat: Infinity,
            delay,
            ease: "linear"
        }}
        className="absolute h-[1px] w-32 bg-gradient-to-r from-transparent via-blue-400 to-transparent z-10"
        style={{ top }}
    />
);

export default function WorkspaceGraphics() {
    return (
        <div className="absolute inset-0 pointer-events-none overflow-hidden select-none">
            {/* Horizontal Scanning Bar */}
            <motion.div
                animate={{
                    top: ["-10%", "110%"],
                    opacity: [0, 0.4, 0.4, 0]
                }}
                transition={{
                    duration: 10,
                    repeat: Infinity,
                    ease: "linear"
                }}
                className="absolute left-0 w-full h-40 bg-gradient-to-b from-transparent via-blue-500/5 to-transparent z-10"
            >
                <div className="absolute top-1/2 left-0 w-full h-[1px] bg-blue-400/20 blur-[1px]" />
            </motion.div>

            {/* Traveling Grid Pulses */}
            <GridPulse top="20%" delay={0} duration={4} />
            <GridPulse top="45%" delay={2} duration={5} />
            <GridPulse top="75%" delay={1} duration={3.5} />
            <GridPulse top="90%" delay={3} duration={6} />

            {/* Background SVG Grid (Neural Connections) */}
            <svg className="absolute inset-0 w-full h-full opacity-[0.03]">
                <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
                    <circle cx="50" cy="50" r="1.5" fill="white" />
                    <path d="M 50 50 L 150 50 M 50 50 L 50 150" stroke="white" strokeWidth="0.5" strokeDasharray="4 4" />
                </pattern>
                <rect width="100%" height="100%" fill="url(#grid)" />
            </svg>

            {/* Explicit Intelligence Graphics */}
            <div className="absolute inset-0 z-0">
                {/* 1. Sales Funnel (Left Center) */}
                <motion.div
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 0.2, x: 0 }}
                    transition={{ duration: 2 }}
                    className="absolute left-[5%] top-[40%] w-64 h-64"
                >
                    <svg viewBox="0 0 200 200" className="w-full h-full text-blue-500">
                        <defs>
                            <linearGradient id="funnelGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stopColor="currentColor" stopOpacity="0.8" />
                                <stop offset="100%" stopColor="currentColor" stopOpacity="0.2" />
                            </linearGradient>
                            <mask id="funnelMask">
                                <path d="M40,20 L160,20 L120,180 L80,180 Z" fill="white" />
                            </mask>
                        </defs>
                        <path d="M40,20 L160,20 L120,180 L80,180 Z" fill="url(#funnelGrad)" />

                        {/* Internal Animated segments */}
                        <motion.path
                            d="M60,40 L140,40 L130,80 L70,80 Z"
                            fill="white"
                            animate={{ opacity: [0.1, 0.3, 0.1] }}
                            transition={{ duration: 2, repeat: Infinity }}
                        />
                        <motion.path
                            d="M75,100 L125,100 L115,140 L85,140 Z"
                            fill="white"
                            animate={{ opacity: [0.1, 0.4, 0.1] }}
                            transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
                        />

                        <path d="M40,20 L160,20" stroke="currentColor" strokeWidth="2" strokeDasharray="5,5" />
                        <circle cx="100" cy="180" r="4" fill="currentColor" className="animate-pulse" />
                        <text x="100" y="25" fill="white" textAnchor="middle" className="text-[12px] font-bold opacity-30">REVENUE FUNNEL</text>
                    </svg>
                </motion.div>

                {/* 2. Decision Tree Network (Right Center) */}
                <motion.div
                    initial={{ opacity: 0, x: 50 }}
                    animate={{ opacity: 0.15, x: 0 }}
                    transition={{ duration: 2.5 }}
                    className="absolute right-[5%] top-[35%] w-80 h-80"
                >
                    <svg viewBox="0 0 200 200" className="w-full h-full text-blue-400">
                        {/* Root to Branches */}
                        <line x1="100" y1="180" x2="100" y2="100" stroke="currentColor" strokeWidth="2" />
                        <line x1="100" y1="100" x2="40" y2="60" stroke="currentColor" strokeWidth="2" />
                        <line x1="100" y1="100" x2="160" y2="60" stroke="currentColor" strokeWidth="2" />

                        {/* Nodes with synchronized pulses */}
                        <motion.circle cx="100" cy="180" r="6" fill="currentColor" animate={{ r: [6, 8, 6], opacity: [0.5, 1, 0.5] }} transition={{ duration: 3, repeat: Infinity }} />
                        <motion.circle cx="100" cy="100" r="8" fill="currentColor" animate={{ r: [8, 10, 8], opacity: [0.5, 1, 0.5] }} transition={{ duration: 3, repeat: Infinity, delay: 0.5 }} />
                        <motion.circle cx="40" cy="60" r="10" fill="currentColor" stroke="white" strokeWidth="2" animate={{ scale: [1, 1.1, 1] }} transition={{ duration: 3, repeat: Infinity, delay: 1 }} />
                        <motion.circle cx="160" cy="60" r="10" fill="currentColor" stroke="white" strokeWidth="2" animate={{ scale: [1, 1.1, 1] }} transition={{ duration: 3, repeat: Infinity, delay: 1.2 }} />

                        {/* Smaller Leaves */}
                        <path d="M40,60 L20,30 M40,60 L60,30" stroke="currentColor" strokeWidth="1" strokeDasharray="3,2" />
                        <path d="M160,60 L140,30 M160,60 L180,30" stroke="currentColor" strokeWidth="1" strokeDasharray="3,2" />

                        <text x="100" y="150" fill="white" textAnchor="middle" className="text-[10px] font-bold uppercase opacity-50 tracking-tighter">Decision Logic Paths</text>
                    </svg>
                </motion.div>

                {/* 3. Upward Trend / Growth Trajectory (Bottom Right) */}
                <motion.div
                    animate={{ opacity: [0.08, 0.15, 0.08] }}
                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute right-[15%] bottom-[10%] w-96 h-40"
                >
                    <svg viewBox="0 0 400 150" className="w-full h-full text-blue-600">
                        <motion.path
                            d="M10,140 Q50,130 100,100 T200,80 T300,40 T390,10"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="3"
                            strokeDasharray="10,5"
                            animate={{ strokeDashoffset: [0, -40] }}
                            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        />
                        <polygon points="385,15 395,5 400,15" fill="currentColor" />
                        <text x="200" y="130" fill="white" textAnchor="middle" className="text-[10px] font-bold opacity-40">INTELLIGENCE VELOCITY</text>
                    </svg>
                </motion.div>
            </div>

            {/* Floating Signals */}
            {signals.map((signal, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 0 }}
                    animate={{
                        opacity: [0, 0.4, 0.4, 0],
                        y: [-20, -100, -20],
                        x: [0, 20, 0]
                    }}
                    transition={{
                        duration: 10 + i * 2,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: signal.delay
                    }}
                    className="absolute flex items-center gap-3 z-20"
                    style={{ left: signal.x, top: signal.y }}
                >
                    <signal.icon className="w-5 h-5 text-blue-500/60" />
                    <span className="text-[11px] font-mono font-bold text-zinc-500 tracking-[0.2em] uppercase whitespace-nowrap">
                        {signal.text}
                    </span>
                    <div className="w-1.5 h-1.5 bg-blue-500/50 rounded-full animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                </motion.div>
            ))}

            {/* Prominent Radial Core Pulse */}
            <motion.div
                animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.05, 0.08, 0.05]
                }}
                transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-blue-500/10 rounded-full blur-[150px] pointer-events-none z-0"
            />
        </div>
    );
}
