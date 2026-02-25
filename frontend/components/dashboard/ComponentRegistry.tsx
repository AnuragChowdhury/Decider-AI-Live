"use client";

import dynamic from "next/dynamic";
import React from "react";

// Dynamic imports to avoid SSR issues with Nivo
const KPIWidget = dynamic(() => import("./widgets/KPIWidget"), { ssr: false });
const BarChartWidget = dynamic(() => import("./widgets/BarChartWidget"), { ssr: false });
const LineChartWidget = dynamic(() => import("./widgets/LineChartWidget"), { ssr: false });
const PieChartWidget = dynamic(() => import("./widgets/PieChartWidget"), { ssr: false });
const AreaChartWidget = dynamic(() => import("./widgets/AreaChartWidget"), { ssr: false });
const TableWidget = dynamic(() => import("./widgets/TableWidget"), { ssr: false });
const AnomalyWidget = dynamic(() => import("./widgets/AnomalyWidget"), { ssr: false });
const RecommendationWidget = dynamic(() => import("./widgets/RecommendationWidget"), { ssr: false });
// New chart types
const RadarChartWidget = dynamic(() => import("./widgets/RadarChartWidget"), { ssr: false });
const HorizontalBarWidget = dynamic(() => import("./widgets/HorizontalBarWidget"), { ssr: false });
const ScatterPlotWidget = dynamic(() => import("./widgets/ScatterPlotWidget"), { ssr: false });
const FunnelWidget = dynamic(() => import("./widgets/FunnelWidget"), { ssr: false });
const SlopeChartWidget = dynamic(() => import("./widgets/SlopeChartWidget"), { ssr: false });
const RadialBarWidget = dynamic(() => import("./widgets/RadialBarWidget"), { ssr: false });
const BasketAnalysisWidget = dynamic(() => import("./widgets/BasketAnalysisWidget"), { ssr: false });

// The Registry Map
// key: backend "type" string
// value: React Component
const REGISTRY: Record<string, React.ComponentType<any>> = {
    kpi: KPIWidget,
    bar_chart: BarChartWidget,
    line_chart: LineChartWidget,
    pie_chart: PieChartWidget,
    area_chart: AreaChartWidget,
    table: TableWidget,
    anomaly_list: AnomalyWidget,
    recommendation_card: RecommendationWidget,
    // New chart type variants
    radar_chart: RadarChartWidget,
    horizontal_bar: HorizontalBarWidget,
    scatter_plot: ScatterPlotWidget,
    funnel_chart: FunnelWidget,   // kept for backwards compat; prefer radial_bar going forward
    slope_chart: SlopeChartWidget,
    radial_bar: RadialBarWidget,
    basket_analysis_card: BasketAnalysisWidget,
    // Fallback or future widgets
    text: ({ title, value }: { title: string, value: string }) => (
        <div className="bg-zinc-900 border border-white/10 p-6 rounded-2xl">
            <h3 className="text-gray-400 text-sm font-medium uppercase">{title}</h3>
            <p className="text-white mt-2">{value}</p>
        </div>
    ),
};

export const getComponent = (type: string) => {
    return REGISTRY[type] || null;
};

// Data Transformers (Optional: if backend data needs reshaping for Nivo)
// For now, we assume the backend sends data in a somewhat usable format,
// or we do lightweight adaptation here.
export const adaptData = (type: string, data: any) => {
    // FIRST: If data is an aggregate dict object (from backend), unwrap the inner data array
    // Backend sends: { table_ref: "...", description: "...", recommended_chart: "...", data: [...rows] }
    if (data && typeof data === 'object' && !Array.isArray(data) && type !== 'kpi') {
        // Could be an aggregate dict - extract the 'data' key
        if (Array.isArray(data.data)) {
            data = data.data; // Unwrap the inner data array
        } else if (data.data === null || data.data === undefined) {
            return null; // No data available
        }
    }

    // 1. Line / Area / Scatter / Slope Chart Adaptation
    if (["line_chart", "area_chart", "scatter_plot", "slope_chart"].includes(type) && Array.isArray(data)) {
        if (data.length > 0) {
            // Check if it's a Forecast Item (has forecast_values array)
            if (data[0].forecast_values) {
                return data.map((series: any) => ({
                    id: series.series || "Forecast",
                    data: series.forecast_values.map((val: number, i: number) => ({
                        x: `Month ${i + 1}`,
                        y: val
                    }))
                }));
            }
            // Standard Nivo format check (already correct)
            if (data[0].id && Array.isArray(data[0].data)) {
                return data;
            }
            // Fallback: Flat array mapping
            return [{
                id: "Series 1",
                data: data.map((d: any, i: number) => ({
                    x: d.date || d.month || d.year || d.label || d.category || d.x || d.key || i,
                    y: d.value || d.amount || d.total || d.y || d.count || 0
                }))
            }];
        } else {
            return null;
        }
    }

    // 2. Pie Chart Adaptation
    if (type === "pie_chart" && Array.isArray(data)) {
        if (data.length === 0) return null;
        return data.map((d: any) => ({
            id: d.id || d.name || d.label || d.category || "Unknown",
            value: d.value || d.count || d.total || 0
        }));
    }

    // 3. Bar Chart (vertical) — ensure it's an array
    if (type === "bar_chart") {
        if (!Array.isArray(data) || data.length === 0) return null;
        return data;
    }

    // 4. Horizontal Bar — same as bar_chart, pass through
    if (type === "horizontal_bar") {
        if (!Array.isArray(data) || data.length === 0) return null;
        return data;
    }

    // 5. Radar Chart — pass as-is (adaptation happens in the widget)
    if (type === "radar_chart") {
        if (!Array.isArray(data) || data.length === 0) return null;
        return data;
    }

    // 6. Funnel Chart — pass as-is (backwards compat)
    if (type === "funnel_chart") {
        if (!Array.isArray(data) || data.length === 0) return null;
        return data;
    }

    // 6b. Radial Bar — same shape as pie/bar [{id, value}]
    if (type === "radial_bar") {
        if (!Array.isArray(data) || data.length === 0) return null;
        return data.map((d: any) => ({
            id: d.id ?? d.name ?? d.label ?? d.category ?? "Unknown",
            value: d.value ?? d.count ?? d.total ?? 0,
        }));
    }

    // 7. Anomaly list — pass through as-is
    if (type === "anomaly_list") {
        if (!Array.isArray(data) || data.length === 0) return null;
        return data;
    }

    // 8. Recommendation card — pass through string[] or object[]
    if (type === "recommendation_card") {
        if (!data) return null;
        if (Array.isArray(data) && data.length === 0) return null;
        return data;
    }

    // 9. Basket Analysis — pass BasketRule[] through as-is
    if (type === "basket_analysis_card") {
        if (!Array.isArray(data) || data.length === 0) return null;
        return data;
    }

    // For other types, check if data is empty
    if (Array.isArray(data) && data.length === 0) return null;
    if (!data) return null;

    return data;
};
