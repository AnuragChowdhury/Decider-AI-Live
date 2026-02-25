import { motion } from "framer-motion";

export default function Background() {
    return (
        <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
            {/* Deep dark background */}
            <div className="absolute inset-0 bg-zinc-950" />

            {/* Grid Pattern */}
            <div
                className="absolute inset-0 opacity-[0.08]"
                style={{
                    backgroundImage: `linear-gradient(to right, #808080 1px, transparent 1px),
                           linear-gradient(to bottom, #808080 1px, transparent 1px)`,
                    backgroundSize: '4rem 4rem',
                }}
            />

            {/* Animated Gradient Orbs */}
            <motion.div
                animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.4, 0.6, 0.4],
                    x: [0, 20, 0],
                    y: [0, -20, 0],
                }}
                transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-blue-600/30 rounded-full blur-[128px]"
            />

            <motion.div
                animate={{
                    scale: [1, 1.1, 1],
                    opacity: [0.3, 0.5, 0.3],
                    x: [0, -30, 0],
                    y: [0, 30, 0],
                }}
                transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-purple-600/25 rounded-full blur-[128px]"
            />

            {/* Center Glow */}
            <div className="absolute top-[40%] left-[50%] -translate-x-[50%] -translate-y-[50%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[96px]" />

            {/* Noise Overlay (Optional for texture) */}
            <div className="absolute inset-0 opacity-[0.02] mix-blend-overlay"
                style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 200 200\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noiseFilter\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.65\' numOctaves=\'3\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noiseFilter)\'/%3E%3C/svg%3E")' }}
            />
        </div>
    );
}
