import { useState } from "react";
import { ArrowRight, Check, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function EmailForm() {
    const [email, setEmail] = useState("");
    const [status, setStatus] = useState<"idle" | "loading" | "success">("idle");

    // TODO: PASTE YOUR GOOGLE APPS SCRIPT WEB APP URL HERE
    const GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwMafq4dfhmj4CswLU31KaZybUoIFHF7ajU5jcEk2d-ahedkmx108-CqGwI7tnPk-xp/exec";

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email) return;
        setStatus("loading");

        try {
            await fetch(GOOGLE_SCRIPT_URL, {
                method: "POST",
                mode: "no-cors",
                headers: { "Content-Type": "text/plain;charset=utf-8" },
                body: JSON.stringify({ email }),
            });
            setStatus("success");
            setEmail("");
        } catch (error) {
            console.error("Error submitting email", error);
            alert("Something went wrong. Please try again.");
            setStatus("idle");
        }
    };

    return (
        <div className="w-full relative z-20">
            <AnimatePresence mode="wait">
                {status === "success" ? (
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-2xl flex items-center justify-center gap-3 backdrop-blur-md"
                    >
                        <div className="bg-emerald-500/20 p-1.5 rounded-full">
                            <Check className="w-4 h-4" />
                        </div>
                        <span className="font-medium tracking-wide">You're on the list. We'll be in touch.</span>
                    </motion.div>
                ) : (
                    <motion.form
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        onSubmit={handleSubmit}
                        className="group relative flex flex-col sm:flex-row items-stretch gap-2 bg-white/5 p-1.5 rounded-2xl border border-white/10 hover:border-white/20 focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/50 transition-all duration-300 shadow-2xl backdrop-blur-xl w-full"
                    >
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Enter your email address..."
                            className="flex-1 bg-transparent border-none outline-none text-white px-4 py-3 placeholder:text-zinc-500 focus:ring-0 text-base w-full min-w-0"
                            disabled={status === "loading"}
                            required
                        />
                        <button
                            type="submit"
                            disabled={status === "loading"}
                            className="bg-white text-black hover:bg-zinc-200 px-6 py-3 rounded-xl font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 disabled:hover:scale-100 flex items-center justify-center gap-2 whitespace-nowrap shadow-lg shadow-white/5 w-full sm:w-auto"
                        >
                            {status === "loading" ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    Join
                                    <ArrowRight className="w-4 h-4" />
                                </>
                            )}
                        </button>
                    </motion.form>
                )}
            </AnimatePresence>
            <p className="text-zinc-600 text-xs text-center mt-4">
                Join <span className="text-zinc-400">2,000+</span> data leaders waiting for the revolution.
            </p>
        </div>
    );
}
