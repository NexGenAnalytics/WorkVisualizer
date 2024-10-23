'use client'
import React, {useEffect, useState} from 'react';
import NavBar from "@/app/ui/components/NavBar";
import {Textarea} from "@nextui-org/react";
import {Accordion, AccordionItem} from "@nextui-org/accordion";
import CallTree from "@/app/ui/components/viz/CallTree";
import ProportionAnalyzer from "@/app/ui/components/viz/ProportionAnalyzer";
import EventsPlot from "@/app/ui/components/viz/EventsPlot";
import AnalysisViewer from "@/app/ui/components/viz/AnalysisViewer";
import ClusterTable from "@/app/ui/components/viz/ClusterTable";
import AnalysisTable from "@/app/ui/components/viz/AnalysisTable";
import AnalysisHelpButton from "@/app/ui/components/help/AnalysisHelpButton";
import AnalysisResultsHelpButton from "@/app/ui/components/help/AnalysisResultsHelpButton";
import VizSelectionHelpButton from "@/app/ui/components/help/VizSelectionHelpButton";
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
    const [inputValue, setInputValue] = useState("0");
    const [invalidRank, setInvalidRank] = useState(false);
    const [specifyRank, setSpecifyRank] = useState<boolean | true>(true);
    const [changedInput, setChangedInput] = useState(false);
    const [selectedDepth, setSelectedDepth] = useState<number | 5>(5);
    const [isIndentedTreeSelected, setIsIndentedTreeSelected] = useState(false);
    const [plotData, setPlotData] = useState<any>({});
    const [representativeRank, setRepresentativeRank] = useState<string | null>(null);
    const [rankClusters, setRankClusters] = useState(null);
    const [isAnalysisRunning, setIsAnalysisRunning] = useState(false);
    const [isAnalysisComplete, setIsAnalysisComplete] = useState(false);
    const [timeSlices, setTimeSlices] = useState(null);
    const [selectedSlice, setSelectedSlice] = useState<string | "">("");
    const [programStart, setProgramStart] = useState(-1);
    const [programEnd, setProgramEnd] = useState(0);
    const [startTime, setStartTime] = useState(-1);
    const [endTime, setEndTime] = useState(0);
    const [specifySlice, setSpecifySlice] = useState(false);
    const [plots, setPlots] = useState<Plot[]>([
        // API formatting: /api/{component}/({root})/{depth}/{rank}
        //   Defaults:
        //      root (only for hierarchies): -1 (shows entire available tree)
        //      depth:                        5 (show records with path depth < 5)
        //      rank:                         0 (default to rank 0)
        { key: 'callTree', plot: { label: 'Call Tree', endpoint: '/api/logical_hierarchy/-1/5/0' } },
        { key: 'proportionAnalyzer', plot: { label: 'Proportion Analyzer', endpoint: '/api/logical_hierarchy/-1/5/0'} },
        { key: 'eventsPlot', plot: { label: 'Events Plot', endpoint: '/api/eventsplot/5/0'} },
        { key: 'summaryTable', plot: { label: 'Summary Table', endpoint: '/api/metadata/5/0' } },
        { key: 'analysisViewer', plot: { label: 'Analysis Viewer', endpoint: '/api/analysisviewer/5/0'}}
        ]);

    const handleRunAnalysisButtonClick = async () => {
        setIsAnalysisRunning(true);
        const repr_response = await fetch('/api/analysis/representativerank');
        const repr_data = await repr_response.json();
        setRepresentativeRank(repr_data["representative rank"]);
        const cluster_response = await fetch('/api/analysis/rankclusters');
        const cluster_data = await cluster_response.json();
        setRankClusters(cluster_data);
        const slice_response = await fetch('/api/analysis/timeslices');
        const slice_data = await slice_response.json();
        setTimeSlices(slice_data);
        setIsAnalysisComplete(true);
        setIsAnalysisRunning(false);
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
            const actualRank = rank == "rep" ? representativeRank : rank;
            return {
                ...plot,
                plot: {
                    ...plot.plot,
                    endpoint: `${previousEndpoint}/${depth}/${actualRank}`
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

            if (startTime == -1) {
                start_time = dataMap['summaryTable']['program.start'];
                setStartTime(start_time);
                setProgramStart(start_time);
                console.log("Resetting start time");

                end_time = dataMap['summaryTable']['program.end'];
                setEndTime(end_time);
                setProgramEnd(end_time);
            }
        }
        fetchData();
    }, [plots]);

        useEffect(() => {
            if (isAnalysisComplete) {
                const fetchAnalysisViewerData = async () => {
                    const response = await fetch(`/api/analysisviewer/5/${specifyRank ? inputValue : representativeRank}`);
                    const data = await response.json();
                    setPlotData((prevData) => ({
                        ...prevData,
                        analysisViewer: data,
                    }));
                };
                fetchAnalysisViewerData();
            }
        }, [isAnalysisComplete, inputValue, representativeRank]);

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
                    <Spacer y={5}/>
                    <div className="flex items-center space-x-4">
                        <Select
                            variant="bordered"
                            placeholder="Select visualization"
                            onSelectionChange={(keys) => setSelectedPlot(Array.from(keys))}
                            className="min-w-[200px]"
                            disabledKeys={timeSlices ? [] : ["analysisViewer"]}
                        >
                            {plots.filter(plot => plot.key !== 'callTree' && plot.key !== 'summaryTable').map((plot) => (
                                <SelectItem key={plot.key}>{plot.plot.label}</SelectItem>
                            ))}
                        </Select>
                        <VizSelectionHelpButton/>
                    </div>
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
                            <Card>
                                {timeSlices !== null && timeSlices !== undefined && (
                                    <div style={{ display: 'flex', alignItems: 'center' }}>
                                        <Spacer x={3} y={2}/>
                                        <h3 style={{ fontSize: '1.0rem', margin: '1rem 0', fontWeight: 'bold' }}>
                                            Analysis Results
                                        </h3>
                                        <Spacer x={2}/>
                                        <AnalysisResultsHelpButton/>
                                        <Spacer y={2}/>
                                    </div>
                                )}
                                {timeSlices !== null && timeSlices !== undefined ?
                                    <AnalysisTable
                                        timeSlices={timeSlices}
                                        summaryData={plotData['summaryTable']}
                                        analysisData={plotData['analysisViewer']}
                                    />
                                    :
                                    <div style={{ display: 'flex', alignItems: 'center' }}>
                                        <Spacer x={2}/>
                                        <Button
                                            color="primary"
                                            onPress={handleRunAnalysisButtonClick}
                                            onKeyDown={handleRunAnalysisButtonClick}
                                            isDisabled={isAnalysisRunning}
                                            style={{ display: 'block', marginTop: '10px' }}
                                        >
                                            {isAnalysisRunning ? (
                                                <div style={{ display: 'flex', alignItems: 'center' }}>
                                                    <CircularProgress size="sm" aria-label="Loading..." />
                                                    <span style={{ marginLeft: '10px' }}>Running...</span>
                                                </div>
                                            ) : ('Run Analysis')}
                                        </Button>
                                        <Spacer x={2}/>
                                        <AnalysisHelpButton fromAnalysisTab={false}/>
                                    </div>
                                }
                                <Spacer y={5}/>
                                {timeSlices !== null && timeSlices !== undefined && (
                                    <div style={{ display: 'flex', alignItems: 'center' }}>
                                        <Spacer x={2}/>
                                        <p style={{ fontSize: '15px' }}><i>Tip: Visualize these results with the Analysis Viewer in the visualizations dropdown.</i></p>
                                    </div>
                                )}
                                <Spacer y={2}/>
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
                                <Accordion isDisabled={!timeSlices} defaultExpandedKeys={timeSlices ? ["1"] : [""]}>
                                    <AccordionItem
                                        title={
                                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                                <Spacer x={1}/>
                                                Slice Explorer
                                            </div>
                                        }
                                        key="1"
                                    >
                                        {timeSlices && (
                                            <>
                                                <Input
                                                    label={selectedSlice in Object.keys(timeSlices) || selectedSlice == ""
                                                            ? "Enter slice name"
                                                            : `Enter slice from 0 - ${Object.keys(timeSlices).length - 1}`}
                                                    type="number"
                                                    placeholder={`Enter slice from 0 - ${Object.keys(timeSlices).length - 1}`}
                                                    value={selectedSlice || ""}
                                                    color={selectedSlice in Object.keys(timeSlices) || selectedSlice == ""
                                                            ? "default"
                                                            : "danger"}
                                                    onChange={(e) => {
                                                        const current_slice = e.target.value
                                                        setSelectedSlice(current_slice);
                                                        if (timeSlices[current_slice]) {
                                                            setStartTime(timeSlices[current_slice].ts[0]);
                                                            setEndTime(timeSlices[current_slice].ts[1]);
                                                            setSpecifySlice(true);
                                                        } else {
                                                            setStartTime(programStart);
                                                            setEndTime(programEnd);
                                                            setSpecifySlice(false);
                                                        }
                                                        console.log(startTime);
                                                        console.log(endTime);
                                                    }}
                                                />
                                                <Spacer y={2}/>
                                                <Table aria-label="Time Slices Table">
                                                    <TableHeader>
                                                        <TableColumn>Slice Name</TableColumn>
                                                        <TableColumn>Begin (s)</TableColumn>
                                                        <TableColumn>End (s)</TableColumn>
                                                        <TableColumn>Total Time Lost (s)</TableColumn>
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
                                                                            {
                                                                                Math.abs(Number(sliceData.time_lost)) >= 0.01 ?
                                                                                    `${Number(sliceData.time_lost).toFixed(2)}` :
                                                                                    `${Number(sliceData.time_lost).toExponential(2)}`
                                                                            }
                                                                    </TableCell>
                                                                </TableRow>
                                                                : null
                                                        ))}
                                                    </TableBody>
                                                </Table>
                                            </>
                                        )}
                                    </AccordionItem>
                                </Accordion>
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
                    {selectedPlot.length > 0 ? (
                        selectedPlot.map((key) => {
                            const PlotComponent = {
                                'proportionAnalyzer': ProportionAnalyzer,
                                'eventsPlot': EventsPlot,
                                'analysisViewer': timeSlices ? AnalysisViewer : null,
                            }[key];
                            return PlotComponent ? (
                                <PlotComponent
                                    data={plotData[key]}
                                    selectSlice={specifySlice}
                                    start={startTime}
                                    end={endTime}
                                    rank={specifyRank ? inputValue : representativeRank}
                                    timeSlices={timeSlices}
                                    summaryData={plotData['summaryTable']}
                                />
                            ) : null;
                        })
                    ) : (
                        <div>
                            <p><i>Select a visualization from the dropdown menu.</i></p>
                        </div>
                    )}
                    </div>
                </div>
            </div>
        </div>
    );
}
