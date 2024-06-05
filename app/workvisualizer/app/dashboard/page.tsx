'use client'
import React, { useState, useEffect } from 'react';
import NavBar from "@/app/ui/components/NavBar";
import {Divider, Spacer} from "@nextui-org/react";
import {Select, SelectItem, Checkbox} from "@nextui-org/react";
import GlobalIndentedTree from "@/app/ui/components/viz/GlobalIndentedTree";
import LogicalSunBurst from "@/app/ui/components/viz/LogicalSunBurst";
import SpaceTime from "@/app/ui/components/viz/SpaceTime";
import SunBurst from "@/app/ui/components/viz/SunBurst";

interface Plot {
    key: string;
    plot: {
        label: string;
        endpoint: string;
    }
}

const plots: Plot[] = [
    { key: 'globalIndentedTree', plot: { label: 'Global Indented Tree', endpoint: '/api/logical_hierarchy/-1' } },
    { key: 'logicalSunBurst', plot: { label: 'Logical Sun Burst', endpoint: '/api/logical_hierarchy/-1'} },
    { key: 'spaceTime', plot: { label: 'Space Time', endpoint: '/api/spacetime'} },
    { key: 'sunBurst', plot: { label: 'Sun Burst', endpoint: '/api/hierarchy'} },
];

export default function Page() {
    const [selectedPlot, setSelectedPlot] = useState<string[]>([]);
    const [isIndentedTreeSelected, setIsIndentedTreeSelected] = useState(false);
    const [plotData, setPlotData] = useState<any>({});

    useEffect(() => {
        async function fetchData() {
            const responses = await Promise.all(plots.map(async (plot) => {
                const response = await fetch(plot.plot.endpoint);
                const data = await response.json();
                return { key: plot.key, data };
            }));
            const dataMap: any = {};
            responses.forEach(res => {
                dataMap[res.key] = res.data;
            });
            setPlotData(dataMap);
        }
        fetchData();
    }, []);

    return (
        <div className='h-screen '>
            <NavBar/>
            <div className='flex'>
                <div className="flex flex-col p-4 min-w-fit">
                    <Checkbox
                        className="min-w-full"
                        isSelected={isIndentedTreeSelected}
                        onValueChange={setIsIndentedTreeSelected}
                    >
                        Global Indented Tree
                    </Checkbox>
                    <Select
                        label="Select Plots"
                        variant="bordered"
                        placeholder="Select plots"
                        selectedKeys={selectedPlot}
                        onSelectionChange={(keys) => setSelectedPlot(Array.from(keys))}
                        className="min-w-full pt-4"
                    >
                        {plots.filter(plot => plot.key !== 'globalIndentedTree').map((plot) => (
                            <SelectItem key={plot.key}>{plot.plot.label}</SelectItem>
                        ))}
                    </Select>
                </div>
                <Divider orientation='vertical'/>
                <div className="flex flex-row p-4">
                    <div className="overflow-auto">
                        {isIndentedTreeSelected && plotData['globalIndentedTree'] ? <GlobalIndentedTree data={plotData['globalIndentedTree']} /> : null}
                    </div>
                    {isIndentedTreeSelected && plotData['globalIndentedTree'] ? <Spacer x={2}/> : null}
                    {isIndentedTreeSelected && plotData['globalIndentedTree'] ? <Divider orientation='vertical' /> : null}
                    <Spacer x={2}/>
                    <div className="overflow-auto">
                        {selectedPlot.map((key) => {
                            const PlotComponent = {
                                'logicalSunBurst': LogicalSunBurst,
                                'spaceTime': SpaceTime,
                                'sunBurst': SunBurst
                            }[key];
                            return PlotComponent ? <PlotComponent data={plotData[key]} /> : null;
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}
