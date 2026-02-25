import { motion } from "framer-motion";

const content = [
    {
        title: "Forensic Pipeline Trace",
        text: "Stop guessing where your revenue leaks. Trace every deal from lead to liquidity with autonomous precision."
    },
    {
        title: "Forecast with Neural Certainty",
        text: "Replace gut feeling with data-driven probability. Our agents analyze thousands of signals to predict your quarter end with 98% accuracy."
    },
    {
        title: "Revenue Autonomy",
        text: "Own your data narrative. Identify churn risks and expansion opportunities before they appear on any dashboard."
    }
];

export default function Manifesto() {
    return (
        <section className="min-h-screen py-32 px-4 relative z-10 flex flex-col items-center gap-32">
            {content.map((item, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 40, scale: 0.95 }}
                    whileInView={{ opacity: 1, y: 0, scale: 1 }}
                    viewport={{ margin: "-20%" }}
                    transition={{ duration: 0.8, delay: i * 0.1 }}
                    className="max-w-4xl text-center space-y-6 group"
                >
                    <h2 className="text-4xl md:text-7xl font-bold font-display tracking-tight bg-gradient-to-b from-white to-zinc-600 bg-clip-text text-transparent group-hover:to-zinc-400 transition-colors duration-500 pb-2">
                        {item.title}
                    </h2>
                    <p className="text-xl md:text-3xl text-zinc-400 font-light leading-relaxed max-w-2xl mx-auto group-hover:text-zinc-300 transition-colors duration-500">
                        {item.text}
                    </p>
                </motion.div>
            ))}
        </section>
    );
}
