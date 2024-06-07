'use client'
import React, { useState, useEffect } from 'react';
import NavBar from "@/app/ui/components/NavBar";
import { Divider, Spacer } from "@nextui-org/react";
import { Select, SelectItem, Checkbox } from "@nextui-org/react";
import { RadioGroup, Radio } from "@nextui-org/react";
import GlobalIndentedTree from "@/app/ui/components/viz/GlobalIndentedTree";
import LogicalSunBurst from "@/app/ui/components/viz/LogicalSunBurst";
import SpaceTime from "@/app/ui/components/viz/SpaceTime";
import SummaryTable from "@/app/ui/components/viz/SummaryTable";

interface Plot {
    key: string;
    plot: {
        label: string;
        endpoint: string;
    }
}

var known_ranks = [0, 1, 2, 3];

export default function Page() {
    const [selectedPlot, setSelectedPlot] = useState<string[]>([]);
    const [selectedRank, setSelectedRank] = useState<number | null>(null);
    const [isIndentedTreeSelected, setIsIndentedTreeSelected] = useState(false);
    const [plotData, setPlotData] = useState<any>({});
    const [plots, setPlots] = useState<Plot[]>([
        { key: 'globalIndentedTree', plot: { label: 'Global Indented Tree', endpoint: '/api/logical_hierarchy/-1/0' } },
        { key: 'logicalSunBurst', plot: { label: 'Logical Sun Burst', endpoint: '/api/logical_hierarchy/-1/0'} },
        { key: 'spaceTime', plot: { label: 'Space Time', endpoint: '/api/spacetime/0'} },
        { key: 'summaryTable', plot: { label: 'Summary Table', endpoint: '/api/metadata/0' } },
    ]);

    const handleRadioChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const rank = parseInt(event.target.value, 10);
        setSelectedRank(rank);
        updateAllEndpoints(rank);
    };

    const updateAllEndpoints = (selection: number) => {
        console.log(plots)
        console.log(selection)
        setPlots(plots.map(plot => {
            const previousEndpoint = plot.plot.endpoint.split("/").slice(0, -1);
            console.log(previousEndpoint);
            console.log(`${previousEndpoint.join("/")}/${selection}`);
            return {
                ...plot,
                plot: {
                    ...plot.plot,
                    endpoint: `${previousEndpoint.join("/")}/${selection}`
                }
            };
        }));
        console.log(plots)
    };

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
    }, [plots, selectedRank]);

    return (
        <div className='h-screen '>
            <NavBar/>
            <div className='flex flex-row h-screen'>
                <div className="flex flex-col p-4 min-w-fit h-screen">
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
                        defaultSelectedKeys={['logicalSunBurst']}
                        onSelectionChange={(keys) => setSelectedPlot(Array.from(keys))}
                        className="min-w-full pt-4"
                    >
                        {plots.filter(plot => plot.key !== 'globalIndentedTree' && plot.key !== 'summaryTable').map((plot) => (
                            <SelectItem key={plot.key}>{plot.plot.label}</SelectItem>
                        ))}
                    </Select>
                    <Spacer y={5}/>
                    <Divider orientation='horizontal'/>
                    <Spacer y={2}/>
                    {plotData['summaryTable'] ? <SummaryTable data={plotData['summaryTable']} /> : null}
                    {/*<p className="text-xs">{JSON.stringify(plotData['summaryTable'])}</p>*/}
                </div>
                <Divider orientation='vertical'/>
                <div className="flex flex-row p-4 bg-slate-950">
                    <div className="overflow-auto">
                        {isIndentedTreeSelected && plotData['globalIndentedTree'] ? <GlobalIndentedTree data={plotData['globalIndentedTree']} /> : null}
                    </div>
                    {isIndentedTreeSelected && plotData['globalIndentedTree'] ? <Spacer x={2}/> : null}
                    {isIndentedTreeSelected && plotData['globalIndentedTree'] ? <Divider orientation='vertical' /> : null}
                    <Spacer x={2}/>
                    <div className="overflow-auto">
                        <RadioGroup
                            label="Select Rank"
                            orientation="horizontal"
                            defaultValue={known_ranks[0].toString()}
                            onChange={handleRadioChange} // Ensure you handle the change event
                        >
                            {known_ranks.map(rank => (
                                <Radio key={rank.toString()} value={rank}>
                                    {rank}
                                </Radio>
                            ))}
                        </RadioGroup>
                        <Spacer y={5}/>
                        {selectedPlot.map((key) => {
                            const PlotComponent = {
                                'logicalSunBurst': LogicalSunBurst,
                                'spaceTime': SpaceTime,
                            }[key];
                            return PlotComponent ? <PlotComponent data={plotData[key]} /> : null;
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}
