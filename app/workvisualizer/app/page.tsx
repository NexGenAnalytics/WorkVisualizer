import {useRouter} from "next/router";
import {Button, Input, Textarea} from "@nextui-org/react";
import Link from 'next/link'
import FileUploadButton from "@/app/ui/components/utility/FileUploadButton";
import Navigation from "next/navigation";
import NavBar from "@/app/ui/components/NavBar";
import Logo from "@/app/ui/components/styling/Logo";


const Page = () => {

    return (
        <div className="flex flex-col min-h-screen">
            <NavBar></NavBar>
            {/* Header Section */}

            {/* Main Content Section */}
            <main className="flex flex-1 items-center justify-center">
                <FileUploadButton redirectOnSuccess={'/dashboard'}></FileUploadButton>
            </main>

            {/* Footer Section */}
            <footer className="w-full text-center text-sm p-4">
                © 2024 NexGen Analytics WorkVisualizer. All rights reserved.
            </footer>
        </div>
    );
};

export const metadata = {
    icons: {
        icon: '/favicon.png',
    },
}

export default Page;
