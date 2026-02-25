"use client";

import { ResponsiveLine } from "@nivo/line";

// Area Chart is essentially a Line Chart with filled area
export default function AreaChartWidget({ title, data, onDrilldown, xLabel, yLabel }: { title: string, data: any[], onDrilldown?: (q: string) => void, xLabel?: string, yLabel?: string }) {

    // Helper for intelligent axis formatting (same as LineChart)
    let tickValues: any = 10;
    let formatTick = (v: any) => `${v}`.slice(0, 10);

    if (Array.isArray(data) && data.length > 0 && data[0].data) {
        const xValues = data[0].data.map((d: any) => `${d.x}`);
        // If string labels (months/categories), just show them, potentially reduced
        if (xValues.length > 15) {
            tickValues = xValues.filter((_: any, i: number) => i % Math.ceil(xValues.length / 10) === 0);
        } else {
            tickValues = undefined;
        }
        formatTick = (v: any) => v;
    }

    return (
        <div className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl h-full flex flex-col group hover:bg-zinc-900/70 transition-all">
            <h3 className="text-white font-semibold mb-6 flex items-center gap-2">
                {title}
                <span className="text-[10px] bg-white/10 px-2 py-0.5 rounded text-gray-500 group-hover:text-blue-400 transition-colors">Click to Analyze</span>
            </h3>
            <div className="flex-1 min-h-[300px] w-full">
                <ResponsiveLine
                    data={Array.isArray(data) ? data : []}
                    onClick={(point: any) => {
                        if (onDrilldown) {
                            const query = `Analyze area trend for ${point.serieId} at ${point.data.x}`;
                            onDrilldown(query);
                        }
                    }}
                    margin={{ top: 20, right: 30, bottom: 60, left: 60 }}
                    xScale={{ type: 'point' }}
                    yScale={{
                        type: 'linear',
                        min: 'auto',
                        max: 'auto',
                        stacked: false, // Area charts often look better stacked, but let's keep it simple
                        reverse: false
                    }}
                    yFormat=" >-.2f"
                    curve="catmullRom" // Smoother curve for area
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
                    colors={{ scheme: 'category10' }}
                    enableArea={true}
                    areaOpacity={0.3}
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
