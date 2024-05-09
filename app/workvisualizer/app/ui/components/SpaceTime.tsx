'use client'
import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const SpaceTime = ({ data }) => {
    const ref = useRef();

    useEffect(() => {
        const svg = d3.select(ref.current);
        svg.selectAll("*").remove();

        // Specify the chart’s dimensions.
        const width = 928;
        const height = 600;
        const marginTop = 25;
        const marginRight = 20;
        const marginBottom = 35;
        const marginLeft = 40;

        // Define color scale for different types
        const colorScale = d3.scaleOrdinal()
            .domain(["collective", "mpi", "kokkos"])
            .range(["#1f77b4","#ff7f0e","#2ca02c"]);

        // Define brush for zooming
        var brush = d3.brush()
            .extent([ [0,0], [width, height] ])
            .on("end", updateChart);

        // console.log(data)
        // console.log(d3.extent(data, (d) => d.begin_time));

        // Prepare the scales for positional encoding.
        const x = d3.scaleLinear()
            .domain(d3.extent(data, d => d.begin_time))
            .range([marginLeft, width - marginRight]);

        const y = d3.scaleLinear()
            .domain(d3.extent(data, d => d.y_value))
            .range([height - marginBottom, marginTop]);

        // Create the SVG container.
        svg.attr("viewBox", [0, 0, width, height])
           .attr("style", "max-width: 100%; height: auto; font: 10px sans-serif;");

        // Try a different tooltip technique
        const tooltip = svg
           .append("text")
           .attr("class", "tooltip")
           .attr("fill", "white")
           .style("pointer-events", "none");
        // try this in the future: https://stackoverflow.com/questions/35652760/styling-d3%C2%B4s-tooltip

        // Wrap the SVG with a container that has the html element above it
        // const container = html`<div>
        // <style>.tooltip {
        //     font: sans-serif 12pt;
        //     background: #eeeeeeee;
        //     pointer-events: none;
        //     border-radius: 2px;
        //     padding: 5px;
        //     position: absolute;
        //     top: 0px;
        //     left: 0px;
        //     z-index: 1;

        // }</style>

        // <div class="tooltip"></div>
        // ${svg.node()}

        // </div>`

        // Create the axes.
        var xAxis = svg.append("g")
            .attr("transform", `translate(0,${height - marginBottom})`)
            .call(d3.axisBottom(x).ticks(width / 80))
            .call(g => g.select(".domain"))
            .call(g => g.append("text")
                .attr("x", width)
                .attr("y", marginBottom - 4)
                .attr("fill", "currentColor")
                .attr("text-anchor", "end")
                .text("Function Begin Time (s) →"));

        var yAxis = svg.append("g")
            .call(d3.axisLeft(y).tickValues([]))
            .call(g => g.select(".domain").remove())
            .call(g => g.append("text")
                .attr("x", marginLeft)
                .attr("y", height));

        // Create the grid.
        // svg.append("g")
        //   .attr("stroke", "currentColor")
        //   .attr("stroke-opacity", 0.1)
        //   .call(g => g.append("g")
        //     .selectAll("line")
        //     .data(x.ticks())
        //     .join("line")
        //       .attr("x1", d => 0.5 + x(d))
        //       .attr("x2", d => 0.5 + x(d))
        //       .attr("y1", marginTop)
        //       .attr("y2", height - marginBottom))
        //   .call(g => g.append("g")
        //     .selectAll("line")
        //     .data(y.ticks())
        //     .join("line")
        //       .attr("y1", d => 0.5 + y(d))
        //       .attr("y2", d => 0.5 + y(d))
        //       .attr("x1", marginLeft)
        //       .attr("x2", width - marginRight));

        // Add brushing
        svg.append("g")
            .attr("class", "brush")
            .call(brush);

        // Define a clip to hide any data points outside of the brushed window
        svg.append("defs").append("svg:clipPath")
            .attr("id", "clip")
            .append("svg:rect")
            .attr("id", "clip-rect")
            .attr("x", marginLeft)
            .attr("y", marginBottom - 4)
            .attr('width', width - marginLeft - marginRight)
            .attr('height', height - marginBottom - marginTop);
        svg.append("g").attr("clip-path", "url(#clip)")

        // A selection for the tooltip
        // const tooltip = d3.select(container).select(".tooltip");

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
            const [mx, my] = d3.pointer(event);
            // Enlarge the selected data point and outline in white
            d3.select(this).transition()
                .duration('50')
                .attr("r", 6)
                .attr("stroke", "white");

                // Define the text in the tooltip
            var tooltip_text = `${d.name}\n
                                Start: ${formatTime(d.begin_time)} s\n
                                End: ${formatTime(d.end_time)} s\n
                                Duration: ${formatTime(d.duration)} s`;
            if ("src" in d) {
            tooltip_text += `\nSource: ${d.src}`;
            }
            if ("dst" in d) {
            tooltip_text += `\nDestination: ${d.dst}`;
            }
            if (d.path.length > 0) {
            tooltip_text += `\nPath: ${d.path}`;
            }

            tooltip
                .attr("transform", `translate(${mx}, ${my})`)
                .selectAll("tspan")
                .data(tooltip_text.split("\n"))
                .join("tspan")
                .attr("dy", "2em")
                .attr("x", "0px")
                .text((text) => text );

            // Define the text in the tooltip
            // var tooltip_text = `<b>${d.name}</b><br>
            //                     Start: ${formatTime(d.begin_time)} s<br>
            //                     End: ${formatTime(d.end_time)} s<br>
            //                     Duration: ${formatTime(d.duration)} s`;
            // if ("src" in d) {
            // tooltip_text += `<br>Source: ${d.src}`;
            // }
            // if ("dst" in d) {
            // tooltip_text += `<br>Destination: ${d.dst}`;
            // }
            // if (d.path.length > 0) {
            // tooltip_text += `<br>Path: ${d.path}`;
            // }

            // // Make the tooltip visible and position correctly
            // const [mx, my] = d3.pointer(event);
            // tooltip
            // .style("opacity", 1)
            // .style("top", (my - 50) + "px")
            // .style("left", (mx + 90) + "px")
            // .html(tooltip_text);
        }

        // Define a function for when the mouse leaves a data point
        var mouseleave = function (d, i) {

            // Shrink the data point back to its original size and remove the outline
            d3.select(this).transition()
            .duration('100')
            .attr("r", 3)
            .attr("stroke", "none");

            // Make the tooltip invisible
            tooltip.text("")
            // tooltip.style("opacity", 0);
        }

        // Add a layer of dots
        svg.append("g")
            .attr("stroke-width", 1.5)
            .selectAll("circle")
            .data(data)
            .join("circle")
            .attr("cx", d => x(d.begin_time))
            .attr("cy", d => y(d.y_value))
            .attr("r", 3)
            .attr("fill", d => colorScale(d.type))
            .on('mouseenter', mouseenter)
            .on('mouseleave', mouseleave);

        // A function that set idleTimeOut to null
        var idleTimeout
        function idled() { idleTimeout = null; }

        // A function that update the chart for given boundaries
        function updateChart({selection}) {

            // If no selection, back to initial coordinate. Otherwise, update X and Y domains
            if (!selection) {
            if (!idleTimeout) return idleTimeout = setTimeout(idled, 350);
            x.domain(d3.extent(data, d => d.begin_time));
            y.domain(d3.extent(data, d => d.y_value));
            } else {
            // Update x and y domains based on brush selection
            x.domain([x.invert(selection[0][0]), x.invert(selection[1][0])]);
            y.domain([y.invert(selection[1][1]), y.invert(selection[0][1])]);
            // Clear the brush
            svg.select(".brush").call(brush.move, null)
            }

            // Update axis and circle position
            xAxis.transition().duration(750).call(d3.axisBottom(x).ticks(width / 80));
            yAxis.transition().duration(750).call(d3.axisLeft(y)).call(g => g.select(".domain").remove());
            svg.selectAll("circle")
            .transition().duration(750)
            .attr("cx", d => x(d.begin_time))
            .attr("cy", d => y(d.y_value));
        }
    }, [data]);

    return (
        <svg ref={ref} width={928} height={600} />
    );
};

export default SpaceTime;



    // function _data(FileAttachment){return(
    // FileAttachment("md_0r_100s_pruned_scatter@2.json").json()
    // )}

    // export default function define(runtime, observer) {
    //   const main = runtime.module();
    //   function toString() { return this.url; }
    //   const fileAttachments = new Map([
    //     ["md_0r_100s_pruned_scatter@2.json", {url: new URL("./files/42249c67dd3cc7eff4336c629104489fee871777ef74a311e7895db60cf99e82ee828ca565c93e37e076d64a65b9f33af102a4d7286e9e79c58f216e33c2644d.json", import.meta.url), mimeType: "application/json", toString}]
    //   ]);
    //   main.builtin("FileAttachment", runtime.fileAttachments(name => fileAttachments.get(name)));
    //   main.variable(observer()).define(["md"], _1);
    //   main.variable(observer("chart")).define("chart", ["d3","data","html"], _chart);
    //   main.variable(observer("data")).define("data", ["FileAttachment"], _data);
    //   return main;
    // }