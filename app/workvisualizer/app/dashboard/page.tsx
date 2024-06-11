'use client'
import React, { useState, useEffect } from 'react';
import NavBar from "@/app/ui/components/NavBar";
import {Tabs, Tab, Card, CardBody} from "@nextui-org/react";
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

let known_ranks = [0]
let known_depths = [1]
let maximum_depth = 1

export default function Page() {
    const [selectedPlot, setSelectedPlot] = useState<string[]>([]);
    const [selectedRank, setSelectedRank] = useState<number | 0>(0);
    const [selectedDepth, setSelectedDepth] = useState<number | 5>(5);
    const [isIndentedTreeSelected, setIsIndentedTreeSelected] = useState(false);
    const [plotData, setPlotData] = useState<any>({});
    const [plots, setPlots] = useState<Plot[]>([
        // API formatting: /api/{component}/({root})/{depth}/{rank}
        //   Defaults:
        //      root (only for hierarchies): -1 (shows entire available tree)
        //      depth:                        5 (only parses records with path depth < 5)
        //      rank:                         0 (default to rank 0)
        { key: 'globalIndentedTree', plot: { label: 'Global Indented Tree', endpoint: '/api/logical_hierarchy/-1/5/0' } },
        { key: 'logicalSunBurst', plot: { label: 'Logical Sun Burst', endpoint: '/api/logical_hierarchy/-1/5/0'} },
        { key: 'spaceTime', plot: { label: 'Space Time', endpoint: '/api/spacetime/5/0'} },
        { key: 'summaryTable', plot: { label: 'Summary Table', endpoint: '/api/metadata/5/0' } },
        ]);

    const handleRankChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const rank = parseInt(event.target.value, 5);
        setSelectedRank(rank);
        updateAllEndpoints(selectedDepth, rank);
    };

    const handleMaxDepthChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const initial_depth = parseInt(event.target.value, 5);
        const depth =  (initial_depth >= maximum_depth && 5 >= maximum_depth) ? 5 : initial_depth;
        setSelectedDepth(depth);
        updateAllEndpoints(depth, selectedRank);
    };

    const updateAllEndpoints = (depth: number, rank: number) => {
        setPlots(plots.map(plot => {
            const previousSplits = plot.plot.endpoint.split("/");
            const previousEndpoint = previousSplits.slice(0,-2).join("/");
            return {
                ...plot,
                plot: {
                    ...plot.plot,
                    endpoint: `${previousEndpoint}/${depth}/${rank}`
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
            known_ranks = dataMap['summaryTable']['known.ranks'].sort()
            known_depths = dataMap['summaryTable']['known.depths'].sort()
            maximum_depth = dataMap['summaryTable']['maximum.depth']
        }
        fetchData();
    }, [plots]);

    return (
        <div className='h-screen '>
            <NavBar/>
            <div className='flex flex-row h-screen'>
                <div className="flex flex-col p-4 h-screen" style={{ minWidth: '425px', maxWidth: '525px' }}>
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
                    <Tabs aria-label="options">
                        <Tab key="summary" title="Summary">
                            <Card>
                                {plotData['summaryTable'] ? <SummaryTable data={plotData['summaryTable']} /> : null}
                            </Card>
                        </Tab>
                        <Tab key="setting" title="Settings">
                            <Card>
                                <Spacer y={5} />
                                <RadioGroup
                                    label="Select rank"
                                    orientation="horizontal"
                                    defaultValue={selectedRank}
                                    onChange={handleRankChange}
                                    style={{ marginLeft: '15px' }}
                                >
                                    {known_ranks.map(rank => (
                                        <Radio key={rank.toString()} value={rank}>
                                            {rank}
                                        </Radio>
                                    ))}
                                </RadioGroup>
                                <Spacer y={5}/>
                                <Select
                                    style={{ marginLeft: '15px' }}
                                    disallowEmptySelection
                                    label="Select maximum depth"
                                    className="max-w-xs"
                                    defaultValue={selectedDepth}
                                    onChange={handleMaxDepthChange}
                                >
                                    {known_depths.map((depth) => (
                                    <SelectItem key={depth.toString()} value={depth.toString()}>
                                        {depth}
                                    </SelectItem>
                                    ))}
                                </Select>
                                <Spacer y={5}/>
                            </Card>
                        </Tab>
                    </Tabs>
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
