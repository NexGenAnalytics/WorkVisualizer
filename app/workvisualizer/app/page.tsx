import React from "react";
import {Button} from "@nextui-org/react";
import Link from 'next/link'

export default function Page() {
    return (
        <main className="flex min-h-screen flex-col p-6 bg-gradient-to-r from-indigo-800 to-indigo-900">
            <div className="backdrop-blur-sm bg-white/30 p-5 rounded-lg bg-slate-500 min-w-20">
                <h1>Work Visualizer</h1>
            </div>
            <div>
                <Link href="/dashboard">
                    <Button>Go to Dashboard</Button>
                </Link>
            </div>
        </main>
    );
}
