"use client";

import { ResponsiveLine } from "@nivo/line";

/**
 * SlopeChartWidget
 *
 * A slope chart visualises the change between exactly two periods (start → end).
 * It takes the same [{x, y}] data as LineChartWidget but collapses the series
 * to just the FIRST and LAST data-point, then renders large labelled dots
 * connected by bold lines — the classic "slope graph" style.
 *
 * If the incoming data already has only 2 points, it's used as-is.
 */
export default function SlopeChartWidget({
    title,
    data,
    onDrilldown,
}: {
    title: string;
    data: any[];
    onDrilldown?: (q: string) => void;
}) {
    // data is Nivo-line format: [{ id, data: [{x, y}, ...] }]
    const nivoData: any[] = Array.isArray(data) ? data : [];

    // Collapse each series to first + last point
    const slopeData = nivoData.map((series: any) => {
        const pts: any[] = Array.isArray(series.data) ? series.data : [];
        if (pts.length <= 2) return series; // already 2 or fewer
        return {
            ...series,
            data: [pts[0], pts[pts.length - 1]],
        };
    });

    // Compute % change for subtitle
    let changeLabel = "";
    if (slopeData.length > 0 && Array.isArray(slopeData[0].data) && slopeData[0].data.length === 2) {
        const [start, end] = slopeData[0].data;
        if (start?.y && end?.y) {
            const pct = (((end.y - start.y) / Math.abs(start.y)) * 100).toFixed(1);
            const arrow = Number(pct) >= 0 ? "↑" : "↓";
            const color = Number(pct) >= 0 ? "#22c55e" : "#ef4444";
            changeLabel = `${arrow} ${Math.abs(Number(pct))}% from ${start.x} to ${end.x}`;
        }
    }

    return (
        <div className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl h-full flex flex-col group hover:bg-zinc-900/70 transition-all cursor-pointer">
            <div className="mb-4">
                <h3 className="text-white font-semibold">{title}</h3>
                {changeLabel && (
                    <p className="text-xs text-zinc-400 mt-0.5">{changeLabel}</p>
                )}
            </div>
            <div className="flex-1 min-h-[300px] w-full">
                <ResponsiveLine
                    data={slopeData}
                    onClick={(point: any) => {
                        if (onDrilldown) {
                            const q = `In "${title}", what caused the value to change to ${point.data.y?.toLocaleString()} at ${point.data.x}?`;
                            onDrilldown(q);
                        }
                    }}
                    margin={{ top: 40, right: 80, bottom: 60, left: 80 }}
                    xScale={{ type: "point" }}
                    yScale={{ type: "linear", min: "auto", max: "auto", stacked: false }}
                    yFormat=">-.2f"
                    /* Straight lines — the defining slope chart aesthetic */
                    curve="linear"
                    lineWidth={3}
                    /* Large, labelled dots */
                    pointSize={14}
                    pointColor={{ theme: "background" }}
                    pointBorderWidth={3}
                    pointBorderColor={{ from: "serieColor" }}
                    pointLabelYOffset={-16}
                    enablePointLabel={true}
                    pointLabel={(pt: any) => {
                        const v = pt.data?.y;
                        if (typeof v === "number") {
                            return v >= 1000
                                ? `${(v / 1000).toFixed(1)}k`
                                : `${v.toFixed(0)}`;
                        }
                        return String(v ?? "");
                    }}
                    useMesh={true}
                    axisTop={null}
                    axisRight={{
                        tickSize: 0,
                        tickPadding: 8,
                        tickRotation: 0,
                    }}
                    axisBottom={{
                        tickSize: 0,
                        tickPadding: 10,
                        tickRotation: 0,
                    }}
                    axisLeft={{
                        tickSize: 0,
                        tickPadding: 8,
                        format: (v: number) =>
                            v >= 1_000_000
                                ? `${(v / 1_000_000).toFixed(1)}M`
                                : v >= 1000
                                    ? `${(v / 1000).toFixed(0)}k`
                                    : `${v}`,
                    }}
                    enableGridX={true}
                    enableGridY={false}
                    colors={{ scheme: "category10" }}
                    legends={[
                        {
                            anchor: "top-right",
                            direction: "column",
                            itemWidth: 100,
                            itemHeight: 18,
                            symbolSize: 10,
                            symbolShape: "circle",
                            itemTextColor: "#9ca3af",
                        },
                    ]}
                    theme={{
                        axis: {
                            ticks: { text: { fill: "#9ca3af", fontSize: 12 } },
                        },
                        grid: { line: { stroke: "#2d2d2d", strokeDasharray: "4 4" } },
                        tooltip: {
                            container: {
                                background: "#18181b",
                                color: "#fff",
                                border: "1px solid #333",
                            },
                        },
                        labels: {
                            text: { fill: "#e5e7eb", fontSize: 11, fontWeight: 600 },
                        },
                        legends: {
                            text: { fill: "#9ca3af" },
                        },
                    }}
                />
            </div>
        </div>
    );
}
