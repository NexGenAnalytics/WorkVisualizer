import {Slider, SliderValue} from "@nextui-org/slider";
import {Spacer, Tooltip, Switch} from "@nextui-org/react";
import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import AnalylsisViewerHelpButton from "@/app/ui/components/help/AnalysisViewerHelpButton";

export default function AnalysisViewer({ data, timeSlices, summaryData }) {
    const sliceViewer = useRef<SVGSVGElement | null>(null);
    const timeLostViewer = useRef<SVGSVGElement | null>(null);
    const runtimeBar = useRef<SVGSVGElement | null>(null);
    const [selectedSlice, setSelectedSlice] = useState(0);
    const [startTime, setStartTime] = useState("0");
    const [endTime, setEndTime] = useState("1");
    const [maxTimeLostSlice, setMaxTimeLostSlice] = useState<number | null>(null);
    const [showTimeLostPerSlice, setShowTimeLostPerSlice] = useState(false);
    const [maxAvgTimeLost, setMaxAvgTimeLost] = useState(0.0);

    function formatTime(input_time: string) {
        const time = Number(input_time);
        if (Math.abs(time) > 0.01 || time == 0) {
            return time.toFixed(2);
        } else {
            return time.toExponential(2);
        }
    }

    // Extract the unique ranks and sort them from least to greatest
    const allRanks = Array.from(new Set(data.map(d => d.rank))).sort((a, b) => a - b);
    const numRanks = allRanks.length;

    // Determine base bar color
    const barColor = "#99d6ff";
    const altBarColor = "#99ffb3";
    const selectedBarColor = "#33adff";
    const altSelectedBarColor = "#61d17d";

    // Get the total program runtime
    const totalRuntime = summaryData["program.runtime"];

    // Get the last slice's key (which represents the last time slice)
    const lastSlice = d3.max(Object.keys(timeSlices).map(Number));

    useEffect(() => {
        if (timeSlices) {
            // Convert timeSlices object to an array of entries
            const timeSlicesArray = Object.entries(timeSlices).map(([key, value]) => ({
                key,
                ...value,
                time_lost: parseFloat(value.time_lost) // Convert time_lost to a number
            }));

            // Find the slice with the maximum time lost
            const maxTimeLost = d3.max(timeSlicesArray, d => Math.abs(d.time_lost));
            console.log("maxTimeLost: ", maxTimeLost)
            const sliceWithMaxTimeLost = timeSlicesArray.find(d => Math.abs(d.time_lost) === maxTimeLost);
            setMaxAvgTimeLost(Math.abs(maxTimeLost / numRanks));

            if (sliceWithMaxTimeLost) {
                setMaxTimeLostSlice(sliceWithMaxTimeLost.key); // Set the key of the slice with max time lost
            }
        }
    }, [timeSlices, numRanks]); // Only re-run the effect if timeSlices changes

    useEffect(() => {
        if (!timeSlices) return; // Guard clause in case timeSlices are not passed

        let data = Object.entries(timeSlices).map(([key, slice]) => ({
            id: key,
            duration: slice.ts[1] - slice.ts[0],
            time_lost: Number(slice.time_lost) / numRanks,
            time_lost_pct: Number(slice.time_lost) / numRanks / totalRuntime * 100
        }));

        // If there are more than 50 slices, only keep the 50 most time-losing slices
        const maxNumSlices = 50;
        if (data.length > maxNumSlices) {
            // Sort slices by the absolute value of `time_lost`
            data = data.sort((a, b) => Math.abs(b.time_lost) - Math.abs(a.time_lost))
                       .slice(0, maxNumSlices)  // Take the top 50 slices
                       .sort((a, b) => Number(a.id) - Number(b.id)); // Sort back by slice ID
        }

        const width = 920;
        const height = 290;
        const margin = { top: 10, right: 200, bottom: 55, left: 80 };

        const xScale = d3.scaleBand()
            .domain(data.map(d => d.id)) // use slice id as the domain
            .range([margin.left, width - margin.right])
            .padding(0.1);

        console.log("maxAvgTimeLost: ", maxAvgTimeLost)

        const yScale = d3.scaleLinear()
            .domain([0, Math.abs(maxAvgTimeLost)])
            .range([height - margin.bottom, margin.top]);

        const svg = d3.select(sliceViewer.current)
            .attr('width', width)
            .attr('height', height);

        svg.selectAll('*').remove();

        // Create a tooltip div and set initial styles
        const tooltip = d3.select('body').append('div')
            .style('position', 'absolute')
            .style('background-color', 'white')
            .style('border', '1px solid #d3d3d3')
            .style('padding', '5px')
            .style('border-radius', '4px')
            .style('pointer-events', 'none')
            .style('opacity', 0);

        svg.append('g')
            .attr('transform', `translate(0,${height - margin.bottom})`)
            .call(d3.axisBottom(xScale).tickSizeOuter(0))
            .call(g => g.append("text")
                .attr("x", (width - margin.left - margin.right) / 2 + margin.left)
                .attr("y", 40)
                .attr("fill", "currentColor")
                .attr("text-anchor", "middle")
                .text("Slice ID")
            );

        svg.append('g')
            .attr('transform', `translate(${margin.left},0)`)
            .call(d3.axisLeft(yScale).tickSizeOuter(0))
            .call(g => g.append("text")
                .attr("x", -height / 2 + 65)
                .attr("y", margin.left - 130)
                .attr("fill", "currentColor")
                .attr("text-anchor", "center")
                .attr("transform", "rotate(-90)")
                .text("Time Lost (s)")
            );

        svg.selectAll('rect')
            .data(data)
            .enter()
            .append('rect')
            .attr('x', d => xScale(d.id)!)
            .attr('y', d => yScale(Math.abs(d.time_lost)))
            .attr('width', xScale.bandwidth())
            .attr('height', d => height - margin.bottom - yScale(Math.abs(d.time_lost)))
            .attr('fill', d => showTimeLostPerSlice && selectedSlice == Number(d.id) ? (d.time_lost > 0.0 ? selectedBarColor : altSelectedBarColor) : (d.time_lost > 0.0 ? barColor : altBarColor))
            // Mouseover event to darken bar and show tooltip
            .on('mouseover', function(event, d) {
                d3.select(this).attr('fill', showTimeLostPerSlice && selectedSlice == Number(d.id)
                                             ? (d.time_lost > 0 ? d3.color(selectedBarColor).darker(0.5) : d3.color(altSelectedBarColor).darker(0.5))
                                             : (d.time_lost > 0 ? d3.color(barColor).darker(0.5) : d3.color(altBarColor).darker(0.5)));

                // Show tooltip
                tooltip.transition()
                    .duration(200)
                    .style('opacity', .9);

                tooltip.html(`Average Time Lost: ${formatTime(d.time_lost)} s`)
                    .style('left', (event.pageX + 10) + 'px') // Position tooltip
                    .style('top', (event.pageY - 20) + 'px')
                    .style('color', 'black');
            })
            // Mouseout event to restore original bar color and hide tooltip
            .on('mouseout', function(event, d) {
                d3.select(this).attr('fill', showTimeLostPerSlice && selectedSlice == Number(d.id)
                                             ? (d.time_lost > 0.0 ? selectedBarColor : altSelectedBarColor)
                                             : (d.time_lost > 0.0 ? barColor : altBarColor)); // Reset color

                tooltip.transition()
                    .duration(500)
                    .style('opacity', 0); // Hide tooltip
            })
            // Mousemove event to follow the cursor with tooltip
            .on('mousemove', function(event) {
                tooltip.style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 20) + 'px');
            });

        // Adding the legend
        const legend = svg.append('g')
            .attr('transform', `translate(${width - margin.right + 20}, ${margin.top})`);

        // Positive Time Lost Legend Entry
        legend.append('rect')
            .attr('x', 0)
            .attr('y', 0)
            .attr('width', 20)
            .attr('height', 20)
            .attr('fill', barColor);

        legend.append('text')
            .attr('x', 30)
            .attr('y', 15)
            .text('Positive Time Lost')
            .style("fill", "currentColor");

        // Negative Time Lost Legend Entry
        legend.append('rect')
            .attr('x', 0)
            .attr('y', 30)
            .attr('width', 20)
            .attr('height', 20)
            .attr('fill', altBarColor);

        legend.append('text')
            .attr('x', 30)
            .attr('y', 45)
            .text('Negative Time Lost')
            .style('fill', 'currentColor');

    }, [timeSlices, totalRuntime, numRanks, barColor, altBarColor, selectedBarColor, altSelectedBarColor, selectedSlice, maxTimeLostSlice]);

    useEffect(() => {
        if (!data) return;

        let topRanks;
        if (showTimeLostPerSlice) {
            const filteredData = data.filter(d => d.slice === selectedSlice);
            topRanks = allRanks.length > 10 ?  filteredData.sort((a, b) => Math.abs(b.time_lost) - Math.abs(a.time_lost)).slice(0, 10) : filteredData;
        } else {
            // Aggregate time lost across all slices per rank
            const rankTimeLostMap = new Map();
            data.forEach(d => {
                const currentLost = rankTimeLostMap.get(d.rank) || 0;
                rankTimeLostMap.set(d.rank, currentLost + d.time_lost);
            });

            // Convert the map to an array and sort by time_lost
            const aggregatedData = Array.from(rankTimeLostMap, ([rank, time_lost]) => ({ rank, time_lost }))
                .sort((a, b) => Math.abs(b.time_lost) - Math.abs(a.time_lost));

            // Select the top 10 time-losing ranks
            topRanks = aggregatedData.slice(0, 10);
        }

        const width = 800;
        const height = 290;
        const margin = { top: 30, right: 80, bottom: 40, left: 80 };

        const xScale = d3.scaleBand()
            .domain(topRanks.map(d => d.rank.toString()))
            .range([margin.left, width - margin.right])
            .padding(0.1);

        const yScale = d3.scaleLinear()
            .domain([0, totalRuntime + totalRuntime * 0.1])
            .range([height - margin.bottom, margin.top]);

        const svg = d3.select(timeLostViewer.current)
            .attr('width', width)
            .attr('height', height);

        svg.selectAll('*').remove();

        svg.append("line")
            .attr("x1", margin.left)
            .attr("x2", width - margin.right)
            .attr("y1", yScale(totalRuntime))
            .attr("y2", yScale(totalRuntime))
            .attr("stroke", selectedBarColor)
            .attr("stroke-width", 1)
            .attr("stroke-dasharray", "4");

        svg.append("text")
            .attr("x", width - margin.right - 160) // Positioning to the right of the line
            .attr("y", yScale(totalRuntime) - 5) // Positioning slightly above the line
            .attr("fill", selectedBarColor)
            .style("font-size", "12px")
            .style("font-family", "sans-serif")
            .text("Total Program Runtime");

        // Create the tooltip div for the second plot
        const tooltip = d3.select('body').append('div')
            .style('position', 'absolute')
            .style('background-color', 'white')
            .style('border', '1px solid #d3d3d3')
            .style('padding', '5px')
            .style('border-radius', '4px')
            .style('pointer-events', 'none')
            .style('opacity', 0);

        svg.append('g')
            .attr('transform', `translate(0,${height - margin.bottom})`)
            .call(d3.axisBottom(xScale).tickSizeOuter(0))
            .call(g => g.append("text")
                .attr("x", (width - margin.left - margin.right) / 2 + margin.left)
                .attr("y", 40)
                .attr("fill", "currentColor")
                .attr("text-anchor", "middle")
                .text("Rank ID")
            );

        svg.append('g')
            .attr('transform', `translate(${margin.left},0)`)
            .call(d3.axisLeft(yScale).tickSizeOuter(0))
            .call(g => g.append("text")
                .attr("x", -height / 2 + 65)
                .attr("y", margin.left - 130)
                .attr("fill", "currentColor")
                .attr("text-anchor", "center")
                .attr("transform", "rotate(-90)")
                .text("Time Lost (s)")
            );

        const bars = svg.selectAll('rect')
            .data(topRanks, d => d.rank);

        // Add new bars and tooltip interactions
        const newBars = bars.enter()
            .append('rect')
            .attr('x', d => xScale(d.rank.toString())!)
            .attr('y', d => yScale(0))
            .attr('width', xScale.bandwidth())
            .attr('height', 0)
            .attr('fill', d => d.time_lost > 0.0 ? barColor : altBarColor)
            .on('mouseover', function(event, d) {
                d3.select(this).attr('fill', d.time_lost > 0.0 ? d3.color(barColor).darker(0.5) : d3.color(altBarColor)); // Darken the color

                tooltip.transition()
                    .duration(200)
                    .style('opacity', .9);

                tooltip.html(`Time Lost: ${formatTime(d.time_lost)} s`)
                    .style('left', (event.pageX + 10) + 'px') // Position tooltip
                    .style('top', (event.pageY - 20) + 'px')
                    .style('color', 'black');
            })
            .on('mouseout', function(event, d) {
                d3.select(this).attr('fill', d.time_lost > 0.0 ? barColor : altBarColor); // Reset color

                tooltip.transition()
                    .duration(500)
                    .style('opacity', 0);
            })
            .on('mousemove', function(event) {
                tooltip.style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 20) + 'px');
            });

        newBars.transition()
            .duration(500)
            .attr('y', d => yScale(Math.abs(d.time_lost)))
            .attr('height', d => height - margin.bottom - yScale(Math.abs(d.time_lost)));

    }, [data, selectedSlice, showTimeLostPerSlice, totalRuntime, barColor, altBarColor]);

    // Bar representing program runtime
    useEffect(() => {
        // Create the runtime bar SVG if it doesn't exist
        const svg = d3.select(runtimeBar.current)
            .attr("width", "100%")
            .attr("height", 10);  // Set a fixed height for the bar

        // Define the highlighted slice bar (initially empty)
        svg.append("rect")
            .attr("class", "highlighted-slice-bar")
            .attr("x", 0)
            .attr("y", 0)
            .attr("height", 20)
            .attr("fill", selectedBarColor) // Use the selected bar color
            .attr("width", 0);  // Initially 0 width

        // Scale the selected slice relative to the total runtime
        const startPercent = Number(startTime) / totalRuntime;
        const endPercent = Number(endTime) / totalRuntime;

        // Calculate the width and position of the highlighted portion
        const totalWidth = 720;  // Get full bar width

        const highlightWidth = (endPercent - startPercent) * totalWidth;
        const highlightX = startPercent * totalWidth;

        console.log("highlightX: ", highlightX);
        console.log("highlightWidth: ", highlightWidth);

        // Update the highlighted bar with smooth transitions
        svg.select(".highlighted-slice-bar")
            .transition()
            .duration(500)  // Smooth transition duration
            .attr("x", highlightX)
            .attr("width", highlightWidth);

    }, [totalRuntime, startTime, endTime, selectedBarColor]);  // Dependencies to trigger update

    const handleSliceChange = (value: SliderValue) => {
        const currentSlice = Number(value);
        setSelectedSlice(currentSlice);
        setStartTime(formatTime(timeSlices[currentSlice]["ts"][0]));
        setEndTime(formatTime(timeSlices[currentSlice]["ts"][1]));
    };

    return (
        <div>
            <div style={{ display: "flex", alignItems: "center" }}>
                <h2 style={{ fontSize: '1.5rem', margin: '1rem 0', fontWeight: 'bold' }}>Analysis Viewer</h2>
                <Spacer x={2}/>
                <AnalylsisViewerHelpButton/>
            </div>
            <h2 style={{ fontSize: '0.9rem', textAlign: 'center', width: '85%', fontWeight: 'bold' }}>Time Lost Per Slice Averaged Over All Ranks</h2>
            <svg ref={sliceViewer} />
            <Spacer y={3}/>
            <Switch
                checked={showTimeLostPerSlice}
                onChange={(event) => {
                    setShowTimeLostPerSlice(event.target.checked);
                    handleSliceChange(selectedSlice);
                }}
                size="sm"
                color="primary"
            >
                Show Time Lost Per Slice
            </Switch>

            {showTimeLostPerSlice ? (
                <h2 style={{ fontSize: '0.9rem', textAlign: 'center', fontWeight: 'bold', width: '85%' }}>Time Lost Per Rank Per Slice</h2>
            ) : (
                <h2 style={{ fontSize: '0.9rem', textAlign: 'center', fontWeight: 'bold', width: '85%' }}>Time Lost Per Rank Over All Slices</h2>
            )}

            <svg ref={timeLostViewer} />

            <div style={{ visibility: showTimeLostPerSlice ? 'visible' : 'hidden'}}>
                <Spacer y={5}/>
                <div style={{ maxWidth: '720px' }}>
                    <svg ref={runtimeBar}></svg>
                </div>
                <Spacer y={2}/>
                <p style={{ marginLeft: '0' }}><b>Slice {selectedSlice} Duration</b>: {formatTime(String(Number(endTime) - Number(startTime)))} s ({formatTime(startTime)} - {formatTime(endTime)})</p>
                <Spacer y={1}/>
                <Slider
                    size="sm"
                    step={1}
                    color={Number(selectedSlice) === Number(maxTimeLostSlice) ? "danger" : "foreground"}
                    aria-label="Slice Selector"
                    marks={[
                        {
                            value: Number(maxTimeLostSlice),
                            label: "!"
                        }
                    ]}
                    showSteps={false}
                    showTooltip={true}
                    tooltipProps={{
                        placement: "bottom"
                    }}
                    onChange={handleSliceChange}
                    maxValue={lastSlice}
                    minValue={0}
                    defaultValue={0}
                    style={{ width: '79%' }}
                />
            </div>
        </div>
    );
};
