"use client";

export default function TableWidget({ title, data, columns }: { title: string, data: any[], columns: { key: string, label: string }[] }) {
    if (!data || data.length === 0) {
        return (
            <div className="bg-zinc-900/50 backdrop-blur-sm border border-white/10 p-6 rounded-2xl h-full flex flex-col">
                <h3 className="text-white font-semibold mb-4">{title}</h3>
                <div className="text-gray-500 italic">No data available</div>
            </div>
        )
    }

    // Auto-detect columns if not provided
    const displayCols = columns || Object.keys(data[0]).map(key => ({ key, label: key.charAt(0).toUpperCase() + key.slice(1) }));

    return (
        <div className="bg-zinc-900 border border-white/10 p-6 rounded-2xl h-full flex flex-col">
            <h3 className="text-white font-semibold mb-1">{title}</h3>
            {title.toLowerCase().includes("anomalies") && (
                <p className="text-xs text-gray-500 mb-4">
                    These define records where sales or quantity significantly deviate from the norm, potentially indicating fraud or viral trends.
                </p>
            )}
            {!title.toLowerCase().includes("anomalies") && <div className="mb-4"></div>}
            <div className="overflow-x-auto flex-1">
                <table className="w-full text-sm text-left text-gray-400">
                    <thead className="text-xs text-gray-500 uppercase bg-zinc-800/50">
                        <tr>
                            {displayCols.map((col) => (
                                <th key={col.key} className="px-6 py-3 rounded-t-lg first:rounded-tl-lg last:rounded-tr-lg">
                                    {col.label}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {data.slice(0, 10).map((row, idx) => (
                            <tr key={idx} className="bg-transparent border-b border-white/5 hover:bg-white/5 transition-colors">
                                {displayCols.map((col) => {
                                    let cellValue = row[col.key];

                                    // 1. Handle Z-Score -> Layman Terms
                                    if (col.key === 'z_score') {
                                        const z = parseFloat(cellValue);
                                        let severity = "Low";
                                        let color = "text-green-400";
                                        if (Math.abs(z) > 3) { severity = "Critical"; color = "text-red-500 font-bold"; }
                                        else if (Math.abs(z) > 2) { severity = "High"; color = "text-orange-400"; }

                                        return (
                                            <td key={col.key} className="px-6 py-4">
                                                <span className={color}>{severity}</span>
                                            </td>
                                        );
                                    }

                                    // 2. Handle Arrays (e.g. Basket Analysis)
                                    if (Array.isArray(cellValue)) {
                                        cellValue = cellValue.join(", ");
                                    }

                                    // 3. Round Floats
                                    if (typeof cellValue === 'number' && !Number.isInteger(cellValue)) {
                                        cellValue = cellValue.toFixed(2);
                                    }

                                    return (
                                        <td key={col.key} className="px-6 py-4">
                                            {cellValue}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
                {data.length > 10 && (
                    <div className="text-xs text-center text-gray-600 mt-2 italic">
                        Showing top 10 of {data.length} rows
                    </div>
                )}
            </div>
        </div>
    );
}
