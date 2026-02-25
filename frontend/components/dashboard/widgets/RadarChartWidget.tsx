"use client";

import { ResponsiveRadar } from "@nivo/radar";

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
    },
    dots: { text: { fill: "#9ca3af" } }
};

export default function RadarChartWidget({
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

    // Radar needs: [{key: "label", seriesA: val, seriesB: val...}]
    // Our data usually comes as [{id/category: "label", value: N}]
    // We convert flat category-value arrays into radar format
    let radarData = safeData;
    let keys: string[] = ["value"];

    // If data has id/value shape (pie/bar style), pivot into radar
    const firstItem = safeData[0];
    if (firstItem && !firstItem.key && (firstItem.id || firstItem.label || firstItem.category)) {
        const catKey = firstItem.id !== undefined ? "id" : firstItem.label !== undefined ? "label" : "category";
        const valKey = firstItem.value !== undefined ? "value" : firstItem.count !== undefined ? "count" : "total";
        keys = [valKey];
        radarData = safeData.map((d: any) => ({
            key: d[catKey] ?? d.name ?? "Unknown",
            [valKey]: d[valKey] ?? 0,
        }));
    }

    return (
        <div
            className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl h-full flex flex-col group hover:bg-zinc-900/70 transition-all cursor-pointer"
            onClick={() => {
                if (onDrilldown) {
                    onDrilldown(`Analyze the radar pattern in "${title}". Which categories are strongest and which are weakest? What actions would balance performance across all dimensions?`);
                }
            }}
        >
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                {title}
                {onDrilldown && (
                    <span className="text-[10px] bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded text-purple-400 group-hover:bg-purple-500/20 transition-colors">
                        Click to analyze ↓
                    </span>
                )}
            </h3>
            <div className="flex-1 min-h-[300px] w-full">
                <ResponsiveRadar
                    data={radarData}
                    keys={keys}
                    indexBy="key"
                    maxValue="auto"
                    margin={{ top: 30, right: 60, bottom: 40, left: 60 }}
                    curve="linearClosed"
                    borderWidth={2}
                    borderColor={{ from: "color" }}
                    gridLevels={4}
                    gridShape="circular"
                    gridLabelOffset={16}
                    enableDots={true}
                    dotSize={8}
                    dotColor={{ theme: "background" }}
                    dotBorderWidth={2}
                    dotBorderColor={{ from: "color" }}
                    enableDotLabel={false}
                    fillOpacity={0.25}
                    blendMode="multiply"
                    motionConfig="wobbly"
                    colors={{ scheme: "purple_blue" }}
                    theme={nivoTheme}
                    sliceTooltip={({ index, data: tData }: any) => (
                        <div className="bg-zinc-800 border border-white/10 rounded px-3 py-2 text-sm text-white shadow-lg">
                            <strong>{index}</strong>
                            {tData.map((d: any) => (
                                <div key={d.id} style={{ color: d.color }}>
                                    {d.id}: {d.value?.toLocaleString()}
                                </div>
                            ))}
                        </div>
                    )}
                />
            </div>
        </div>
    );
}
