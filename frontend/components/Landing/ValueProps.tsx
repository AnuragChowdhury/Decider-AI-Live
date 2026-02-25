import { motion } from "framer-motion";
import { Zap, BarChart3, BrainCircuit } from "lucide-react";

export default function ValueProps() {
    return (
        <section className="py-20 border-y border-white/5 bg-zinc-900/20 backdrop-blur-sm">
            <div className="container mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-12">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    className="flex flex-col gap-4"
                >
                    <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                        <Zap className="w-6 h-6 text-blue-400" />
                    </div>
                    <h3 className="text-xl font-bold text-white">Revenue Velocity</h3>
                    <p className="text-zinc-400 text-sm leading-relaxed">
                        Eliminate data latency. Process complex CRM dumps and pipeline exports into actionable insights in seconds.
                    </p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.1 }}
                    className="flex flex-col gap-4"
                >
                    <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center border border-purple-500/20">
                        <BrainCircuit className="w-6 h-6 text-purple-400" />
                    </div>
                    <h3 className="text-xl font-bold text-white">Neural Forecasting</h3>
                    <p className="text-zinc-400 text-sm leading-relaxed">
                        Go beyond simple rollups. Our agents run multi-agent simulations to predict deal slippage and quarter-end outcomes.
                    </p>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2 }}
                    className="flex flex-col gap-4"
                >
                    <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center border border-green-500/20">
                        <BarChart3 className="w-6 h-6 text-green-400" />
                    </div>
                    <h3 className="text-xl font-bold text-white">Actionable Decisions</h3>
                    <p className="text-zinc-400 text-sm leading-relaxed">
                        Don't just look at charts. Decider AI recommends specific actions to rescue at-risk deals and optimize territory allocation.
                    </p>
                </motion.div>
            </div>
        </section>
    );
}
