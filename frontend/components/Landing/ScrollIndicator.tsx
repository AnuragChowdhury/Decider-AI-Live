import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";

export default function ScrollIndicator() {
    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1, duration: 1 }}
            className="fixed bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-zinc-500 z-20 pointer-events-none"
        >
            <span className="text-xs uppercase tracking-widest font-light">Scroll</span>
            <motion.div
                animate={{ y: [0, 5, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            >
                <ChevronDown className="w-5 h-5" />
            </motion.div>
        </motion.div>
    );
}
