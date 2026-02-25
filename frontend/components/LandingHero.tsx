"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

export default function LandingHero() {
    return (
        <section className="h-screen w-full flex flex-col items-center justify-center bg-black text-white overflow-hidden relative">

            {/* Background Gradient Blob */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none" />

            <div className="z-10 text-center px-4 max-w-4xl mx-auto space-y-8">

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                >
                    <span className="inline-block py-1 px-3 rounded-full bg-white/10 border border-white/20 text-sm font-medium backdrop-blur-md mb-6">
                        ✨ The AI CFO for E-commerce
                    </span>
                    <h1 className="text-5xl md:text-7xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60">
                        Stop guessing. <br />
                        Start deciding.
                    </h1>
                </motion.div>

                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
                    className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed"
                >
                    Drop your sales data. Get instant RFM segmentation, inventory forecasts, and smart basket analysis. No setup required.
                </motion.p>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
                    className="flex flex-col sm:flex-row items-center justify-center gap-4"
                >
                    <Link href="/workspace">
                        <button className="group relative px-8 py-4 bg-white text-black rounded-full font-semibold text-lg hover:bg-gray-200 transition-all flex items-center gap-2">
                            Launch Workspace
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </button>
                    </Link>

                    <button className="px-8 py-4 rounded-full font-semibold text-lg text-white border border-white/20 hover:bg-white/10 transition-all">
                        View Demo
                    </button>
                </motion.div>
            </div>

            {/* Footer / Social Proof */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.0, duration: 1 }}
                className="absolute bottom-10 left-0 right-0 text-center"
            >
                <p className="text-sm text-gray-500 uppercase tracking-widest font-mono">
                    Powered by Decider AI Intelligence
                </p>
            </motion.div>

        </section>
    );
}
