'use client'
import React, { useState, useCallback, useEffect } from 'react';
import GridLayout from 'react-grid-layout';
import NavBar from "@/app/ui/components/NavBar";
import { Divider } from "@nextui-org/react";
import { ToolBar } from "@/app/ui/components/utility/ToolBar";
import dynamic from "next/dynamic";
import Logo from "@/app/ui/components/styling/Logo";

const GlobalIndentedTree = dynamic(() => import('@/app/ui/components/viz/GlobalIndentedTree'), {
    suspense: true,
    ssr: false
});

export default function Page() {
    const [selectedPlots, setSelectedPlots] = useState([]);
    const [plotsData, setPlotsData] = useState({});

    useEffect(() => {
        selectedPlots.forEach(plot => {
            if (!plotsData[plot]?.data && !plotsData[plot]?.isLoading) {
                fetchData(plot);
            }
        });
    }, [selectedPlots, plotsData]);

    const fetchData = async (plot) => {
        setPlotsData(prev => ({ ...prev, [plot]: { isLoading: true } }));
        try {
            const module = await import(`@/app/ui/components/viz/${plot}`);
            const response = await fetch('http://127.0.0.1:8000' + module.dataRequirements.endpoint);
            const data = await response.json();
            setPlotsData(prev => ({ ...prev, [plot]: { data, isLoading: false } }));
        } catch (error) {
            console.error('Failed to fetch data for:', plot);
            setPlotsData(prev => ({ ...prev, [plot]: { isLoading: false, error } }));
        }
    };

    const handlePlotSelectionChange = useCallback(selectedKeys => {
        setSelectedPlots(Array.from(selectedKeys));
    }, []);

    return (
        <>
            <NavBar/>
            <div className='flex h-screen border-2 border-rose-500'>
                <ToolBar onPlotSelectionChange={handlePlotSelectionChange}/>
                <Divider orientation='vertical'/>
                <GridLayout rowHeight={30} width={1200} verticalCompact={true} compactType={'vertical'}>
                    {selectedPlots.map(plot =>
                        <div key={plot} className={`border-2 border-rose-500 overflow-auto h-full ${plotsData[plot]?.isLoading ? 'loading' : ''}`}>
                            {/*{plotsData[plot]?.data ? (*/}
                            {/*    plot === "GlobalIndentedTree" ? <GlobalIndentedTree data={plotsData[plot].data} /> : null*/}
                            {/*) : (*/}
                            {/*    <div>No data or still loading for {plot}</div>*/}
                            {/*)}*/}
                            <Logo/>
                        </div>
                    )}
                </GridLayout>
            </div>
        </>
    );
}
