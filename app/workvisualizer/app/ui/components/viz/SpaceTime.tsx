import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { CheckboxGroup, Checkbox } from '@nextui-org/react';
import { VisualizationProps } from '@/app/types';

const SpaceTime: React.FC<VisualizationProps> = ({ data }) => {
    const ref = useRef();
    const [visibleTypes, setVisibleTypes] = useState(["collective", "mpi", "kokkos", "other"]);
    const [filteredData, setFilteredData] = useState(data);

    // Update filteredData when visibleTypes change
    useEffect(() => {
        const filtered = data.filter(d => visibleTypes.includes(d.type));
        setFilteredData(filtered);
    }, [data, visibleTypes]);

    useEffect(() => {
        const svg = d3.select(ref.current);
        svg.selectAll("*").remove();

        const width = 928;
        const height = 600;
        const marginTop = 25;
        const marginRight = 20;
        const marginBottom = 35;
        const marginLeft = 40;

        const colorScale = d3.scaleOrdinal()
            .domain(["collective", "mpi", "kokkos", "other"])
            .range(["#1f77b4", "#ff7f0e", "#2ca02c", "#a783c9"]);

        // Define brush for zooming
        var brush = d3.brush()
            .extent([ [0,0], [width, height] ])
            .on("start", disableTooltips)
            .on("end", updateChart);

        const x = d3.scaleLinear()
            .domain(d3.extent(filteredData, d => d.ts))
            .range([marginLeft, width - marginRight]);

        const sortedData = filteredData.sort((a, b) => a.depth - b.depth);
        const uniqueKeys = Array.from(new Set(sortedData.map(d => d.ftn_id)));
        const keyIndexMap = new Map(uniqueKeys.map((key, index) => [key, index]));

        const y = d3.scaleLinear()
            .domain([0, uniqueKeys.length - 1])
            .range([marginTop, height - marginBottom]);

        svg.attr("viewBox", [0, 0, width, height])
           .attr("style", "max-width: 100%; height: auto; font: 10px sans-serif;");

        var xAxis = svg.append("g")
            .attr("transform", `translate(0,${height - marginBottom})`)
            .call(d3.axisBottom(x).ticks(width / 80))
            .call(g => g.select(".domain"))
            .call(g => g.append("text")
                .attr("x", width / 2)
                .attr("y", marginBottom - 4)
                .attr("fill", "currentColor")
                .attr("text-anchor", "center")
                .text("Function Begin Time (s)"));

        var yAxis = svg.append("g")
            .call(d3.axisLeft(y).tickValues([]))
            .call(g => g.select(".domain").remove())
            .call(g => g.append("text")
                .attr("x", -height / 2 + 50)
                .attr("y", marginLeft - 10)
                .attr("fill", "currentColor")
                .attr("text-anchor", "center")
                .attr("transform", "rotate(-90)")
                .text("<-- Depth in the Path <--"));

        // Add brushing
        svg.append("g")
            .attr("class", "brush")
            .call(brush);

        // Define a function to format the begin, end, and duration times
        function formatTime(time) {
            if (time < 0.0001) {
                return time.toExponential(2);
            } else {
                return time.toFixed(6);
            }
        }

        // Define a function for what happens when mousing over a data point
        var mouseenter = function(event, d) {

            // Enlarge the selected data point and outline in white
            d3.select(this).raise();
            d3.select(this).transition()
                .duration('50')
                .attr("r", 6)
                .attr("stroke", "white");

            // Define the text in the tooltip
            var tooltip_text = `${d.name}\n
            Start: ${formatTime(d.ts)} s\n
            End: ${formatTime(d.ts + d.dur)} s\n
            Duration: ${formatTime(d.dur)} s\n
            Rank: ${d.rank}`;
            if ("src" in d) {
                tooltip_text += `\nSource: ${d.src}`;
            }
            if ("dst" in d) {
                tooltip_text += `\nDestination: ${d.dst}`;
            }
            if (d.depth > 0) {
                tooltip_text += `\nPath: ${d.path}`;
            }
            const [mx, my] = d3.pointer(event);
            const lineHeight = 10;
            const y_pos = my < (marginBottom + height) / 2 ? 10 : -80;
            tooltip
                .attr("transform", `translate(${mx}, ${my})`)
                .selectAll("tspan")
                .data(tooltip_text.split("\n"))
                .join("tspan")
                .attr("x", mx < (marginLeft + width)/2 ? "20px" : "-250px")
                .attr("y", (d, i) => y_pos + i * lineHeight)
                .text((text) => text );
        }

        // Define a function for when the mouse leaves a data point
        var mouseleave = function (d, i) {

            d3.select(this).lower();
            // Shrink the data point back to its original size and remove the outline
            d3.select(this).transition()
                .duration('100')
                .attr("r", 3)
                .attr("stroke", "none");

            // Make the tooltip invisible
            tooltip.text("")
            // tooltip.style("opacity", 0);
        }

        // Draw horizontal lines for depth levels
        svg.selectAll(".depth-line")
            .data(Array.from(new Set(sortedData.map(d => d.depth))))
            .enter().append("line")
            .attr("class", "depth-line")
            .attr("x1", marginLeft)
            .attr("x2", width - marginRight)
            .attr("y1", d => {
                const firstInDepth = sortedData.find(item => item.depth === d);
                return y(keyIndexMap.get(firstInDepth.ftn_id));
            })
            .attr("y2", d => {
                const firstInDepth = sortedData.find(item => item.depth === d);
                return y(keyIndexMap.get(firstInDepth.ftn_id));
            })
            .attr("stroke", "currentColor")
            .attr("stroke-opacity", 0.3)
            .attr("stroke-width", 2);

        svg.append("g")
            .attr("stroke-width", 1.5)
            .selectAll("circle")
            .data(filteredData)
            .enter().append("circle")
            .attr("cx", d => x(d.ts))
            .attr("cy", d => y(keyIndexMap.get(d.ftn_id)))
            .attr("r", 3)
            .attr("fill", d => colorScale(d.type))
            .on('mouseenter', mouseenter)
            .on('mouseleave', mouseleave);

        // Try a different tooltip technique
        const tooltip = svg
            .append("text")
            .attr("class", "tooltip")
            .attr("fill", "currentColor")
            .style("pointer-events", "none")
            .style("font-size", "12px")
            .style("font-weight", "bold");

        // A function that set idleTimeOut to null
        var idleTimeout;
        function idled() { idleTimeout = null; }

        // Stack to keep track of zoom states
        var zoomStack = [];

        // A function that update the chart for given boundaries
        function updateChart({selection}) {

            disableTooltips;

            // If no selection, back to initial coordinate. Otherwise, update X and Y domains
            if (!selection) {
                if (!idleTimeout) return idleTimeout = setTimeout(idled, 350);
                x.domain(d3.extent(data, d => d.ts));
                y.domain(d3.extent(data, d => keyIndexMap.get(d.ftn_id)));
            } else {

                const zoomState = {
                    xDomain: x.domain(),
                    yDomain: y.domain()
                };
                zoomStack.push(zoomState);

                // Update x and y domains based on brush selection
                x.domain([x.invert(selection[0][0]), x.invert(selection[1][0])]);
                y.domain([y.invert(selection[0][1]), y.invert(selection[1][1])]);

                // Clear the brush
                svg.select(".brush").call(brush.move, null)
            }

            // Update axis and circle position
            xAxis.transition().duration(750).call(d3.axisBottom(x).ticks(width / 80));
            yAxis.transition().duration(750).call(d3.axisLeft(y)).call(g => g.select(".domain").remove());
            svg.selectAll("circle")
                .transition().duration(750)
                .attr("cx", d => x(d.ts))
                .attr("cy", d => y(keyIndexMap.get(d.ftn_id)))
                .on("end", function() {
                    // Re-enable mouse events after transition ends
                    d3.select(this).style("pointer-events", "all");
                });
            // Update depth lines
            svg.selectAll(".depth-line")
                .transition().duration(750)
                .attr("y1", d => {
                    const firstInDepth = sortedData.find(item => item.depth === d);
                    return y(keyIndexMap.get(firstInDepth.ftn_id));
                })
                .attr("y2", d => {
                    const firstInDepth = sortedData.find(item => item.depth === d);
                    return y(keyIndexMap.get(firstInDepth.ftn_id));
                });
        }

        svg.on("dblclick", () => {
            disableTooltips;
            if (zoomStack.length > 0) {
                const lastZoomState = zoomStack.pop();
                x.domain(lastZoomState.xDomain);
                y.domain(lastZoomState.yDomain);

                xAxis.transition().duration(750).call(d3.axisBottom(x).ticks(width / 80));
                yAxis.transition().duration(750).call(d3.axisLeft(y)).call(g => g.select(".domain").remove());
                svg.selectAll("circle")
                    .transition().duration(750)
                    .attr("cx", d => x(d.ts))
                    .attr("cy", d => y(keyIndexMap.get(d.ftn_id)))
                    .on("end", function() {
                        d3.select(this).style("pointer-events", "all");
                    });
            }
            enableTooltips;
        });

        // Simple function to disable tooltips during transitions
        function disableTooltips() {
            svg.selectAll("circle").style("pointer-events", "none");
        }

        // Simple function to enable tooltips during transitions
        function enableTooltips() {
            svg.selectAll("circle").style("pointer-events", "all");
        }

    }, [filteredData]);

    const handleCheckboxChange = (values) => {
        setVisibleTypes(values);
    };

    return (
        <div>
            <CheckboxGroup
                size="sm"
                orientation="horizontal"
                color="primary"
                defaultValue={visibleTypes}
                onChange={handleCheckboxChange}
            >
                <Checkbox color="primary" value="collective">MPI Collective</Checkbox>
                <Checkbox color="warning" value="mpi">MPI Point-To-Point</Checkbox>
                <Checkbox color="success" value="kokkos">Kokkos</Checkbox>
                <Checkbox color="secondary" value="other">Application</Checkbox>
            </CheckboxGroup>
            <svg ref={ref} width={928} height={600} />
        </div>
    );
};

export default SpaceTime;
