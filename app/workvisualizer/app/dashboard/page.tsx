'use client'
import React, { useState, useCallback, useEffect } from 'react';
import GridLayout from 'react-grid-layout';
import NavBar from "@/app/ui/components/NavBar";
import { Divider } from "@nextui-org/react";
import dynamic from "next/dynamic";
import Logo from "@/app/ui/components/styling/Logo";
import {Select, SelectItem, Selection} from "@nextui-org/react";

const GlobalIndentedTree = dynamic(() => import('@/app/ui/components/viz/GlobalIndentedTree'), {
    suspense: true,
    ssr: false
});

interface Plot {
    key: string;
    label: string;
}

const plots: Plot[] = [
    { key: 'GlobalIndentedTree.tsx', label: 'Global Indented Tree' },
    { key: 'LogicalSunBurst.tsx', label: 'Logical Sun Burst' },
    { key: 'SpaceTime.tsx', label: 'Space Time' },
    { key: 'SunBurst.tsx', label: 'Sun Burst' }
];

export default function Page() {
    const [selectedPlots, setSelectedPlots] = useState<Set<string>>(new Set());
    const [disabledKeys, setDisabledKeys] = useState<string[]>([]);
    const [plotsData, setPlotsData] = useState({});

    useEffect(() => {
        const selectedArray = Array.from(selectedPlots);
        const includesTree = selectedArray.includes('GlobalIndentedTree.tsx');

        // Independent selection rule for the tree plot
        const nonTreePlots = plots.filter(plot => plot.key !== 'GlobalIndentedTree.tsx').map(plot => plot.key);
        const selectedNonTreePlots = selectedArray.filter(key => nonTreePlots.includes(key));

        if (selectedNonTreePlots.length === 1 && includesTree) {
            setDisabledKeys(nonTreePlots.filter(key => !selectedNonTreePlots.includes(key)));
        } else if (selectedNonTreePlots.length === 1 && !includesTree) {
            setDisabledKeys([]);
        } else if (selectedNonTreePlots.length === 0) {
            setDisabledKeys([]);
        } else {
            setDisabledKeys(nonTreePlots);
        }
    }, [selectedPlots]);


    const handleSelectionChange = (newSelection: Set<string>) => {
        setSelectedPlots(newSelection);
    };

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

    return (
        <>
            <NavBar/>
            <div className='flex h-screen border-2 border-rose-500'>
                <Select
                    label="Select Plots"
                    variant="bordered"
                    placeholder="Select plots"
                    selectionMode={"multiple"}
                    selectedKeys={selectedPlots}
                    className="max-w-xs pt-2 pl-2 pr-2"
                    disabledKeys={disabledKeys}
                    onSelectionChange={handleSelectionChange}
                >
                    {plots.map((plot) => (
                        <SelectItem key={plot.key}>{plot.label}</SelectItem>
                    ))}
                </Select>
                <Divider orientation='vertical'/>
                {/*<GridLayout rowHeight={30} width={1200} verticalCompact={true} compactType={'vertical'}>*/}
                {/*    {selectedPlots.map(plot =>*/}
                {/*        <div key={plot} className={`border-2 border-rose-500 overflow-auto h-full ${plotsData[plot]?.isLoading ? 'loading' : ''}`}>*/}
                {/*            /!*{plotsData[plot]?.data ? (*!/*/}
                {/*            /!*    plot === "GlobalIndentedTree" ? <GlobalIndentedTree data={plotsData[plot].data} /> : null*!/*/}
                {/*            /!*) : (*!/*/}
                {/*            /!*    <div>No data or still loading for {plot}</div>*!/*/}
                {/*            /!*)}*!/*/}
                {/*            <Logo/>*/}
                {/*        </div>*/}
                {/*    )}*/}
                {/*</GridLayout>*/}
            </div>
        </>
    );
}
