'use client'

import React, {MutableRefObject, useRef} from "react";
import {useRouter} from "next/router";
import {Button, Input, Textarea} from "@nextui-org/react";
import Link from 'next/link'
import DarkModeToggle from '@/app/ui/components/utility/DarkModeToggle'
import UploadJsonButton from "@/app/ui/components/utility/UploadJsonButton";


const Page = () => {

    return (
        <div className="flex flex-col min-h-screen bg-gray-800 text-white">
            {/* Header Section */}
            <header className="flex justify-between items-center p-4 bg-gray-900">
                <h1 className="text-3xl">WorkVisualizer</h1>
                <DarkModeToggle></DarkModeToggle>
            </header>

            {/* Main Content Section */}
            <main className="flex flex-1 items-center justify-center">
                <UploadJsonButton redirectOnSuccess={'/dashboard'}></UploadJsonButton>
            </main>

            {/* Footer Section */}
            <footer className="w-full text-center text-sm p-4 bg-gray-900">
                © 2024 NexGen Analytics WorkVisualizer. All rights reserved.
            </footer>
        </div>
    );
};

export default Page;
