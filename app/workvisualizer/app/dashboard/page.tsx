'use client'
import React, { useState, useEffect } from 'react';
import NavBar from "@/app/ui/components/NavBar";
import { Button } from "@nextui-org/react";
import { Tabs, Tab, Card, CardBody } from "@nextui-org/react";
import { Divider, Spacer } from "@nextui-org/react";
import { Select, SelectItem, Checkbox } from "@nextui-org/react";
import { RadioGroup, Radio, Input } from "@nextui-org/react";
import GlobalIndentedTree from "@/app/ui/components/viz/GlobalIndentedTree";
import LogicalSunBurst from "@/app/ui/components/viz/LogicalSunBurst";
import SpaceTime from "@/app/ui/components/viz/SpaceTime";
import SummaryTable from "@/app/ui/components/viz/SummaryTable";
import {CircularProgress} from "@nextui-org/react";


interface Plot {
    key: string;
    plot: {
        label: string;
        endpoint: string;
    }
}

let known_ranks : string[] = []
let rank_range : string = ""
let rank_range_error : string = ""
let known_depths = [1]
let maximum_depth = 1

export default function Page() {
    const [selectedPlot, setSelectedPlot] = useState<string[]>([]);
    const [selectedRank, setSelectedRank] = useState<string | "0">("0");
    const [inputValue, setInputValue] = useState("");
    const [invalidRank, setInvalidRank] = useState(false);
    const [specifyRank, setSpecifyRank] = useState<boolean | true>(true);
    const [changedInput, setChangedInput] = useState(false);
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
    const [isAnalysisRunning, setIsAnalysisRunning] = useState(false);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [representativeRank, setRepresentativeRank] = useState("");

    const handleAnalysisButtonClick = async () => {
        setIsAnalysisRunning(true);
        const response = await fetch('/api/analysis/representativerank');
        const data = await response.json();
        setAnalysisResult(data);
        setIsAnalysisRunning(false);
    };

    const handleRadioChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const rank = event.target.value;
        setInvalidRank(false);
        if (rank == "rep") {
            setSpecifyRank(false);
            setSelectedRank(rank);
            updateAllEndpoints(selectedDepth, representativeRank);
        } else {
            setSpecifyRank(true);
            setSelectedRank("");
            if (inputValue != "") {
                setSelectedRank(inputValue);
                updateAllEndpoints(selectedDepth, inputValue);
            }
        }
    };

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setInvalidRank(false);
        setSelectedRank(event.target.value);
        if (event.target.value != "") {
            setChangedInput(true);
        }
    };

    const handleInputSubmission = () => {
        if (known_ranks.includes(selectedRank.toString())) {
            setInputValue(selectedRank);
            setInvalidRank(false);
            updateAllEndpoints(selectedDepth, selectedRank);
        } else {
            setInvalidRank(true);
        }
        setChangedInput(false);
    }

    const handleMaxDepthChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const initial_depth = parseInt(event.target.value, 10);
        const depth =  (initial_depth >= maximum_depth && 5 >= maximum_depth) ? 5 : initial_depth;
        setSelectedDepth(depth);
        updateAllEndpoints(depth, selectedRank);
    };

    const updateAllEndpoints = (depth: number, rank: string) => {
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
            known_ranks = dataMap['summaryTable']['known.ranks'].map(String).sort();
            known_depths = dataMap['summaryTable']['known.depths'].sort();
            maximum_depth = dataMap['summaryTable']['maximum.depth'];

            rank_range = `Enter a rank ${known_ranks[0]} - ${known_ranks[known_ranks.length - 1]}`;
            rank_range_error = `Rank not found in range ${known_ranks[0]} - ${known_ranks[known_ranks.length - 1]}`;
        }
        fetchData();
    }, [plots]);

    useEffect(() => {
        if (analysisResult) {
            setRepresentativeRank(analysisResult['representative rank']);
        }
    }, [analysisResult]);

    return (
        <div className='h-screen '>
            <NavBar/>
            <div className='flex flex-row h-full'>
                <div className="flex flex-col p-4 h-full overflow-y-auto" style={{ minWidth: '425px', maxWidth: '525px' }}>
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
                                    label="Select Rank View"
                                    defaultValue={specifyRank ? "select" : selectedRank}
                                    orientation="horizontal"
                                    value={specifyRank ? "select" : selectedRank}
                                    onChange={handleRadioChange}
                                    style={{ marginLeft: '15px' }}
                                >
                                    <Radio key="rep" value="rep">
                                        Representative
                                        {/* it would be cool to have a small (?) icon that explains what the representative rank is */}
                                    </Radio>
                                    <Radio key="select" value="select">
                                        Enter Rank
                                    </Radio>
                                </RadioGroup>
                                <Spacer y={5}/>
                                <div style={{ display: 'flex', alignItems: 'left'}}>
                                    <Spacer x={3.5}/>
                                    <Input
                                        style={{ marginLeft: '15px' }}
                                        type="number"
                                        isClearable={specifyRank}
                                        placeholder={specifyRank ? rank_range : inputValue}
                                        isDisabled={!specifyRank}
                                        defaultValue={specifyRank ? selectedRank : inputValue}
                                        value={specifyRank ? selectedRank : ""}
                                        isInvalid={invalidRank}
                                        errorMessage={rank_range_error}
                                        onClear={() => {
                                            setSelectedRank("");
                                            setInputValue("");
                                            setInvalidRank(false);
                                            setChangedInput(false);
                                        }}
                                        onChange={handleInputChange}
                                        startContent={
                                            <div className="pointer-events-none flex items-center">
                                                <span className="text-default-400 text-small"> </span>
                                            </div>
                                        }>
                                    </Input>
                                    <Spacer x={1}/>
                                    <Button
                                        color="default"
                                        onPress={handleInputSubmission}
                                        onKeyDown={handleInputSubmission}
                                        isDisabled={!changedInput}>
                                            Submit
                                    </Button>
                                    <Spacer x={12}/>
                                </div>
                                <Spacer y={5}/>
                                <Select
                                    style={{ marginLeft: '15px' }}
                                    disallowEmptySelection
                                    label="Select maximum depth"
                                    placeholder={selectedDepth > maximum_depth ? maximum_depth.toString() : selectedDepth.toString()}
                                    className="max-w-xs"
                                    defaultValue={selectedDepth}
                                    onChange={handleMaxDepthChange}
                                >
                                    {known_depths.map((depth) => (
                                    <SelectItem key={depth.toString()} value={depth.toString()}>
                                        {depth.toString()}
                                    </SelectItem>
                                    ))}
                                </Select>
                                <Spacer y={5}/>
                            </Card>
                        </Tab>
                    </Tabs>
                    <Spacer y={2}/>
                    <Divider orientation='horizontal'/>
                    <Spacer y={2}/>
                    {representativeRank ?
                            <Card>
                              <CardBody>
                                <p>Representative rank: {representativeRank}</p>
                              </CardBody>
                            </Card>
                        :
                        <Button
                            color="default"
                            onPress={handleAnalysisButtonClick}
                            onKeyDown={handleAnalysisButtonClick}
                            isDisabled={isAnalysisRunning}>
                            {isAnalysisRunning ?
                                <div style={{ display: 'flex', alignItems: 'center' }}>
                                    <CircularProgress size="sm" aria-label="Loading..."/>
                                    <span style={{ marginLeft: '10px' }}>Running...</span>
                                </div>
                                : 'Run analysis'}
                        </Button>
                    }

                </div>
                <Divider orientation='vertical'/>
                <div className="flex flex-row p-4 bg-slate-950 h-full overflow-y-auto w-full">
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
