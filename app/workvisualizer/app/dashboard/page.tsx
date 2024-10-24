'use client'
import React, {useEffect, useState} from 'react';
import NavBar from "@/app/ui/components/NavBar";
import CallTree from "@/app/ui/components/viz/CallTree";
import ProportionAnalyzer from "@/app/ui/components/viz/ProportionAnalyzer";
import EventsPlot from "@/app/ui/components/viz/EventsPlot";
import ClusterTable from "@/app/ui/components/viz/ClusterTable";
import SummaryTable from "@/app/ui/components/viz/SummaryTable";
import {
    Button,
    Card,
    CardBody,
    Checkbox,
    CircularProgress,
    Divider,
    Dropdown,
    DropdownItem,
    DropdownMenu,
    DropdownTrigger,
    Input,
    Radio,
    RadioGroup,
    Select,
    SelectItem,
    Spacer,
    Tab,
    Table,
    TableBody,
    TableCell,
    TableColumn,
    TableHeader,
    TableRow,
    Tabs
} from "@nextui-org/react";

interface Plot {
    key: string;
    plot: {
        label: string;
        endpoint: string;
    }
}

let comm_size : number;
let known_ranks : string[] = []
let rank_range : string = ""
let rank_range_error : string = ""
let known_depths = [1]
let maximum_depth = 1

let start_time : number;
let end_time : number;

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
        { key: 'callTree', plot: { label: 'Call Tree', endpoint: '/api/logical_hierarchy/-1/5/0' } },
        { key: 'proportionAnalyzer', plot: { label: 'Proportion Analyzer', endpoint: '/api/logical_hierarchy/-1/5/0'} },
        { key: 'eventsPlot', plot: { label: 'Events Plot', endpoint: '/api/eventsplot/5/0'} },
        { key: 'summaryTable', plot: { label: 'Summary Table', endpoint: '/api/metadata/5/0' } },
        ]);
    const [isAnalysisRunning, setIsAnalysisRunning] = useState(false);
    const [representativeRank, setRepresentativeRank] = useState(null);
    const [rankClusters, setRankClusters] = useState(null);
    const [isTimeSlicingRunning, setIsTimeSlicingRunning] = useState(false);
    const [timeSlices, setTimeSlices] = useState(null);
    const [selectedSlice, setSelectedSlice] = useState<string | null>(null);
    const [showSliceLines, setShowSliceLines] = useState(false);


    const handleAnalysisButtonClick = async () => {
        setIsAnalysisRunning(true);
        const response = await fetch('/api/analysis/representativerank');
        const data = await response.json();
        setRepresentativeRank(data["representative rank"]);
        const cluster_response = await fetch('/api/analysis/rankclusters');
        const cluster_data = await cluster_response.json();
        setRankClusters(cluster_data);
        setIsAnalysisRunning(false);
    };

    const handleTimeSlicingButtonClick = async () => {
        setIsTimeSlicingRunning(true);
        const repr_response = await fetch('/api/analysis/representativerank');
        const repr_data = await repr_response.json();
        setRepresentativeRank(repr_data["representative rank"]);
        const cluster_response = await fetch('/api/analysis/rankclusters');
        const cluster_data = await cluster_response.json();
        setRankClusters(cluster_data);
        const slice_response = await fetch('/api/analysis/timeslices');
        const slice_data = await slice_response.json();
        setTimeSlices(slice_data);
        setIsTimeSlicingRunning(false);
    };

    const handleRadioChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const rank = event.target.value;
        setInvalidRank(false);
        if (rank == "rep" && representativeRank !== null) {
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
        if (known_ranks.includes(selectedRank)) {
            setInputValue(selectedRank);
            setInvalidRank(false);
            updateAllEndpoints(selectedDepth, selectedRank);
        } else {
            setInvalidRank(true);
        }
        setChangedInput(false);
    }

    const handleMaxDepthChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
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
            comm_size = dataMap['summaryTable']['mpi.world.size'];
            // known_ranks = dataMap['summaryTable']['known.ranks'].map(Number).sort((a, b) => a - b);
            let tmp_known_ranks = Array.from({length: comm_size}, (_, i) => i);
            known_depths = dataMap['summaryTable']['known.depths'].sort();
            maximum_depth = dataMap['summaryTable']['maximum.depth'];

            rank_range = `Enter a rank ${known_ranks[0]} - ${known_ranks[known_ranks.length - 1]}`;
            rank_range_error = `Rank not found in range ${known_ranks[0]} - ${known_ranks[known_ranks.length - 1]}`;
            known_ranks = tmp_known_ranks.map(String);

            start_time = dataMap['summaryTable']['program.start'];
            end_time = dataMap['summaryTable']['program.end'];
        }
        fetchData();
    }, [plots]);

    return (
        <div className='h-screen '>
            <NavBar/>
            <div className='flex flex-row h-full'>
                <div className="flex flex-col p-4 h-full overflow-y-auto" style={{ minWidth: '500px', maxWidth: '525px' }}>
                    <Checkbox
                        className="min-w-full"
                        isSelected={isIndentedTreeSelected}
                        onValueChange={setIsIndentedTreeSelected}
                    >
                        Call Tree
                    </Checkbox>
                    <Select
                        label="Select Plots"
                        variant="bordered"
                        placeholder="Select plots"
                        onSelectionChange={(keys) => setSelectedPlot(Array.from(keys))}
                        className="min-w-full pt-4"
                    >
                        {plots.filter(plot => plot.key !== 'callTree' && plot.key !== 'summaryTable').map((plot) => (
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
                        <Tab key="analysis" title="Analysis">
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <Spacer y={2}/>
                                {/* {representativeRank !== null && representativeRank !== undefined ?
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
                                            : 'Run rank analysis'}
                                    </Button>
                                } */}
                                <Spacer x={2}/>
                                {timeSlices !== null && timeSlices !== undefined ?
                                    <Card>
                                        <CardBody>
                                            <p>Time Slices Generated ✅</p>
                                            <Checkbox
                                                isSelected={showSliceLines}
                                                onChange={(e) => setShowSliceLines(e.target.checked)}
                                            >
                                                Show Slice Lines
                                            </Checkbox>
                                        </CardBody>
                                    </Card>
                                    :
                                    <Button
                                        color="default"
                                        onPress={handleTimeSlicingButtonClick}
                                        onKeyDown={handleTimeSlicingButtonClick}
                                        isDisabled={isTimeSlicingRunning}>
                                        {isTimeSlicingRunning ?
                                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                                <CircularProgress size="sm" aria-label="Loading..."/>
                                                <span style={{ marginLeft: '10px' }}>Running...</span>
                                            </div>
                                            : 'Run time slicing analysis'}
                                    </Button>
                                }
                            </div>
                            <Spacer y={2}/>
                            {timeSlices !== null && timeSlices !== undefined ?
                                <>
                                    <Input
                                        label="Enter slice name"
                                        type="number"
                                        placeholder="Enter slice name"
                                        value={selectedSlice || ""}
                                        onChange={(e) => setSelectedSlice(e.target.value)}
                                    />
                                    <Spacer y={2}/>
                                    <Table aria-label="Time Slices Table">
                                        <TableHeader>
                                            <TableColumn>Slice Name</TableColumn>
                                            <TableColumn>Begin</TableColumn>
                                            <TableColumn>End</TableColumn>
                                            <TableColumn>Avg Time Lost (s)</TableColumn>
                                        </TableHeader>
                                        <TableBody>
                                            {Object.entries(timeSlices).map(([sliceName, sliceData]) => (
                                                sliceName === selectedSlice ?
                                                    <TableRow key={sliceName}>
                                                        <TableCell>{sliceName}</TableCell>
                                                        <TableCell>
                                                            {
                                                                `${sliceData.ts[0].toFixed(3)}`
                                                            }
                                                        </TableCell>
                                                        <TableCell>
                                                            {
                                                                `${sliceData.ts[1].toFixed(3)}`
                                                            }
                                                        </TableCell>
                                                        <TableCell>
                                                            <Dropdown>
                                                                <DropdownTrigger>
                                                                    <Button>{sliceData.time_lost}</Button>
                                                                </DropdownTrigger>
                                                                <DropdownMenu>
                                                                    {Object.entries(sliceData.statistics).map(([statKey, statValue]) => (
                                                                        <DropdownItem key={statKey}>{`${statKey}: ${statValue}`}</DropdownItem>
                                                                    ))}
                                                                </DropdownMenu>
                                                            </Dropdown>
                                                        </TableCell>
                                                    </TableRow>
                                                    : null
                                            ))}
                                        </TableBody>
                                    </Table>
                                </>
                                : null
                            }
                            {/* {rankClusters !== null && rankClusters !== undefined ?
                                <ClusterTable clusters={rankClusters} />
                            : null
                            } */}
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
                                    <Radio key="rep" value="rep" isDisabled={representativeRank == null || representativeRank == undefined}>
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

                </div>
                <Divider orientation='vertical'/>
                <div className="flex flex-row p-4 h-full overflow-y-auto w-full">
                    <div className="overflow-auto">
                        {isIndentedTreeSelected && plotData['callTree'] ? <CallTree data={plotData['callTree']} /> : null}
                    </div>
                    {isIndentedTreeSelected && plotData['callTree'] ? <Spacer x={2}/> : null}
                    {isIndentedTreeSelected && plotData['callTree'] ? <Divider orientation='vertical' /> : null}
                    <Spacer x={2}/>
                    <div className="overflow-auto">
                        <Spacer y={5}/>
                        {selectedPlot.map((key) => {
                            const PlotComponent = {
                                'proportionAnalyzer': ProportionAnalyzer,
                                'eventsPlot': EventsPlot,
                            }[key];
                            return PlotComponent ? <PlotComponent data={plotData[key]} start={start_time} end={end_time} timeSlices={timeSlices} showSliceLines={showSliceLines} /> : null;
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}
