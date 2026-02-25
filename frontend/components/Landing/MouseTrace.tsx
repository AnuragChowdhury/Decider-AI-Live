import { useEffect, useState } from "react";
import { motion, useSpring, useMotionValue } from "framer-motion";

export default function MouseTrace() {
    const [isHovering, setIsHovering] = useState(false);
    const cursorX = useMotionValue(-100);
    const cursorY = useMotionValue(-100);

    const springConfig = { damping: 25, stiffness: 500, mass: 0.5 };
    const cursorXSpring = useSpring(cursorX, springConfig);
    const cursorYSpring = useSpring(cursorY, springConfig);

    useEffect(() => {
        const moveCursor = (e: MouseEvent) => {
            cursorX.set(e.clientX);
            cursorY.set(e.clientY);

            // Check if hovering over interactive elements
            const target = e.target as HTMLElement;
            const isClickable =
                target.tagName === 'BUTTON' ||
                target.tagName === 'A' ||
                target.closest('button') ||
                target.closest('a') ||
                window.getComputedStyle(target).cursor === 'pointer';

            setIsHovering(!!isClickable);
        };

        window.addEventListener("mousemove", moveCursor);
        return () => window.removeEventListener("mousemove", moveCursor);
    }, []);

    return (
        <motion.div
            className="fixed top-0 left-0 pointer-events-none z-[9999] hidden md:block"
            style={{
                translateX: cursorXSpring,
                translateY: cursorYSpring,
                x: "-50%",
                y: "-50%"
            }}
        >
            {/* Outer Rotating Brackets */}
            <motion.div
                animate={{
                    rotate: 360,
                    scale: isHovering ? 1.5 : 1
                }}
                transition={{
                    rotate: { duration: 10, repeat: Infinity, ease: "linear" },
                    scale: { type: "spring", stiffness: 300, damping: 20 }
                }}
                className="relative w-12 h-12 flex items-center justify-center"
            >
                {/* 4 Brackets */}
                {[0, 90, 180, 270].map((rotation) => (
                    <div
                        key={rotation}
                        className="absolute w-2 h-2 border-t border-l border-blue-500/50"
                        style={{
                            transform: `rotate(${rotation}deg) translate(-12px, -12px)`,
                        }}
                    />
                ))}
            </motion.div>

            {/* Central Intelligence Dot */}
            <motion.div
                animate={{
                    scale: isHovering ? 0.5 : 1,
                    backgroundColor: isHovering ? "rgb(59, 130, 246)" : "rgb(255, 255, 255)"
                }}
                className="absolute top-1/2 left-1/2 w-1.5 h-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full shadow-[0_0_8px_rgba(59,130,246,0.5)]"
            />

            {/* Scanning Ring */}
            <motion.div
                animate={{
                    scale: [1, 2, 1],
                    opacity: [0.3, 0, 0.3]
                }}
                transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                }}
                className="absolute top-1/2 left-1/2 w-4 h-4 -translate-x-1/2 -translate-y-1/2 border border-blue-400/20 rounded-full"
            />
        </motion.div>
    );
}
