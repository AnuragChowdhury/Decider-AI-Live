"use client";

import { AlertTriangle, AlertCircle, CheckCircle, Zap } from "lucide-react";

interface Anomaly {
    row_index: number;
    column: string;
    value: number;
    z_score: number;
}

function SeverityBadge({ z }: { z: number }) {
    if (Math.abs(z) >= 3) {
        return (
            <span className="flex items-center gap-1 text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded-full text-xs font-medium">
                <AlertTriangle className="w-3 h-3" /> Critical
            </span>
        );
    } else if (Math.abs(z) >= 2) {
        return (
            <span className="flex items-center gap-1 text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full text-xs font-medium">
                <AlertCircle className="w-3 h-3" /> Warning
            </span>
        );
    }
    return (
        <span className="flex items-center gap-1 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full text-xs font-medium">
            <CheckCircle className="w-3 h-3" /> Minor
        </span>
    );
}

export default function AnomalyWidget({
    title,
    data,
    onDrilldown,
}: {
    title: string;
    data: Anomaly[];
    onDrilldown?: (q: string) => void;
}) {
    const anomalies = Array.isArray(data) ? data : [];

    return (
        <div className="bg-zinc-900/50 backdrop-blur-sm border border-red-500/20 p-6 rounded-2xl h-full flex flex-col group hover:bg-zinc-900/70 transition-all">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-white font-semibold flex items-center gap-2">
                    <Zap className="w-4 h-4 text-red-400" />
                    {title}
                </h3>
                <span className="text-[10px] bg-red-500/10 border border-red-500/20 text-red-400 px-2 py-0.5 rounded-full font-medium">
                    {anomalies.length} detected
                </span>
            </div>

            {/* Anomaly list */}
            {anomalies.length === 0 ? (
                <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">
                    No anomalies detected
                </div>
            ) : (
                <div className="flex-1 overflow-auto space-y-2">
                    {anomalies.slice(0, 8).map((anomaly, i) => (
                        <div
                            key={i}
                            className="flex items-center gap-3 bg-white/5 border border-white/5 rounded-xl px-4 py-2.5 hover:border-red-500/30 transition-all group/row"
                        >
                            {/* Row index */}
                            <span className="text-gray-600 text-xs font-mono w-8 shrink-0">
                                #{anomaly.row_index}
                            </span>

                            {/* Column + value */}
                            <div className="flex-1 min-w-0">
                                <span className="text-gray-300 text-sm font-medium truncate block">
                                    {anomaly.column}
                                </span>
                                <span className="text-gray-500 text-xs">
                                    value:{" "}
                                    <span className="text-white font-mono">
                                        {typeof anomaly.value === "number"
                                            ? anomaly.value.toLocaleString()
                                            : anomaly.value}
                                    </span>{" "}
                                    · z={" "}
                                    <span
                                        className={
                                            Math.abs(anomaly.z_score) >= 3
                                                ? "text-red-400"
                                                : "text-amber-400"
                                        }
                                    >
                                        {anomaly.z_score.toFixed(2)}
                                    </span>
                                </span>
                            </div>

                            {/* Severity */}
                            <SeverityBadge z={anomaly.z_score} />

                            {/* Drill button */}
                            {onDrilldown && (
                                <button
                                    onClick={() =>
                                        onDrilldown(
                                            `Explain the anomaly in column "${anomaly.column}" at row ${anomaly.row_index}. The value is ${anomaly.value} which has a z-score of ${anomaly.z_score.toFixed(2)}. What could cause this?`
                                        )
                                    }
                                    className="opacity-0 group-hover/row:opacity-100 text-[10px] bg-blue-500/10 border border-blue-500/30 text-blue-400 px-2 py-1 rounded-lg hover:bg-blue-500/20 transition-all shrink-0"
                                >
                                    Investigate →
                                </button>
                            )}
                        </div>
                    ))}

                    {anomalies.length > 8 && (
                        <p className="text-center text-gray-600 text-xs py-2">
                            + {anomalies.length - 8} more anomalies. Ask the AI
                            Analyst for a full report.
                        </p>
                    )}
                </div>
            )}
        </div>
    );
}
