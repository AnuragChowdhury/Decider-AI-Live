"use client";

import { ResponsiveRadialBar } from "@nivo/radial-bar";

/**
 * RadialBarWidget — "Radial Column Chart"
 *
 * Uses @nivo/radial-bar to render a polar/circular bar chart.
 * Great for categorical comparisons where you want a visual alternative
 * to a regular bar chart with an eye-catching circular layout.
 *
 * Expected data format:
 *   [{id: "Category", value: 1234}, ...] (same as pie/bar)
 * Internally transformed to Nivo radial-bar format:
 *   [{ id: "Category", data: [{ x: "value", y: 1234 }] }]
 */
export default function RadialBarWidget({
    title,
    data,
    onDrilldown,
}: {
    title: string;
    data: any[];
    onDrilldown?: (q: string) => void;
}) {
    const rawData: any[] = Array.isArray(data) ? data : [];

    // Transform [{id, value}] → Nivo radial-bar format
    const radialData = rawData.map((row: any) => ({
        id: String(row.id ?? row.label ?? row.name ?? row.x ?? ""),
        data: [{ x: "value", y: typeof row.value === "number" ? row.value : Number(row.y ?? 0) }],
    }));

    const isEmpty = radialData.length === 0;

    return (
        <div
            className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl h-full flex flex-col group hover:bg-zinc-900/70 transition-all cursor-pointer"
            onClick={() => {
                if (onDrilldown && !isEmpty) {
                    const topId = radialData[0]?.id;
                    onDrilldown(
                        `In "${title}", ${topId} has the highest value. Why? What actions should we take?`
                    );
                }
            }}
        >
            <h3 className="text-white font-semibold mb-4">{title}</h3>
            <div className="flex-1 min-h-[300px] w-full">
                {isEmpty ? (
                    <div className="flex items-center justify-center h-full text-zinc-500 text-sm">
                        No data available
                    </div>
                ) : (
                    <ResponsiveRadialBar
                        data={radialData}
                        valueFormat=">-.2f"
                        padding={0.4}
                        cornerRadius={4}
                        margin={{ top: 30, right: 80, bottom: 30, left: 80 }}
                        radialAxisStart={{ tickSize: 5, tickPadding: 5, tickRotation: 0 }}
                        circularAxisOuter={{ tickSize: 5, tickPadding: 8, tickRotation: 0 }}
                        colors={{ scheme: "nivo" }}
                        enableTracks={true}
                        tracksColor="rgba(255,255,255,0.06)"
                        enableRadialGrid={true}
                        enableCircularGrid={false}
                        legends={[
                            {
                                anchor: "right",
                                direction: "column",
                                justify: false,
                                translateX: 70,
                                translateY: 0,
                                itemsSpacing: 6,
                                itemWidth: 60,
                                itemHeight: 14,
                                itemTextColor: "#9ca3af",
                                symbolSize: 10,
                                symbolShape: "circle",
                            },
                        ]}
                        tooltip={({ bar }: any) => (
                            <div
                                style={{
                                    background: "#18181b",
                                    border: "1px solid #333",
                                    padding: "6px 10px",
                                    borderRadius: 6,
                                    color: "#fff",
                                    fontSize: 12,
                                }}
                            >
                                <strong>{bar.category}</strong>:{" "}
                                {typeof bar.value === "number"
                                    ? bar.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
                                    : bar.value}
                            </div>
                        )}
                        theme={{
                            axis: {
                                ticks: { text: { fill: "#9ca3af", fontSize: 11 } },
                            },
                            grid: { line: { stroke: "#2d2d2d", strokeDasharray: "4 4" } },
                            legends: { text: { fill: "#9ca3af" } },
                            labels: { text: { fill: "#e5e7eb", fontSize: 11 } },
                        }}
                    />
                )}
            </div>
        </div>
    );
}
