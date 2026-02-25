"use client";

import { Lightbulb, TrendingUp, AlertTriangle, CheckCircle, ChevronRight } from "lucide-react";

interface Recommendation {
    text?: string;
    title?: string;
    priority?: "high" | "medium" | "low";
    type?: string;
}

function priorityIcon(p?: string) {
    if (p === "high") return <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />;
    if (p === "medium") return <TrendingUp className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />;
    return <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />;
}

function priorityBadge(p?: string) {
    if (p === "high") return <span className="text-[9px] bg-red-500/10 border border-red-500/20 text-red-400 px-1.5 py-0.5 rounded-full">High Priority</span>;
    if (p === "medium") return <span className="text-[9px] bg-amber-500/10 border border-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded-full">Medium</span>;
    return <span className="text-[9px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded-full">Insight</span>;
}

export default function RecommendationWidget({
    title,
    data,
    onDrilldown,
}: {
    title: string;
    data: string[] | Recommendation[];
    onDrilldown?: (q: string) => void;
}) {
    // Normalize: data can be string[] or object[]
    const items: Recommendation[] = Array.isArray(data)
        ? data.map((d) =>
            typeof d === "string"
                ? { text: d, priority: "medium" }
                : d
        )
        : [];

    if (items.length === 0) return null;

    return (
        <div className="bg-gradient-to-br from-indigo-950/60 to-zinc-900/60 backdrop-blur-sm border border-indigo-500/20 p-6 rounded-2xl h-full flex flex-col group hover:border-indigo-500/40 transition-all">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-indigo-400" />
                    {title}
                </h3>
                <span className="text-[10px] bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded-full font-medium">
                    {items.length} actions
                </span>
            </div>

            {/* List */}
            <div className="flex-1 space-y-2 overflow-auto">
                {items.slice(0, 6).map((rec, i) => {
                    const text = rec.text || rec.title || String(rec);
                    return (
                        <div
                            key={i}
                            className="flex items-start gap-3 bg-white/5 border border-white/5 rounded-xl px-4 py-3 hover:border-indigo-500/30 hover:bg-indigo-500/5 transition-all group/row cursor-pointer"
                            onClick={() =>
                                onDrilldown &&
                                onDrilldown(
                                    `Based on this recommendation: "${text}" — explain how to implement this, what the expected impact is, and what data evidence supports it.`
                                )
                            }
                        >
                            {/* Priority icon */}
                            {priorityIcon(rec.priority)}

                            {/* Text */}
                            <div className="flex-1 min-w-0">
                                <p className="text-gray-200 text-sm leading-relaxed">{text}</p>
                            </div>

                            <div className="flex items-center gap-2 shrink-0">
                                {priorityBadge(rec.priority)}
                                <ChevronRight className="w-3 h-3 text-gray-600 group-hover/row:text-indigo-400 transition-colors" />
                            </div>
                        </div>
                    );
                })}

                {items.length > 6 && (
                    <p className="text-center text-gray-600 text-xs py-2">
                        + {items.length - 6} more. Ask the AI Analyst for the full strategic report.
                    </p>
                )}
            </div>

            {/* CTA */}
            {onDrilldown && (
                <button
                    onClick={() =>
                        onDrilldown(
                            "Based on the dashboard analysis, what are the top 3 strategic decisions I should make right now? Include specific actions, expected ROI, and timeline."
                        )
                    }
                    className="mt-4 w-full text-center text-xs bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 py-2 rounded-xl hover:bg-indigo-500/20 transition-all font-medium"
                >
                    Ask AI for Full Strategic Report →
                </button>
            )}
        </div>
    );
}
