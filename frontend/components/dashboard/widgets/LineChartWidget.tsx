"use client";

import { ResponsiveLine } from "@nivo/line";

export default function LineChartWidget({ title, data, onDrilldown, xLabel, yLabel }: { title: string, data: any[], onDrilldown?: (q: string) => void, xLabel?: string, yLabel?: string }) {
    // Nivo Line expects [{ id: "series1", data: [{x:..., y:...}] }]
    // We might receive simple array, so we might need adapter.
    // Assuming 'data' passed here is ALREADY formatted for Nivo for simplicity,
    // OR we adapt it. Let's assume the DashboardRenderer prepares it.

    // Intelligent Axis Logic
    let tickValues: any = 10;
    let formatTick = (v: any) => `${v}`.slice(0, 10);

    if (Array.isArray(data) && data.length > 0 && data[0].data) {
        const xValues = data[0].data.map((d: any) => `${d.x}`);
        const count = xValues.length;

        // Check if X values are Date-like (YYYY-MM or YYYY-MM-DD)
        const isYM = xValues.every((v: string) => /^\d{4}-\d{2}$/.test(v));
        const isYMD = xValues.every((v: string) => /^\d{4}-\d{2}-\d{2}/.test(v));

        if (isYM || isYMD) {
            // ... (Date Logic) ...
            if (count > 48) {
                tickValues = xValues.filter((v: string) => /-01($|T)/.test(v));
                if (tickValues.length < 2) tickValues = xValues.filter((_: any, i: number) => i % 12 === 0);
                formatTick = (v: any) => `${v}`.split("-")[0];
            } else if (count > 18) {
                tickValues = xValues.filter((v: string) => /-(01|04|07|10)($|T)/.test(v));
                if (tickValues.length < 2) tickValues = xValues.filter((_: any, i: number) => i % 3 === 0);
                formatTick = (v: any) => {
                    const parts = `${v}`.split("-");
                    if (parts.length < 2) return v;
                    const y = parts[0];
                    const m = parseInt(parts[1]);
                    const q = Math.ceil(m / 3);
                    return `Q${q} ${y}`;
                };
            }
        } else {
            // String Labels (e.g. Month Names)
            // If we have too many, reduce density
            if (count > 12) {
                tickValues = xValues.filter((_: any, i: number) => i % Math.ceil(count / 12) === 0);
            } else {
                tickValues = undefined; // Show all
            }
            formatTick = (v: any) => v;
        }
    }

    return (
        <div className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl h-full flex flex-col group hover:bg-zinc-900/70 transition-all cursor-pointer">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                {title}
                {onDrilldown && (
                    <span className="text-[10px] bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded text-blue-400 group-hover:bg-blue-500/20 transition-colors">
                        Click point to drill ↓
                    </span>
                )}
            </h3>
            <div className="flex-1 min-h-[300px] w-full">
                <ResponsiveLine
                    data={Array.isArray(data) ? data : []}
                    onClick={(point: any) => {
                        if (onDrilldown) {
                            const query = `In the "${title}" trend chart, what caused the value to be ${point.data.y?.toLocaleString()} at ${point.data.x}? Is this an anomaly or expected seasonal behaviour? What should we do?`;
                            onDrilldown(query);
                        }
                    }}
                    margin={{ top: 20, right: 30, bottom: 60, left: 60 }}
                    xScale={{ type: 'point' }}
                    yScale={{
                        type: 'linear',
                        min: 'auto',
                        max: 'auto',
                        stacked: false,
                        reverse: false
                    }}
                    yFormat=" >-.2f"
                    curve="natural"
                    axisTop={null}
                    axisRight={null}
                    axisBottom={{
                        tickSize: 5,
                        tickPadding: 5,
                        tickRotation: -45,
                        legend: xLabel,
                        legendOffset: 50,
                        legendPosition: 'middle',
                        format: formatTick,
                        tickValues: tickValues
                    }}
                    axisLeft={{
                        tickSize: 5,
                        tickPadding: 5,
                        tickRotation: 0,
                        legend: yLabel,
                        legendOffset: -50,
                        legendPosition: 'middle'
                    }}
                    enableGridX={false}
                    colors={{ scheme: 'blues' }}
                    pointSize={8}
                    pointColor={{ theme: 'background' }}
                    pointBorderWidth={2}
                    pointBorderColor={{ from: 'serieColor' }}
                    pointLabelYOffset={-12}
                    useMesh={true}
                    theme={{
                        axis: {
                            ticks: { text: { fill: "#9ca3af" } },
                            legend: { text: { fill: "#9ca3af" } }
                        },
                        grid: { line: { stroke: "#333", strokeDasharray: "4 4" } },
                        crosshair: { line: { stroke: "#fff" } },
                        tooltip: {
                            container: {
                                background: "#18181b",
                                color: "#fff",
                                border: "1px solid #333"
                            }
                        }
                    }}
                />
            </div>
        </div>
    );
}
