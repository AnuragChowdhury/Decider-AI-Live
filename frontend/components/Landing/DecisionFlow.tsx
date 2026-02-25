import { motion } from "framer-motion";

const branches = [
    { id: 1, d: "M 100 200 L 200 200 L 250 150 L 350 150", label: "YES", delay: 0 },
    { id: 2, d: "M 200 200 L 250 250 L 350 250", label: "NO", delay: 2 },
    { id: 3, d: "M 350 150 L 450 150", label: "RESOLVE", delay: 1.5 },
    { id: 4, d: "M 350 250 L 450 250", label: "RETRY", delay: 3.5 },
];

export default function DecisionFlow() {
    return (
        <div className="absolute inset-0 pointer-events-none opacity-20 overflow-hidden">
            <svg className="w-full h-full" viewBox="0 0 1000 1000" preserveAspectRatio="none">
                <defs>
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {branches.map((branch) => (
                    <g key={branch.id} filter="url(#glow)">
                        {/* Static Path Shadow */}
                        <path
                            d={branch.d}
                            fill="none"
                            stroke="white"
                            strokeWidth="1"
                            strokeOpacity="0.05"
                        />

                        {/* Animated Flow Path */}
                        <motion.path
                            d={branch.d}
                            fill="none"
                            stroke="rgba(59, 130, 246, 0.5)"
                            strokeWidth="2"
                            initial={{ pathLength: 0, opacity: 0 }}
                            animate={{
                                pathLength: [0, 1, 1],
                                opacity: [0, 1, 0]
                            }}
                            transition={{
                                duration: 4,
                                repeat: Infinity,
                                delay: branch.delay,
                                ease: "easeInOut"
                            }}
                        />

                        {/* Logic Node */}
                        <motion.circle
                            cx={branch.d.split(' ')[1]}
                            cy={branch.d.split(' ')[2]}
                            r="3"
                            fill="#3b82f6"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: [0, 1, 0] }}
                            transition={{
                                duration: 4,
                                repeat: Infinity,
                                delay: branch.delay
                            }}
                        />

                        {/* Branch Label */}
                        <motion.text
                            x={parseInt(branch.d.split(' ')[1]) + 10}
                            y={parseInt(branch.d.split(' ')[2]) - 10}
                            fill="white"
                            fontSize="8"
                            fontWeight="bold"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: [0, 0.5, 0] }}
                            transition={{
                                duration: 4,
                                repeat: Infinity,
                                delay: branch.delay
                            }}
                            className="font-mono uppercase tracking-widest"
                        >
                            {branch.label}
                        </motion.text>
                    </g>
                ))}
            </svg>
        </div>
    );
}
