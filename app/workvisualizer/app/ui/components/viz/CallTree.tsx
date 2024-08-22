'use client'
import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export const dataRequirements = {
    endpoint: '/api/logical_hierarchy/-1', // API endpoint for this component's data
    params: {} // Additional parameters if needed
};

const CallTree = ({ data }) => {
    const ref = useRef();

    useEffect(() => {
        const svg = d3.select(ref.current);
        svg.selectAll('*').remove();

        const format = d3.format(",");
        const nodeSize = 22;
        const root = d3.hierarchy(data).eachBefore((i => d => d.index = i++)(0));
        const nodes = root.descendants();
        const width = 928;
        const height = (nodes.length + 1) * nodeSize;

        // Define color scale for different types
        const colorScale = d3.scaleOrdinal()
            .domain(["mpi_collective", "mpi_p2p", "kokkos", "other"])
            .range(["#1f77b4", "#f5a524", "#2ca02c", "#a783c9"]);

        const columns = [
            {
                label: "Seconds Spent in Kernel",
                value: d => d.dur,
                format,
                x: 580
            },
            {
                label: "# of Instances",
                value: d => d.count,
                format: (value, d) => d.count ? format(value) : "-",
                x: 700
            }
        ];

        svg
            .attr("width", width)
            .attr("height", height)
            .attr("viewBox", [-nodeSize / 2, -nodeSize * 3 / 2, width, height])
            .attr("style", "max-width: 100%; height: auto; font: 12px sans-serif; overflow: visible;");

        svg.append("style")
            .text(`
            .highlighted text {
                font-weight: bold; /* Make the text bold */
            }
            `);

        const link = svg.append("g")
            .attr("fill", "none")
            .attr("stroke", "#999")
            .selectAll()
            .data(root.links())
            .join("path")
            .attr("d", d => `
                M${d.source.depth * nodeSize},${d.source.index * nodeSize}
                V${d.target.index * nodeSize}
                h${nodeSize}
            `);

        const node = svg.append("g")
            .selectAll()
            .data(nodes)
            .join("g")
            .attr("transform", d => `translate(0,${d.index * nodeSize})`);

        node.append("circle")
            .attr("cx", d => d.depth * nodeSize)
            .attr("r", 2.5)
            .attr("fill", d => d.children ? "currentColor" : "#999");

        node.append("text")
            .attr("dy", "0.32em")
            .attr("fill", d => d.children ? "currentColor" : "#999")
            .attr("x", d => d.depth * nodeSize + 6)
            .text(d => d.data.name);

        node.append("title")
            .text(d => d.ancestors().reverse().map(d => d.data.name).join("/"));

        for (const { label, value, format, x } of columns) {
            svg.append("text")
                .attr("dy", "0.32em")
                .attr("y", -nodeSize)
                .attr("x", x)
                .attr("text-anchor", "end")
                .attr("font-weight", "bold")
                .attr("fill", "currentColor")
                .text(label);

            node.append("text")
                .attr("dy", "0.32em")
                .attr("x", x)
                .attr("text-anchor", "end")
                .attr("fill", d => d.children ? "currentColor" : "#999")
                .data(root.copy().sum(value).descendants())
                .text(d => format(d.value, d));
        }

        node.on("click", clicked);

        function clicked(event, d) {
            const isHighlighted = d3.select(this).classed("highlighted");

            // Remove highlight from previously highlighted nodes
            svg.selectAll(".highlighted")
                .classed("highlighted", false)
                .selectAll("text")
                .attr("fill", d => d.children ? "currentColor" : "#999");

            if (!isHighlighted) {
                d3.select(this)
                    .classed("highlighted", true)
                    .raise(); // Bring the highlighted node to the front

                d3.select(this).selectAll("text")
                    .attr("fill", colorScale(d.data.type));
            } else {
                d3.select(this)
                    .classed("highlighted", false);

                d3.select(this).selectAll("text")
                    .attr("fill", d => d.children ? "currentColor" : "#999");
            }
        }

    }, [data]);

    return (
        <svg ref={ref} width={928} height={1000} />
    );
};

export default CallTree;
