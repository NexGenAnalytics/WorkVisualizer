'use client'
import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export const dataRequirements = {
    endpoint: '/api/global_hierarchy', // API endpoint for this component's data
    params: {} // Additional parameters if needed
};

const GlobalSunBurst = ({ data }) => {
    const ref = useRef();

    useEffect(() => {
        const svg = d3.select(ref.current);
        svg.selectAll('*').remove();

        // Specify the chart’s dimensions.
        const width = 928;
        const height = width;
        const radius = width / 6;

        // Create the color scale.
        // const color = d3.scaleOrdinal(d3.quantize(d3.interpolateRainbow, data.children.length + 1));
        const color = d3.scaleOrdinal(d3.quantize(d3.interpolateTurbo, data.children.length + 1).reverse());

        // Compute the layout.
        const hierarchy = d3.hierarchy(data)
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
            .outerRadius(d => Math.max(d.y0 * radius, d.y1 * radius - 1))

        // Create the SVG container.
        svg
            .attr("viewBox", [-width / 2, -height / 2, width, width])
            .style("font", "10px sans-serif");

        // Append the arcs.
        const path = svg.append("g")
            .selectAll("path")
            .data(root.descendants().slice(1))
            .join("path")
            .attr("fill", d => { while (d.depth > 1) d = d.parent; return color(d.value); })
            .attr("fill-opacity", d => arcVisible(d.current) ? (d.children ? 0.9 : 0.7) : 0)
            .attr("pointer-events", d => arcVisible(d.current) ? "auto" : "none")

            .attr("d", d => arc(d.current));

        // Make them clickable if they have children.
        path.filter(d => d.children)
            .style("cursor", "pointer")
            // .on("mouseenter", mouseenter)
            // .on("mouseleave", mouseleave)
            .on("click", clicked);

        const format = d3.format(",d");
        path.append("title")
            .text(d => `${d.ancestors().map(d => d.data.name).reverse().join("/")}\n${d.data.count} calls\nAverage Duration Per Call ${d.data.dur / d.data.count} s\n`);

        // const label = svg.append("g")
        //     .attr("pointer-events", "none")
        //     .attr("text-anchor", "middle")
        //     .style("user-select", "none")
        //   .selectAll("text")
        //   .data(root.descendants().slice(1))
        //   .join("text")
        //     .attr("dy", "0.35em")
        //     .attr("fill-opacity", d => +labelVisible(d.current))
        //     .attr("transform", d => labelTransform(d.current))
        //     .text(d => d.data.name);

        const parent = svg.append("circle")
            .datum(root)
            .attr("r", radius)
            .attr("fill", "none")
            .attr("pointer-events", "all")
            .on("click", clicked);

        // parent.append("text")
        //     .attr("dy", ".35em")
        //     .style("text-anchor", "middle")
        //     .style("font-size", "16px")
        //     .text("testing");

        // Handle zoom on click.
        function clicked(event, p) {
            d3.select(this).style("pointer-events", "none");
            parent.datum(p.parent || root);
            // parent.select("text")
            //   .text(p.parent ? p.parent.data.name : "");

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

                .attrTween("d", d => () => arc(d.current));
            // label.filter(function(d) {
            //     return +this.getAttribute("fill-opacity") || labelVisible(d.target);
            //   }).transition(t)
            //     .attr("fill-opacity", d => +labelVisible(d.target))
            //     .attrTween("transform", d => () => labelTransform(d.current));
            d3.select(this).style("pointer-events", "all");
        }

        function mouseenter(event, d) {
          d3.select(this).transition()
              .duration("50")
              .attr("stroke", "white")
              .attr("stroke-width", 1);
        }

        function mouseleave(event, d) {
          d3.select(this).transition()
              .duration("50")
              .attr("stroke", "none")
        }

        function arcVisible(d) {
            return d.y1 <= 3 && d.y0 >= 1 && d.x1 > d.x0;
        }

        function labelVisible(d) {
            return d.y1 <= 3 && d.y0 >= 1 && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.03;
        }

        function labelTransform(d) {
            const x = (d.x0 + d.x1) / 2 * 180 / Math.PI;
            const y = (d.y0 + d.y1) / 2 * radius;
            return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
        }
    }, [data]);

    return (
        <svg ref={ref} width={928} height={928} />
    );
};

export default GlobalSunBurst;
