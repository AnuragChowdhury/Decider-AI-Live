import { motion } from "framer-motion";
import { ShieldCheck, Server, Lock, EyeOff } from "lucide-react";

const features = [
    {
        icon: Server,
        title: "Local Processing",
        desc: "Your raw CSV data is processed locally on your server. It never leaves your infrastructure."
    },
    {
        icon: EyeOff,
        title: "Privacy First",
        desc: "AI only sees de-identified metadata and aggregates. No PII is shared with LLMs."
    },
    {
        icon: Lock,
        title: "No Training",
        desc: "Your data is strictly used for analysis and never used to train our AI models."
    },
    {
        icon: ShieldCheck,
        title: "Audit Ready",
        desc: "Full transparency logs show exactly what data was sent to the AI for each query."
    }
];

export default function TrustSection() {
    return (
        <section className="py-24 relative">
            <div className="container mx-auto px-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="text-center max-w-2xl mx-auto mb-16"
                >
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent mb-4">
                        Enterprise-Grade Security
                    </h2>
                    <p className="text-zinc-400">
                        Built on a "Privacy-First Hybrid Architecture" designed for sensitive financial and customer data.
                    </p>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {features.map((feature, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: idx * 0.1 }}
                            className="bg-zinc-900/50 border border-white/5 p-6 rounded-2xl hover:border-blue-500/20 transition-colors group"
                        >
                            <div className="w-12 h-12 bg-zinc-800 rounded-xl flex items-center justify-center mb-4 group-hover:bg-blue-500/10 transition-colors">
                                <feature.icon className="w-6 h-6 text-zinc-400 group-hover:text-blue-400 transition-colors" />
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                            <p className="text-sm text-zinc-400 leading-relaxed">
                                {feature.desc}
                            </p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
