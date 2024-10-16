import {Slider, SliderValue} from "@nextui-org/slider";
import {Spacer, Tooltip, Switch} from "@nextui-org/react";
import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import AnalylsisViewerHelpButton from "@/app/ui/components/help/AnalysisViewerHelpButton";

export default function AnalysisViewer({ data, timeSlices, summaryData }) {
    const sliceViewer = useRef<SVGSVGElement | null>(null);
    const timeLostViewer = useRef<SVGSVGElement | null>(null);
    const [selectedSlice, setSelectedSlice] = useState(0);
    const [maxTimeLostSlice, setMaxTimeLostSlice] = useState<number | null>(null); // Store the slice with max time lost
    const [showTimeLostPerSlice, setShowTimeLostPerSlice] = useState(false);

    function formatTime(input_time: string) {
        const time = Number(input_time);
        if (Math.abs(time) > 0.01) {
            return time.toFixed(2);
        } else {
            return time.toExponential(2);
        }
    }

    // Extract the unique ranks and sort them from least to greatest
    const allRanks = Array.from(new Set(data.map(d => d.rank))).sort((a, b) => a - b);

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
            const maxTimeLost = d3.max(timeSlicesArray, d => d.time_lost);
            const sliceWithMaxTimeLost = timeSlicesArray.find(d => d.time_lost === maxTimeLost);

            if (sliceWithMaxTimeLost) {
                setMaxTimeLostSlice(sliceWithMaxTimeLost.key); // Set the key of the slice with max time lost
            }
        }
    }, [timeSlices]); // Only re-run the effect if timeSlices changes

    useEffect(() => {
        if (!timeSlices) return; // Guard clause in case timeSlices are not passed

        const data = Object.entries(timeSlices).map(([key, slice]) => ({
            id: key,
            duration: slice.ts[1] - slice.ts[0],
            time_lost: Number(slice.time_lost),
            time_lost_pct: Number(slice.time_lost) / totalRuntime * 100
        }));

        const width = 900;
        const height = 350;
        const margin = { top: 30, right: 200, bottom: 55, left: 80 };

        const xScale = d3.scaleBand()
            .domain(data.map(d => d.id)) // use slice id as the domain
            .range([margin.left, width - margin.right])
            .padding(0.1);

        const yScale = d3.scaleLinear()
            .domain([0, 100])
            .range([height - margin.bottom, margin.top]);

        const colorScale = d3.scaleSequential(d3.interpolateBlues)
        .domain([0, 100]); // Flip domain to match the bar color scheme


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
                .text("Time Lost (%)")
            );

        svg.selectAll('rect')
            .data(data)
            .enter()
            .append('rect')
            .attr('x', d => xScale(d.id)!)
            .attr('y', d => yScale(d.time_lost_pct))
            .attr('width', xScale.bandwidth())
            .attr('height', d => height - margin.bottom - yScale(d.time_lost_pct))
            .attr('fill', d => colorScale(d.time_lost_pct))
            // Mouseover event to darken bar and show tooltip
            .on('mouseover', function(event, d) {
                d3.select(this).attr('fill', d3.color(colorScale(d.time_lost_pct)).darker(0.5)); // Darken the color

                // Show tooltip
                tooltip.transition()
                    .duration(200)
                    .style('opacity', .9);

                tooltip.html(`Total Time Lost: ${formatTime(d.time_lost)} s`)
                    .style('left', (event.pageX + 10) + 'px') // Position tooltip
                    .style('top', (event.pageY - 20) + 'px')
                    .style('color', 'black');
            })
            // Mouseout event to restore original bar color and hide tooltip
            .on('mouseout', function(event, d) {
                d3.select(this).attr('fill', colorScale(d.time_lost_pct)); // Reset color

                tooltip.transition()
                    .duration(500)
                    .style('opacity', 0); // Hide tooltip
            })
            // Mousemove event to follow the cursor with tooltip
            .on('mousemove', function(event) {
                tooltip.style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 20) + 'px');
            });

    // Add color scale legend (vertical)
    const legendHeight = 150;
    const legendWidth = 20;
    const legendMargin = { top: 10, right: 175, bottom: 10, left: 0 };

    // Define the vertical gradient
    const defs = svg.append("defs");

    const linearGradient = defs.append("linearGradient")
        .attr("id", "linear-gradient")
        .attr("x1", "0%").attr("y1", "100%") // From bottom (green)
        .attr("x2", "0%").attr("y2", "0%");  // To top (red)

    linearGradient.selectAll("stop")
        .data(d3.range(0, 1.01, 0.01))
        .enter().append("stop")
        .attr("offset", d => `${d * 100}%`)
        .attr("stop-color", d => d3.interpolateBlues(d)); // Red at top, green at bottom

    // Draw the color bar
    svg.append("rect")
        .attr("x", width - legendMargin.right) // Position next to the plot
        .attr("y", margin.top)
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .style("fill", "url(#linear-gradient)");

    // Add text labels for legend
    svg.append("text")
        .attr("x", width - legendMargin.right + legendWidth + 5) // Position next to the color bar
        .attr("y", margin.top + legendHeight)
        .style("fill", "currentColor")
        .attr("text-anchor", "start")
        .text("Less Time Lost");

    svg.append("text")
        .attr("x", width - legendMargin.right + legendWidth + 5) // Position next to the color bar
        .attr("y", margin.top)
        .style("fill", "currentColor")
        .attr("text-anchor", "start")
        .text("More Time Lost");

    }, [timeSlices, totalRuntime]);

    useEffect(() => {
        if (!data) return;

        let topRanks;
        if (showTimeLostPerSlice) {
            const filteredData = data.filter(d => d.slice === selectedSlice);
            topRanks = allRanks.length > 10 ?  filteredData.sort((a, b) => b.time_lost - a.time_lost).slice(0, 10) : filteredData;
        } else {
            // Aggregate time lost across all slices per rank
            const rankTimeLostMap = new Map();
            data.forEach(d => {
                const currentLost = rankTimeLostMap.get(d.rank) || 0;
                rankTimeLostMap.set(d.rank, currentLost + d.time_lost);
            });

            // Convert the map to an array and sort by time_lost
            const aggregatedData = Array.from(rankTimeLostMap, ([rank, time_lost]) => ({ rank, time_lost }))
                .sort((a, b) => b.time_lost - a.time_lost);

            // Select the top 10 time-losing ranks
            topRanks = aggregatedData.slice(0, 10);
        }

        const width = 900;
        const height = 350;
        const margin = { top: 30, right: 200, bottom: 40, left: 80 };

        // const timeslice_data = Object.entries(timeSlices).map(([key, slice]) => ({
        //     id: key,
        //     duration: slice.ts[1] - slice.ts[0],
        //     time_lost: Number(slice.time_lost)
        // }));

        const xScale = d3.scaleBand()
            .domain(topRanks.map(d => d.rank.toString()))
            .range([margin.left, width - margin.right])
            .padding(0.1);

        const yScale = d3.scaleLinear()
            .domain([0, 100])
            .range([height - margin.bottom, margin.top]);

        const colorScale = d3.scaleSequential(d3.interpolateBlues)
            .domain([0, 100]);

        const svg = d3.select(timeLostViewer.current)
            .attr('width', width)
            .attr('height', height);

        svg.selectAll('*').remove();

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
                .text("Time Lost (%)")
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
            .attr('fill', d => colorScale(d.time_lost / totalRuntime * 100))
            .on('mouseover', function(event, d) {
                d3.select(this).attr('fill', d3.color(colorScale(d.time_lost / totalRuntime * 100)).darker(0.5)); // Darken the color

                tooltip.transition()
                    .duration(200)
                    .style('opacity', .9);

                tooltip.html(`Time Lost: ${formatTime(d.time_lost)} s`)
                    .style('left', (event.pageX + 10) + 'px') // Position tooltip
                    .style('top', (event.pageY - 20) + 'px')
                    .style('color', 'black');
            })
            .on('mouseout', function(event, d) {
                d3.select(this).attr('fill', colorScale(d.time_lost / totalRuntime * 100)); // Reset color

                tooltip.transition()
                    .duration(500)
                    .style('opacity', 0);
            })
            .on('mousemove', function(event) {
                tooltip.style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 20) + 'px');
            });

        newBars.merge(bars)
            .transition()
            .duration(500)
            .attr('y', d => yScale(d.time_lost / totalRuntime * 100))
            .attr('height', d => height - margin.bottom - yScale(d.time_lost / totalRuntime * 100));

    }, [data, selectedSlice, showTimeLostPerSlice, totalRuntime]);

    const getTimeLostForSlice = (slice) => {
        return formatTime(timeSlices[slice].time_lost);
    };

    const handleSliceChange = (value: SliderValue) => {
        setSelectedSlice(Number(value));
    };

    return (
        <div>
            <div style={{ display: "flex", alignItems: "center" }}>
                <h2 style={{ fontSize: '1.5rem', margin: '1rem 0', fontWeight: 'bold' }}>Analysis Viewer</h2>
                <Spacer x={2}/>
                <AnalylsisViewerHelpButton/>
            </div>
            <Switch
                checked={showTimeLostPerSlice}
                onChange={(event) => setShowTimeLostPerSlice(event.target.checked)}
                size="sm"
                color="primary"
            >
                Show Time Lost Per Slice
            </Switch>
            <svg ref={sliceViewer}></svg>
            <svg ref={timeLostViewer}></svg>
            { showTimeLostPerSlice && (
                <Tooltip placement="right" offset={10} content={`Total Time Lost: ${getTimeLostForSlice(selectedSlice)} s`}>
                    <Slider
                        size="sm"
                        step={1}
                        color={selectedSlice == maxTimeLostSlice ? "danger" : "foreground"}
                        label="Slice"
                        marks={[
                            {
                                value: Number(maxTimeLostSlice),
                                label: "!"
                            }
                            ]}
                        showSteps={false}
                        showTooltip={false}
                        onChange={handleSliceChange}
                        maxValue={lastSlice}
                        value={selectedSlice}
                        minValue={0}
                        defaultValue={0}
                        className="max-w-md"
                        style={{ marginLeft: '85px' }}
                    />
                </Tooltip>
            )}
        </div>
    );
};
