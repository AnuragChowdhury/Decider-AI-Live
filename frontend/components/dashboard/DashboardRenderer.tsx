"use client";

import { getComponent, adaptData } from "./ComponentRegistry";
import { motion } from "framer-motion";

// Auto-infer xKey and yKey from the first data row
function inferKeys(data: any[]): { xKey: string; yKey: string } {
    if (!Array.isArray(data) || data.length === 0) return { xKey: "id", yKey: "value" };
    const firstRow = data[0];
    const keys = Object.keys(firstRow);
    // Common x-axis candidates
    const xCandidates = ["id", "month", "date", "year", "label", "category", "name", "x", "status", "region"];
    // Common y-axis candidates
    const yCandidates = ["value", "count", "total", "amount", "revenue", "y", "sales"];

    const xKey = xCandidates.find(k => keys.includes(k)) || keys[0] || "id";
    const yKey = yCandidates.find(k => keys.includes(k)) || keys[1] || "value";
    return { xKey, yKey };
}

export default function DashboardRenderer({ components, onDrilldown }: { components: any[], onDrilldown?: (query: string) => void }) {
    if (!components || components.length === 0) {
        return <div className="text-gray-500">No dashboard components found.</div>;
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 auto-rows-min">
            {components.map((comp, index) => {
                const Widget = getComponent(comp.type);

                if (!Widget) {
                    console.warn(`Unknown component type: ${comp.type}`);
                    return null;
                }

                // Determine column span
                let colSpan = "col-span-1";
                if (comp.col_span) {
                    const spans: Record<number, string> = {
                        1: "col-span-1",
                        2: "col-span-1 md:col-span-2",
                        3: "col-span-1 md:col-span-3",
                        4: "col-span-1 md:col-span-2 lg:col-span-4"
                    };
                    colSpan = spans[comp.col_span] || "col-span-1";
                } else {
                    // Smart defaults by type
                    if (comp.type === "anomaly_list") colSpan = "col-span-1 md:col-span-2 lg:col-span-4";
                    else if (comp.type === "basket_analysis_card") colSpan = "col-span-1 md:col-span-2 lg:col-span-4";
                    else if (["bar_chart", "pie_chart"].includes(comp.type)) colSpan = "col-span-1 md:col-span-2";
                    else if (["line_chart", "area_chart", "table"].includes(comp.type)) colSpan = "col-span-1 md:col-span-2 lg:col-span-4";
                }

                const adaptedData = adaptData(comp.type, comp.data);

                // Skip if no data (except kpi which always has value)
                if (comp.type !== 'kpi' && comp.type !== 'anomaly_list') {
                    if (!adaptedData || (Array.isArray(adaptedData) && adaptedData.length === 0)) {
                        console.warn(`Skipping component "${comp.title}" (${comp.type}) — no renderable data.`);
                        return null;
                    }
                }
                if (comp.type === 'kpi' && !adaptedData) {
                    return null;
                }

                // Auto-infer axis keys for chart types
                const rawData = Array.isArray(adaptedData) ? adaptedData : [];
                const { xKey, yKey } = inferKeys(rawData);

                return (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: index * 0.05 }}
                        className={`${colSpan} min-h-[150px]`}
                    >
                        <Widget
                            title={comp.title}
                            subtitle={comp.subtitle}
                            description={comp.description}
                            data={adaptedData}
                            onDrilldown={onDrilldown}
                            xLabel={comp.x || xKey}
                            yLabel={comp.y || yKey}
                            xKey={comp.x || xKey}
                            yKey={comp.y || yKey}
                            {...comp.props}
                        />
                    </motion.div>
                );
            })}
        </div>
    );
}
