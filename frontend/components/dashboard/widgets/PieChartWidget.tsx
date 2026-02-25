"use client";

import { ResponsivePie } from "@nivo/pie";

export default function PieChartWidget({ title, data, onDrilldown }: { title: string, data: any[], onDrilldown?: (q: string) => void }) {
    const safeData = Array.isArray(data) ? data : [];
    const total = safeData.reduce((sum, d) => sum + (d.value || 0), 0);

    return (
        <div className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl h-full flex flex-col group hover:bg-zinc-900/70 transition-all cursor-pointer">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                {title}
                {onDrilldown && (
                    <span className="text-[10px] bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded text-blue-400 group-hover:bg-blue-500/20 transition-colors">
                        Click slice to drill ↓
                    </span>
                )}
            </h3>
            <div className="flex-1 min-h-[300px] w-full">
                <ResponsivePie
                    data={safeData}
                    onClick={(node) => {
                        if (onDrilldown) {
                            const pct = total > 0 ? ((node.value / total) * 100).toFixed(1) : "?";
                            const query = `In the "${title}" breakdown, "${node.id}" accounts for ${pct}% (${node.value?.toLocaleString()}). What drives this performance and how can it be improved?`;
                            onDrilldown(query);
                        }
                    }}
                    margin={{ top: 20, right: 80, bottom: 80, left: 80 }}
                    innerRadius={0.5}
                    padAngle={0.7}
                    cornerRadius={3}
                    activeOuterRadiusOffset={8}
                    borderWidth={1}
                    borderColor={{ from: 'color', modifiers: [['darker', 0.2]] }}
                    enableArcLinkLabels={true}
                    arcLinkLabelsSkipAngle={10}
                    arcLinkLabelsTextColor="#9ca3af"
                    arcLinkLabelsThickness={2}
                    arcLinkLabelsColor={{ from: 'color' }}
                    arcLabelsSkipAngle={10}
                    arcLabelsTextColor={{ from: 'color', modifiers: [['darker', 2]] }}
                    colors={{ scheme: 'nivo' }}
                    theme={{
                        tooltip: {
                            container: {
                                background: "#18181b",
                                color: "#fff",
                                border: "1px solid #333"
                            }
                        }
                    }}
                    legends={[
                        {
                            anchor: 'bottom',
                            direction: 'row',
                            justify: false,
                            translateX: 0,
                            translateY: 56,
                            itemsSpacing: 0,
                            itemWidth: 100,
                            itemHeight: 18,
                            itemTextColor: '#999',
                            itemDirection: 'left-to-right',
                            itemOpacity: 1,
                            symbolSize: 18,
                            symbolShape: 'circle',
                            effects: [
                                {
                                    on: 'hover',
                                    style: {
                                        itemTextColor: '#fff'
                                    }
                                }
                            ]
                        }
                    ]}
                />
            </div>
        </div>
    );
}
