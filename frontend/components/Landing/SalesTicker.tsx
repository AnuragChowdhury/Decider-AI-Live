import { motion } from "framer-motion";

const events = [
    { type: "DATA", msg: "Pipeline Ingested", value: "8.4k nodes", color: "text-blue-400" },
    { type: "DELTA", msg: "Forecast Variance", value: "±2.1%", color: "text-purple-400" },
    { type: "REVENUE", msg: "Deal Lock", value: "$450k", color: "text-emerald-400" },
    { type: "NEURAL", msg: "Slippage Detected", value: "High Prob", color: "text-amber-400" },
    { type: "AUDIT", msg: "Forensic Complete", value: "100% Integrity", color: "text-blue-400" },
    { type: "STRATEGY", msg: "Next Best Action", value: "Resourced", color: "text-indigo-400" }
];

export default function SalesTicker() {
    return (
        <div className="w-full overflow-hidden py-8 border-y border-white/5 bg-zinc-950/50 backdrop-blur-md relative">
            {/* Scanline Effect */}
            <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_50%,rgba(255,255,255,0.02)_50%)] bg-[length:100%_4px] pointer-events-none z-10" />

            <motion.div
                animate={{ x: [0, -1600] }}
                transition={{
                    duration: 30,
                    repeat: Infinity,
                    ease: "linear",
                    repeatType: "loop"
                }}
                className="flex gap-12 whitespace-nowrap"
            >
                {[...events, ...events, ...events].map((event, i) => (
                    <div key={i} className="flex items-center gap-4">
                        <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-white/5 border border-white/10 ${event.color}`}>
                            {event.type}
                        </span>
                        <span className="text-sm font-medium tracking-tight text-zinc-400">
                            {event.msg}:
                        </span>
                        <span className="text-sm font-mono font-bold text-white pr-12">
                            {event.value}
                        </span>
                    </div>
                ))}
            </motion.div>
        </div>
    );
}
