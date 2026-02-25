"use client";

import { ResponsiveFunnel } from "@nivo/funnel";

const nivoTheme = {
    tooltip: {
        container: {
            background: "#18181b",
            color: "#fff",
            border: "1px solid #333"
        }
    },
    labels: { text: { fill: "#e5e7eb" } }
};

export default function FunnelWidget({
    title,
    data,
    onDrilldown,
}: {
    title: string;
    data: any[];
    onDrilldown?: (q: string) => void;
}) {
    const safeData = Array.isArray(data) ? data : [];
    if (safeData.length === 0) return null;

    // Nivo Funnel expects: [{id, value, label}]
    const funnelData = safeData.map((d: any, i: number) => ({
        id: d.id ?? d.label ?? d.category ?? d.name ?? `step_${i}`,
        value: d.value ?? d.count ?? d.total ?? 0,
        label: d.label ?? d.id ?? d.category ?? d.name ?? `Step ${i + 1}`,
    }));

    return (
        <div className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl h-full flex flex-col group hover:bg-zinc-900/70 transition-all cursor-pointer">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                {title}
                {onDrilldown && (
                    <span className="text-[10px] bg-pink-500/10 border border-pink-500/20 px-2 py-0.5 rounded text-pink-400 group-hover:bg-pink-500/20 transition-colors">
                        Click stage to drill ↓
                    </span>
                )}
            </h3>
            <div className="flex-1 min-h-[300px] w-full">
                <ResponsiveFunnel
                    data={funnelData}
                    margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                    valueFormat=">-.0f"
                    colors={{ scheme: "pink_yellowGreen" }}
                    borderWidth={20}
                    labelColor={{ from: "color", modifiers: [["darker", 3]] }}
                    beforeSeparatorLength={100}
                    beforeSeparatorOffset={20}
                    afterSeparatorLength={100}
                    afterSeparatorOffset={20}
                    currentPartSizeExtension={10}
                    currentBorderWidth={40}
                    motionConfig="wobbly"
                    theme={nivoTheme}
                    onClick={(part: any) => {
                        if (onDrilldown) {
                            const query = `In the "${title}" funnel, the "${part.data.label}" stage has ${part.data.value?.toLocaleString()} items. What is causing drop-off here and how can conversion be improved?`;
                            onDrilldown(query);
                        }
                    }}
                    tooltip={({ part }: any) => (
                        <div className="bg-zinc-800 border border-white/10 rounded px-3 py-2 text-sm text-white shadow-lg">
                            <strong>{part.data.label}</strong>
                            <div>Value: {part.data.value?.toLocaleString()}</div>
                        </div>
                    )}
                />
            </div>
        </div>
    );
}
