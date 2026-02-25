import { motion } from "framer-motion";

export default function DecisionGrid() {
    // Create a 10x10 grid of intersections
    const nodes = Array.from({ length: 40 }).map((_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        delay: Math.random() * 5,
        duration: 3 + Math.random() * 4
    }));

    return (
        <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-20">
            {/* Grid Lines */}
            <div
                className="absolute inset-0"
                style={{
                    backgroundImage: `linear-gradient(to right, #ffffff11 1px, transparent 1px),
                                    linear-gradient(to bottom, #ffffff11 1px, transparent 1px)`,
                    backgroundSize: '8rem 8rem',
                }}
            />

            {/* Pulsing Neural Nodes */}
            {nodes.map((node) => (
                <motion.div
                    key={node.id}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{
                        opacity: [0, 0.8, 0],
                        scale: [0.5, 1.2, 0.5],
                    }}
                    transition={{
                        duration: node.duration,
                        repeat: Infinity,
                        delay: node.delay,
                        ease: "easeInOut"
                    }}
                    className="absolute w-1.5 h-1.5 bg-blue-500 rounded-full blur-[1px]"
                    style={{
                        left: `${node.x}%`,
                        top: `${node.y}%`,
                        boxShadow: '0 0 8px #3b82f6'
                    }}
                />
            ))}
        </div>
    );
}
