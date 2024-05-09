'use client'
import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const BarChart = ({ data }) => {
    const ref = useRef();

    useEffect(() => {
        const svg = d3.select(ref.current);
        svg.selectAll('*').remove();
        const width = 500;
        const height = 300;
        const margin = { top: 20, right: 20, bottom: 30, left: 40 };

        const x = d3.scaleBand()
            .domain(data.map(d => d.month))
            .rangeRound([margin.left, width - margin.right])
            .padding(0.1);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.sales)]).nice()
            .range([height - margin.bottom, margin.top]);

        const xAxis = g => g
            .attr('transform', `translate(0,${height - margin.bottom})`)
            .call(d3.axisBottom(x).tickSizeOuter(0));

        const yAxis = g => g
            .attr('transform', `translate(${margin.left},0)`)
            .call(d3.axisLeft(y));

        svg.append('g').call(xAxis);
        svg.append('g').call(yAxis);

        svg.append('g')
            .attr('fill', 'steelblue')
            .selectAll('rect').data(data).enter().append('rect')
            .attr('x', d => x(d.month))
            .attr('y', d => y(d.sales))
            .attr('height', d => y(0) - y(d.sales))
            .attr('width', x.bandwidth());
    }, [data]);

    return (
        <svg ref={ref} width={500} height={300} />
    );
};

export default BarChart;
