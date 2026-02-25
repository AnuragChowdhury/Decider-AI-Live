"use client";

import { ResponsiveBar } from "@nivo/bar";

// Mock data removed. Component should handle empty data gracefully or not render.
const defaultData: any[] = [];

export default function BarChartWidget({ title, data = defaultData, xKey = "id", yKey = "value", onDrilldown }: { title: string, data: any[], xKey?: string, yKey?: string, onDrilldown?: (q: string) => void }) {
    return (
        <div className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl h-full flex flex-col group hover:bg-zinc-900/70 transition-all cursor-pointer">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                {title}
                {onDrilldown && (
                    <span className="text-[10px] bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded text-blue-400 group-hover:bg-blue-500/20 transition-colors">
                        Click bar to drill ↓
                    </span>
                )}
            </h3>
            <div className="flex-1 min-h-[300px] w-full">
                <ResponsiveBar
                    data={Array.isArray(data) ? data : []}
                    onClick={(node) => {
                        if (onDrilldown) {
                            const query = `In the "${title}" chart, why does "${node.indexValue}" have a ${yKey} of ${node.value?.toLocaleString()}? What are the key factors driving this? Provide actionable insights.`;
                            onDrilldown(query);
                        }
                    }}

                    keys={[yKey]}
                    indexBy={xKey}
                    margin={{ top: 10, right: 10, bottom: 50, left: 60 }}
                    padding={0.3}
                    valueScale={{ type: 'linear' }}
                    indexScale={{ type: 'band', round: true }}
                    colors={{ scheme: 'nivo' }} // Or custom theme colors
                    theme={{
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
                    }}
                    borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
                    axisTop={null}
                    axisRight={null}
                    axisBottom={{
                        tickSize: 5,
                        tickPadding: 5,
                        tickRotation: 0,
                        legend: xKey,
                        legendPosition: 'middle',
                        legendOffset: 32
                    }}
                    axisLeft={{
                        tickSize: 5,
                        tickPadding: 5,
                        tickRotation: 0,
                        legend: yKey,
                        legendPosition: 'middle',
                        legendOffset: -40
                    }}
                    labelSkipWidth={12}
                    labelSkipHeight={12}
                    labelTextColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
                    role="application"
                    ariaLabel={title}
                    valueFormat={(v) => new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(v)}
                />
            </div>
        </div>
    );
}
