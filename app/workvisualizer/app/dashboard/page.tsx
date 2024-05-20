import React from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import NavBar from "@/app/ui/components/NavBar";
import GlobalIndentedTree from '@/app/ui/components/GlobalIndentedTree';
import SpaceTime from '@/app/ui/components/SpaceTime';
import UploadJsonButton from "@/app/ui/components/utility/UploadJsonButton";
import { IoIosStats } from 'react-icons/io';
import {redirect} from "next/navigation";

// const ResponsiveGridLayout = WidthProvider(Responsive);

export default async function Page() {
    const data = await getData()
    return (
        <div>
            <NavBar />
            <SpaceTime data={data} />
        </div>
    );
}

async function getData() {
    try {
        const res = await fetch('http://127.0.0.1:8000/api/spacetime')

        if (!res.ok) {
            throw new Error('Failed to fetch data')
        }
        const jsonData = await res.json();

        if (jsonData.message === "No file was uploaded.") {
            console.log(jsonData.message);
            // setError('No file was uploaded.');
            redirect('/'); // Redirecting to the landing page
        }

        return jsonData
    } catch (error) {
        console.error(error)
    }
}
