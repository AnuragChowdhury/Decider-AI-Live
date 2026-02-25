import { motion } from "framer-motion";

const metrics = [
    { text: "$1.2M", x: "10%", y: "20%", duration: 15 },
    { text: "98.2% CONFIDENCE", x: "85%", y: "15%", duration: 18 },
    { text: "FORECAST LOCK", x: "75%", y: "80%", duration: 12 },
    { text: "PIPELINE Δ", x: "5%", y: "70%", duration: 20 },
    { text: "NEURAL SYNC", x: "40%", y: "10%", duration: 25 },
    { text: "REVENUE AUTONOMY", x: "60%", y: "90%", duration: 22 },
];

export default function ImpactFloaters() {
    return (
        <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
            {metrics.map((metric, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0 }}
                    animate={{
                        y: [0, -40, 0],
                        opacity: [0, 0.1, 0]
                    }}
                    transition={{
                        duration: metric.duration,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: i * 2
                    }}
                    className="absolute font-mono font-bold text-white text-4xl md:text-6xl tracking-tighter"
                    style={{ left: metric.x, top: metric.y }}
                >
                    {metric.text}
                </motion.div>
            ))}
        </div>
    );
}
