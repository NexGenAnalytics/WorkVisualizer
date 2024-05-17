import React from "react";
import {Button, Input, Textarea} from "@nextui-org/react";
import Link from 'next/link'
import DarkModeToggle from '@/app/ui/components/utility/DarkModeToggle'

const Page = () => {
    // const { setTheme, type } = useTheme();
    //
    // const handleThemeToggle = () => {
    //     setTheme(type === 'dark' ? 'light' : 'dark');
    // };

    return (
        <div className="flex flex-col min-h-screen bg-gray-800 text-white">
            {/* Header Section */}
            <header className="flex justify-between items-center p-4 bg-gray-900">
                <h1 color="warning">WorkVisualizer</h1>
                <DarkModeToggle></DarkModeToggle>
            </header>

            {/* Main Content Section */}
            <main className="flex flex-1 items-center justify-center">
                <Button color="primary">
                    Upload...
                </Button>
            </main>

            {/* Footer Section */}
            <footer className="w-full text-center text-sm p-4 bg-gray-900">
                © 2024 NexGen Analytics WorkVisualizer. All rights reserved.
            </footer>
        </div>
    );
};

export default Page;
