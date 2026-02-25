import { motion } from "framer-motion";

export default function StrategicScanner() {
    return (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
            {/* Horizontal Scanning Bar */}
            <motion.div
                animate={{
                    top: ["-10%", "110%"],
                    opacity: [0, 1, 1, 0]
                }}
                transition={{
                    duration: 8,
                    repeat: Infinity,
                    ease: "linear"
                }}
                className="absolute left-0 w-full h-32 bg-gradient-to-b from-transparent via-blue-500/10 to-transparent z-10"
            >
                {/* Bright Edge */}
                <div className="absolute top-1/2 left-0 w-full h-[1px] bg-blue-400/30 blur-[2px]" />
            </motion.div>

            {/* Occasional Digital "Glitches" */}
            <motion.div
                animate={{
                    opacity: [0, 0.2, 0, 0.1, 0],
                    x: ["-5%", "5%", "-2%", "2%", "0%"]
                }}
                transition={{
                    duration: 0.5,
                    repeat: Infinity,
                    repeatDelay: 4,
                    ease: "linear"
                }}
                className="absolute inset-0 bg-blue-500/5 mix-blend-overlay"
            />
        </div>
    );
}
