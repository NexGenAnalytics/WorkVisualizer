'use client'
import React, {useState, useCallback, useEffect} from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import NavBar from "@/app/ui/components/NavBar";
import GlobalIndentedTree from '@/app/ui/components/viz/GlobalIndentedTree';
// import SpaceTime from '@/app/ui/components/viz/SpaceTime';
import UploadJsonButton from "@/app/ui/components/utility/UploadJsonButton";
import { IoIosStats } from 'react-icons/io';
import {redirect} from "next/navigation";
import {ToolBar} from "@/app/ui/components/utility/ToolBar";
import {Divider} from "@nextui-org/divider";
import {Spacer} from "@nextui-org/react";
import {Spinner} from "@nextui-org/react";
import dynamic from 'next/dynamic';
import {VisualizationProps} from "@/app/types";

// const ResponsiveGridLayout = WidthProvider(Responsive);

export default function Page() {
    const [selectedPlots, setSelectedPlots] = useState([]);
    const [plotsData, setPlotsData] = useState({});

    useEffect(() => {
        async function fetchData(plot) {
            if (plotsData[plot]?.data || plotsData[plot]?.isLoading) return; // Avoid refetching or fetching if already loading

            // Start loading
            setPlotsData(prev => ({ ...prev, [plot]: { isLoading: true } }));

            try {
                const module = await import(`@/app/ui/components/viz/${plot}`);
                const { dataRequirements } = module;
                const response = await fetch('http://127.0.0.1:8000' + dataRequirements.endpoint, {
                    method: 'GET',
                });
                const data = await response.json();

                // Set data
                setPlotsData(prev => ({ ...prev, [plot]: { data, isLoading: false } }));
            } catch (error) {
                console.error('Failed to fetch data for:', plot);
                setPlotsData(prev => ({ ...prev, [plot]: { isLoading: false, error } }));
            }
        }

        selectedPlots.forEach(plot => {
            fetchData(plot);
        });

    }, [selectedPlots]);

    const handlePlotSelectionChange = useCallback((selectedKeys: Iterable<never> | ArrayLike<never>) => {
        setSelectedPlots(Array.from(selectedKeys));
    }, []);

    return (
        <>
            <NavBar/>
            <div className='flex h-screen'>
                <ToolBar onPlotSelectionChange={handlePlotSelectionChange}/>
                <Divider orientation='vertical'/>
                <div className="flex flex-row items-center">
                    {selectedPlots.map((plot) => {
                        const PlotComponent = dynamic(() => import(`@/app/ui/components/viz/${plot}`).then(mod => mod.default));
                        const plotInfo = plotsData[plot];

                        if (!plotInfo || plotInfo.isLoading) {
                            return <Spinner size="lg"/>;
                        } else if (plotInfo.error) {
                            return <div key={plot}>Error loading {plot}</div>;
                        }

                        return <PlotComponent key={plot} data={plotInfo.data}/>;
                    })}
                </div>
            </div>
        </>
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
