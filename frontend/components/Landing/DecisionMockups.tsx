import { motion } from "framer-motion";
import { ShieldCheck, AlertCircle, Target, ArrowRight } from "lucide-react";

const recommendations = [
    {
        id: 1,
        title: "Rescue Q4 Slippage",
        type: "CRITICAL",
        metric: "Δ $1.2M",
        desc: "Forecast indicates 12% probability of slippage in APAC region deals. Neural recommendation: Immediate territory reassignment.",
        icon: AlertCircle,
        color: "text-red-400",
        border: "border-red-500/20",
        bg: "bg-red-500/5"
    },
    {
        id: 2,
        title: "Optimize Territory B",
        type: "STRATEGIC",
        metric: "+18% VELOCITY",
        desc: "Autonomous pattern recognition detected untapped pipeline density in Sector 7. Strategy: Deploy Tier-1 Account Executives.",
        icon: Target,
        color: "text-blue-400",
        border: "border-blue-500/20",
        bg: "bg-blue-500/5"
    },
    {
        id: 3,
        title: "Neural Trust Validated",
        type: "VERIFIED",
        metric: "99.2% CONFIDENCE",
        desc: "Forensic audit complete. No data leakage detected in pipeline ingestion. System state: Optimal for strategic execution.",
        icon: ShieldCheck,
        color: "text-emerald-400",
        border: "border-emerald-500/20",
        bg: "bg-emerald-500/5"
    }
];

export default function DecisionMockups() {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-6xl mx-auto py-20 px-4">
            {recommendations.map((rec, i) => (
                <motion.div
                    key={rec.id}
                    initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1 }}
                    whileHover={{ y: -10 }}
                    className={`relative p-8 rounded-3xl border ${rec.border} ${rec.bg} backdrop-blur-xl group cursor-none`}
                >
                    <div className="flex items-center justify-between mb-6">
                        <div className={`text-[10px] font-bold ${rec.color} uppercase tracking-[0.2em]`}>{rec.type}</div>
                        <rec.icon className={`w-5 h-5 ${rec.color}`} />
                    </div>

                    <h3 className="text-2xl font-bold text-white mb-2 leading-tight">{rec.title}</h3>
                    <div className={`text-sm font-mono ${rec.color} mb-4`}>{rec.metric}</div>

                    <p className="text-zinc-400 text-sm leading-relaxed mb-8">
                        {rec.desc}
                    </p>

                    <div className="flex items-center gap-2 text-white text-xs font-bold group-hover:gap-4 transition-all uppercase tracking-widest">
                        Execute Recommendation <ArrowRight className="w-3 h-3" />
                    </div>

                    {/* Glossy Overlay */}
                    <div className="absolute inset-0 rounded-3xl bg-gradient-to-tr from-white/5 to-transparent pointer-events-none" />
                </motion.div>
            ))}
        </div>
    );
}
