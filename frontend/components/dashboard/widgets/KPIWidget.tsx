"use client";

import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";

export default function KPIWidget({ title, subtitle, description, value, change, trend = "neutral", data }: { title: string, subtitle?: string, description?: string, value?: string | number, change?: string, trend?: "up" | "down" | "neutral", data?: any }) {

    // Fallback: If 'data' is provided (from DashboardRenderer), try to extract value
    const finalValue = value ?? data?.value ?? data?.amount ?? 0;
    const finalChange = change ?? data?.change;
    const finalTrend = trend ?? data?.trend ?? "neutral";
    const finalDesc = description ?? data?.description;
    const finalSubs = subtitle ?? data?.subtitle;

    const getTrendIcon = () => {
        switch (finalTrend) {
            case "up": return <ArrowUpRight className="w-4 h-4 text-green-500" />;
            case "down": return <ArrowDownRight className="w-4 h-4 text-red-500" />;
            default: return <Minus className="w-4 h-4 text-gray-500" />;
        }
    };

    const getTrendColor = () => {
        switch (finalTrend) {
            case "up": return "text-green-500";
            case "down": return "text-red-500";
            default: return "text-gray-500";
        }
    };

    // Format value if number
    const displayValue = typeof finalValue === 'number'
        ? new Intl.NumberFormat('en-US', { notation: "compact", maximumFractionDigits: 1 }).format(finalValue)
        : finalValue;

    return (
        <div className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl flex flex-col justify-between h-full hover:bg-zinc-900/70 transition-colors">
            <div>
                <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-1">{title}</h3>
                {finalSubs && <p className="text-zinc-500 text-xs mb-2">{finalSubs}</p>}

                <div className="flex items-end justify-between mt-2">
                    <div className="text-3xl font-bold text-white tracking-tight">{displayValue}</div>
                    {finalChange && (
                        <div className={`flex items-center gap-1 text-xs font-medium ${getTrendColor()}`}>
                            {getTrendIcon()}
                            {finalChange}
                        </div>
                    )}
                </div>
            </div>

            {finalDesc && (
                <p className="text-zinc-400 text-xs mt-4 leading-relaxed border-t border-white/5 pt-4 italic">
                    {finalDesc}
                </p>
            )}
        </div>
    );
}
