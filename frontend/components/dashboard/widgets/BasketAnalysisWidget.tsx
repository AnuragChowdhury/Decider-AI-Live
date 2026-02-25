"use client";

import { motion } from "framer-motion";
import { ShoppingCart, ArrowRight, TrendingUp } from "lucide-react";

interface BasketRule {
    antecedents: string[];
    consequents: string[];
    confidence: number;
    lift: number;
}

interface Props {
    title?: string;
    subtitle?: string;
    data?: BasketRule[];
}

function LiftBadge({ lift }: { lift: number }) {
    const color =
        lift >= 2.5 ? "text-emerald-300 bg-emerald-500/10 border-emerald-500/30" :
            lift >= 1.5 ? "text-blue-300   bg-blue-500/10   border-blue-500/30" :
                "text-yellow-300  bg-yellow-500/10  border-yellow-500/30";
    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${color}`}>
            <TrendingUp className="w-3 h-3" />
            {lift.toFixed(2)}×
        </span>
    );
}

function ConfidenceBar({ confidence }: { confidence: number }) {
    const pct = Math.round(confidence * 100);
    return (
        <div className="flex items-center gap-2 min-w-[80px]">
            <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                    className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                />
            </div>
            <span className="text-xs text-gray-400 w-8 text-right">{pct}%</span>
        </div>
    );
}

export default function BasketAnalysisWidget({ title = "Market Basket Analysis", subtitle, data }: Props) {
    const rules: BasketRule[] = Array.isArray(data)
        ? (data as any[])
            .filter(d => d && d.antecedents && d.consequents)
            .map(d => ({
                antecedents: Array.isArray(d.antecedents) ? d.antecedents : [d.antecedents],
                consequents: Array.isArray(d.consequents) ? d.consequents : [d.consequents],
                confidence: Number(d.confidence ?? 0),
                lift: Number(d.lift ?? 0),
            }))
        : [];

    if (rules.length === 0) return null;

    return (
        <div className="w-full rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-6 space-y-4">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
                    <ShoppingCart className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                    <h3 className="text-sm font-semibold text-white">{title}</h3>
                    <p className="text-xs text-gray-500">
                        {subtitle || `${rules.length} product association rules · Lift > 1.0 indicates genuine co-purchase signal`}
                    </p>
                </div>
            </div>

            {/* Column headers */}
            <div className="grid grid-cols-[1fr_auto_1fr_90px_64px] gap-3 px-2 text-[11px] font-medium text-gray-500 uppercase tracking-wide">
                <span>If customer buys…</span>
                <span />
                <span>They also buy</span>
                <span>Confidence</span>
                <span className="text-right">Lift</span>
            </div>

            {/* Rules */}
            <div className="space-y-1.5">
                {rules.map((rule, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.04, duration: 0.3 }}
                        className="grid grid-cols-[1fr_auto_1fr_90px_64px] items-center gap-3 px-3 py-2.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/5 transition-colors group"
                    >
                        {/* Antecedent */}
                        <span className="text-sm text-white font-medium truncate" title={rule.antecedents.join(", ")}>
                            {rule.antecedents.join(", ")}
                        </span>

                        {/* Arrow */}
                        <ArrowRight className="w-3.5 h-3.5 text-indigo-400 shrink-0" />

                        {/* Consequent */}
                        <span className="text-sm text-indigo-300 font-medium truncate" title={rule.consequents.join(", ")}>
                            {rule.consequents.join(", ")}
                        </span>

                        {/* Confidence bar */}
                        <ConfidenceBar confidence={rule.confidence} />

                        {/* Lift badge */}
                        <div className="flex justify-end">
                            <LiftBadge lift={rule.lift} />
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Legend */}
            <div className="flex flex-wrap gap-4 pt-1 border-t border-white/5 text-[11px] text-gray-500">
                <span><span className="text-emerald-400 font-semibold">≥2.5×</span> lift — strong signal</span>
                <span><span className="text-blue-400 font-semibold">1.5–2.5×</span> — moderate signal</span>
                <span><span className="text-yellow-400 font-semibold">&lt;1.5×</span> — weak but notable</span>
                <span className="ml-auto">Confidence = P(B|A)</span>
            </div>
        </div>
    );
}
