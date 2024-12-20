'use client'
import { useEffect, useRef, useState } from 'react';
import {Accordion, AccordionItem} from "@nextui-org/accordion";
import * as d3 from 'd3';
import { CheckboxGroup, Checkbox, Spacer, Switch } from '@nextui-org/react';
import ProportionAnalyzerHelpButton from '@/app/ui/components/help/ProportionAnalyzerHelpButton';

export const dataRequirements = {
    endpoint: '/api/logical_hierarchy/-1', // API endpoint for this component's data
    params: {}                             // Additional parameters if needed
};

const GlobalSunBurst = ({ data, rank }) => {
    const ref = useRef();
    const [visibleTypes, setVisibleTypes] = useState(["mpi_collective", "mpi_p2p", "kokkos", "other"]);
    const [showImbalance, setShowImbalance] = useState(false);

    useEffect(() => {
        const svg = d3.select(ref.current);
        svg.selectAll('*').remove();

        // Specify the chart’s dimensions.
        const width = 700;
        const height = width;
        const radius = width / 6;

        // Create the color scale.
        const colorScale = d3.scaleOrdinal()
            .domain(["mpi_collective", "mpi_p2p", "kokkos", "other"])
            .range(["#1f77b4", "#f5a524", "#2ca02c", "#a783c9"]);

        // Filter data to include only nodes with visible types
        const filterData = (node) => {
            if (!node.children) {
                return visibleTypes.includes(node.type) ? { ...node } : null;
            }

            // If the node's type is in visibleTypes, recursively filter its children
            const children = node.children.map(filterData).filter(d => d);
            return { ...node, children };
        };

        const filteredData = filterData(data);

        // Compute the layout.
        const hierarchy = d3.hierarchy(filteredData)
            .sum(d => Math.sqrt(d.dur))
            .sort((a, b) => b.value - a.value);
        const root = d3.partition()
            .size([2 * Math.PI, hierarchy.height + 1])
        (hierarchy);
        root.each(d => d.current = d);

        // Create the arc generator.
        const arc = d3.arc()
            .startAngle(d => d.x0)
            .endAngle(d => d.x1)
            .padAngle(d => Math.min((d.x1 - d.x0) / 2, 0.005))
            .padRadius(radius * 1.5)
            .innerRadius(d => d.y0 * radius)
            .outerRadius(d => Math.max(d.y0 * radius, d.y1 * radius - 1));

        // Create the SVG container.
        svg
            .attr("viewBox", [-width / 2, -height / 2, width, width])
            .style("font", "10px sans-serif");

        // Append the arcs.
        const path = svg.append("g")
            .selectAll("path")
            .data(root.descendants().slice(1))
            .join("path")
            .attr("stroke-width", d => showImbalance ? (d.data.imbalance ? 2 : "none") : "none")
            .attr("stroke", d => showImbalance ? (d.data.imbalance ? "#da0b54" : "none") : "none")
            .attr("fill", d => colorScale(d.data.type))
            .attr("fill-opacity", d => arcVisible(d.current) ? (d.children ? 0.9 : 0.7) : 0)
            .attr("pointer-events", d => arcVisible(d.current) ? "auto" : "none")
            .attr("d", d => arc(d.current));

        // Make them clickable if they have children.
        path.filter(d => d.children)
            .style("cursor", "pointer")
            // .on("mouseenter", mouseenter)
            // .on("mouseleave", mouseleave)
            .on("click", clicked);

        path.append("title")
        .text(d => {
            const imbalanceInfo = d.data.imbalance
                ? (Array.isArray(d.data.imbalance)
                    ? "\nImbalance:\n" + d.data.imbalance.map(entry => {
                        const rank = Object.keys(entry)[0];
                        const percentDiff = entry[rank] * 100; // convert to percentage
                        return `  Rank ${rank}: ${percentDiff.toFixed(2)}%`;
                    }).join("\n")
                    : `\nImbalance: ${(d.data.imbalance * 100).toFixed(2)}%` // convert to percentage
                )
                : "";

            return `${d.ancestors().map(d => d.data.name).reverse().join("/")}\nTotal Time: ${d.data.dur} s\n${d.data.count} calls\nAverage Duration Per Call: ${d.data.dur / d.data.count} s${imbalanceInfo}`;
        });

        const parent = svg.append("circle")
            .datum(root)
            .attr("r", radius)
            .attr("fill", "none")
            .attr("pointer-events", "all")
            .on("click", clicked);

        // Handle zoom on click.
        function clicked(event, p) {
            parent.datum(p.parent || root);

            root.each(d => d.target = {
            x0: Math.max(0, Math.min(1, (d.x0 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
            x1: Math.max(0, Math.min(1, (d.x1 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
            y0: Math.max(0, d.y0 - p.depth),
            y1: Math.max(0, d.y1 - p.depth)
            });

            const t = svg.transition().duration(750);

            // Transition the data on all arcs, even the ones that aren’t visible,
            // so that if this transition is interrupted, entering arcs will start
            // the next transition from the desired position.
            path.transition(t)
                .tween("data", d => {
                    const i = d3.interpolate(d.current, d.target);
                    return t => d.current = i(t);
                })
                .filter(function(d) {
                    return +this.getAttribute("fill-opacity") || arcVisible(d.target);
                 })
                .attr("fill-opacity", d => arcVisible(d.target) ? (d.children ? 0.9 : 0.7) : 0)
                .attr("pointer-events", d => arcVisible(d.target) ? "auto" : "none")
                .attr("stroke", d => showImbalance ? (arcVisible(d.target) ? (d.data.imbalance ? "#da0b54" : "none") : "none") : "none")
                .attrTween("d", d => () => arc(d.current));
        }

        function mouseenter(event, d) {
          d3.select(this).transition()
              .duration("50")
              .attr("stroke", "white")
              .attr("stroke-width", 1);
        }

        function arcVisible(d) {
            return d.y1 <= 3 && d.y0 >= 1 && d.x1 > d.x0;
        }

    }, [data, rank, visibleTypes, showImbalance]);

    const handleCheckboxChange = (values) => {
        setVisibleTypes(values);
    };

    const handleImbalanceToggle = () => {
        setShowImbalance(prevState => !prevState)
    }

    return (
        <div>
            <div style={{ display: "flex", alignItems: "center" }}>
                <h2 style={{ fontSize: "1.5rem", margin: "1rem 0", fontWeights: "bold"}}>
                    Proportion Analyzer
                </h2>
                <Spacer x={2}/>
                <ProportionAnalyzerHelpButton/>
            </div>
            <CheckboxGroup
                size="sm"
                orientation="horizontal"
                color="primary"
                defaultValue={visibleTypes}
                onChange={handleCheckboxChange}
            >
                <Checkbox color="primary" value="mpi_collective">MPI Collective</Checkbox>
                <Checkbox color="warning" value="mpi_p2p">MPI Point-To-Point</Checkbox>
                <Checkbox color="success" value="kokkos">Kokkos</Checkbox>
                <Checkbox color="secondary" value="other">Application</Checkbox>
            </CheckboxGroup>
            <Spacer y={5}/>
            <svg ref={ref} width={700} height={700} />
            <p><i>Rank {rank}</i></p>
        </div>
    );
};

export default GlobalSunBurst;
