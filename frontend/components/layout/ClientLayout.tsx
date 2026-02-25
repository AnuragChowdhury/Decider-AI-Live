"use client";

import Background from "../ui/Background";
import MouseTrace from "../ui/MouseTrace";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="relative min-h-screen">
            <Background />
            <MouseTrace />
            <div className="relative z-10">
                {children}
            </div>
        </div>
    );
}
