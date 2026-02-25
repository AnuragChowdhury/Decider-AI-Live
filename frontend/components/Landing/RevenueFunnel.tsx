import { motion } from "framer-motion";
import { Database, Zap, Brain, TrendingUp } from "lucide-react";

const steps = [
    { id: "raw", label: "Raw CRM Output", icon: Database, color: "text-zinc-500", glow: "bg-zinc-500/20" },
    { id: "neural", label: "Neural Fusion", icon: Zap, color: "text-blue-400", glow: "bg-blue-400/20" },
    { id: "forensic", label: "Forensic Audit", icon: Brain, color: "text-purple-400", glow: "bg-purple-400/20" },
    { id: "revenue", label: "Revenue Autonomy", icon: TrendingUp, color: "text-emerald-400", glow: "bg-emerald-400/20" },
];

export default function RevenueFunnel() {
    return (
        <div className="relative w-full max-w-4xl mx-auto py-20 overflow-hidden">
            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-blue-500/5 rounded-full blur-[120px]" />

            <div className="relative flex flex-col items-center gap-8">
                {steps.map((step, i) => (
                    <motion.div
                        key={step.id}
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: i * 0.2, duration: 0.8 }}
                        className="relative flex flex-col items-center"
                    >
                        {/* Connecting Line with Flow */}
                        {i > 0 && (
                            <div className="w-px h-16 bg-gradient-to-b from-transparent via-white/10 to-transparent relative">
                                <motion.div
                                    animate={{ y: [0, 64], opacity: [0, 1, 0] }}
                                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                                    className="absolute top-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-blue-400 rounded-full blur-[1px]"
                                />
                            </div>
                        )}

                        <div className="group relative">
                            <motion.div
                                whileHover={{ scale: 1.05 }}
                                className={`w-20 h-20 rounded-2xl bg-zinc-900/50 border border-white/5 backdrop-blur-md flex items-center justify-center relative z-10 transition-colors group-hover:border-white/10`}
                            >
                                <step.icon className={`w-8 h-8 ${step.color} transition-transform duration-500 group-hover:scale-110`} />
                                <div className={`absolute inset-0 ${step.glow} rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                            </motion.div>

                            {/* Label */}
                            <div className="absolute left-24 top-1/2 -translate-y-1/2 whitespace-nowrap hidden md:block">
                                <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Checkpoint {i + 1}</div>
                                <div className="text-xl font-bold tracking-tight text-white">{step.label}</div>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Geometric Accents */}
            <div className="absolute top-0 right-0 w-64 h-64 border-r border-t border-white/5 rounded-tr-[100px] pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-64 h-64 border-l border-b border-white/5 rounded-bl-[100px] pointer-events-none" />
        </div>
    );
}
