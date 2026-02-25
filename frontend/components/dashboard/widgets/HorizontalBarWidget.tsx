"use client";

import { ResponsiveBar } from "@nivo/bar";

const nivoTheme = {
    axis: {
        ticks: { text: { fill: "#9ca3af" } },
        legend: { text: { fill: "#9ca3af" } }
    },
    grid: { line: { stroke: "#333" } },
    tooltip: {
        container: {
            background: "#18181b",
            color: "#fff",
            border: "1px solid #333"
        }
    }
};

export default function HorizontalBarWidget({
    title,
    data = [],
    xKey = "id",
    yKey = "value",
    onDrilldown,
}: {
    title: string;
    data: any[];
    xKey?: string;
    yKey?: string;
    onDrilldown?: (q: string) => void;
}) {
    const safeData = Array.isArray(data) ? data : [];

    return (
        <div className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl h-full flex flex-col group hover:bg-zinc-900/70 transition-all cursor-pointer">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                {title}
                {onDrilldown && (
                    <span className="text-[10px] bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded text-emerald-400 group-hover:bg-emerald-500/20 transition-colors">
                        Click bar to drill ↓
                    </span>
                )}
            </h3>
            <div className="flex-1 min-h-[300px] w-full">
                <ResponsiveBar
                    data={safeData}
                    keys={[yKey]}
                    indexBy={xKey}
                    layout="horizontal"
                    margin={{ top: 10, right: 80, bottom: 30, left: 120 }}
                    padding={0.3}
                    valueScale={{ type: "linear" }}
                    indexScale={{ type: "band", round: true }}
                    colors={{ scheme: "green_blue" }}
                    theme={nivoTheme}
                    borderColor={{ from: "color", modifiers: [["darker", 1.6]] }}
                    axisTop={null}
                    axisRight={null}
                    axisBottom={{
                        tickSize: 5,
                        tickPadding: 5,
                        tickRotation: 0,
                        legend: yKey,
                        legendPosition: "middle",
                        legendOffset: 32,
                        format: (v: any) => new Intl.NumberFormat("en-US", { notation: "compact" }).format(v),
                    }}
                    axisLeft={{
                        tickSize: 5,
                        tickPadding: 5,
                        tickRotation: 0,
                        format: (v: any) => `${v}`.length > 14 ? `${v}`.slice(0, 13) + "…" : v,
                    }}
                    enableGridY={false}
                    enableGridX={true}
                    labelSkipWidth={32}
                    labelSkipHeight={12}
                    labelTextColor={{ from: "color", modifiers: [["darker", 1.6]] }}
                    valueFormat={(v) =>
                        new Intl.NumberFormat("en-US", { notation: "compact", compactDisplay: "short" }).format(v)
                    }
                    onClick={(node) => {
                        if (onDrilldown) {
                            const query = `In the "${title}" ranking, why does "${node.indexValue}" have a value of ${node.value?.toLocaleString()}? What drives this result and how can it improve?`;
                            onDrilldown(query);
                        }
                    }}
                    role="application"
                    ariaLabel={title}
                />
            </div>
        </div>
    );
}
