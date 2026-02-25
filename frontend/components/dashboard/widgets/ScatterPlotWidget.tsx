"use client";

import { ResponsiveScatterPlot } from "@nivo/scatterplot";

const nivoTheme = {
    axis: {
        ticks: { text: { fill: "#9ca3af" } },
        legend: { text: { fill: "#9ca3af" } }
    },
    grid: { line: { stroke: "#333", strokeDasharray: "4 4" } },
    tooltip: {
        container: {
            background: "#18181b",
            color: "#fff",
            border: "1px solid #333"
        }
    }
};

export default function ScatterPlotWidget({
    title,
    data,
    onDrilldown,
    xLabel,
    yLabel,
}: {
    title: string;
    data: any[];
    onDrilldown?: (q: string) => void;
    xLabel?: string;
    yLabel?: string;
}) {
    const safeData = Array.isArray(data) ? data : [];
    if (safeData.length === 0) return null;

    // Nivo scatterplot expects: [{ id: "series", data: [{x: ..., y: ...}] }]
    // If data comes in Nivo line format (same shape), we can use it directly
    let scatterData: any[] = safeData;

    // If flat array like [{x,y} or similar], wrap into series
    if (safeData.length > 0 && !safeData[0].data) {
        scatterData = [{
            id: title,
            data: safeData.map((d: any) => ({
                x: d.x ?? d.date ?? d.label ?? d.category ?? d.month ?? 0,
                y: d.y ?? d.value ?? d.amount ?? d.total ?? d.count ?? 0,
            }))
        }];
    }

    return (
        <div className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl h-full flex flex-col group hover:bg-zinc-900/70 transition-all cursor-pointer">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                {title}
                {onDrilldown && (
                    <span className="text-[10px] bg-orange-500/10 border border-orange-500/20 px-2 py-0.5 rounded text-orange-400 group-hover:bg-orange-500/20 transition-colors">
                        Click point to drill ↓
                    </span>
                )}
            </h3>
            <div className="flex-1 min-h-[300px] w-full">
                <ResponsiveScatterPlot
                    data={scatterData}
                    margin={{ top: 20, right: 30, bottom: 60, left: 60 }}
                    xScale={{ type: "linear", min: "auto", max: "auto" }}
                    yScale={{ type: "linear", min: "auto", max: "auto" }}
                    blendMode="multiply"
                    axisTop={null}
                    axisRight={null}
                    axisBottom={{
                        tickSize: 5,
                        tickPadding: 5,
                        tickRotation: -30,
                        legend: xLabel ?? "X",
                        legendOffset: 46,
                        legendPosition: "middle",
                        format: (v: any) => new Intl.NumberFormat("en-US", { notation: "compact" }).format(v),
                    }}
                    axisLeft={{
                        tickSize: 5,
                        tickPadding: 5,
                        tickRotation: 0,
                        legend: yLabel ?? "Y",
                        legendOffset: -50,
                        legendPosition: "middle",
                        format: (v: any) => new Intl.NumberFormat("en-US", { notation: "compact" }).format(v),
                    }}
                    colors={{ scheme: "orange_red" }}
                    nodeSize={9}
                    useMesh={false}
                    onClick={(node: any) => {
                        if (onDrilldown) {
                            const query = `In the "${title}" scatter chart, what is the significance of the data point at (${node.xValue}, ${node.yValue})? What correlation does this suggest?`;
                            onDrilldown(query);
                        }
                    }}
                    theme={nivoTheme}
                    tooltip={({ node }: any) => (
                        <div className="bg-zinc-800 border border-white/10 rounded px-3 py-2 text-sm text-white shadow-lg">
                            <div><strong>{node.serieId}</strong></div>
                            <div>x: {node.xValue?.toLocaleString()}</div>
                            <div>y: {node.yValue?.toLocaleString()}</div>
                        </div>
                    )}
                />
            </div>
        </div>
    );
}
