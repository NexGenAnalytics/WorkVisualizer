import React from 'react';
import {Table, TableHeader, TableColumn, TableBody, TableRow, TableCell} from "@nextui-org/react";


// Assuming timeSlices is your input dictionary
export default function AnalysisTable({ timeSlices, summaryData }) {
    // Define a function for formatting the percentage
    function formatPct(pct) {
        pct = pct * 100;
        if (pct < 0.0001) {
            return "< 0.0001"
        } else {
            if (pct >= 0.01) {
                return pct.toFixed(2);
            }
            return pct.toFixed(3);
        }
    }

    // Extract summary info
    const numRanks = summaryData["mpi.world.size"];
    const totalRuntime = summaryData["program.runtime"]

    // Calculate the longest slice and the most time-losing rank
    let longestSlice = null;
    let longestLength = 0.;
    let mostTimeLosingRank = '';
    let mostTimeLosingRankSlice = '';
    let timeLostByMostTimeLosingRank = 0.;
    let timeLostByMostTimeLosingSlice = 0.;
    let mostTimeLosingSlice = null;
    let maxTimeLost = Number.NEGATIVE_INFINITY;
    let totalTimeLost = 0.;

    // Iterate through timeSlices to find the longest slice and most time-losing rank
    for (const key in timeSlices) {
        const slice = timeSlices[key];
        const sliceLength = slice.ts[1] - slice.ts[0];

        // Update longestSlice if the current slice is longer
        if (sliceLength > longestLength) {
            longestSlice = key;
            longestLength = sliceLength;
        }

        // Determine the most time-losing slice
        const timeLostValue = parseFloat(slice.time_lost);
        if (timeLostValue > maxTimeLost) {
            totalTimeLost += timeLostValue;
            maxTimeLost = timeLostValue;
            mostTimeLosingSlice = key;
            timeLostByMostTimeLosingSlice = maxTimeLost;
        }

        // Check if there's a significant time-losing rank in statistics
        for (const rank in slice.statistics) {
            if (rank) { // Check if rank is not empty
                mostTimeLosingRank = rank;
                mostTimeLosingRankSlice = key;
                timeLostByMostTimeLosingRank = Number(slice.statistics[rank]);
                break; // Break after finding the first significant rank
            }
        }

        console.log("mostTimeLosingRank: ", mostTimeLosingRank)
        console.log("timeLostByMostTimeLosingRank: ", timeLostByMostTimeLosingRank)
        console.log("timeLostByMostTimeLosingSlice: ", timeLostByMostTimeLosingSlice)
    }

    const pctLost = ( totalTimeLost / numRanks ) / totalRuntime
    const pctLostByMostTimeLosingRank = timeLostByMostTimeLosingRank / totalRuntime;
    const pctLostByMostTimeLosingSlice = timeLostByMostTimeLosingSlice / totalRuntime;

    return (
        <div>
            <Table
                hideHeader
                removeWrapper
                selectionMode="single"
                defaultSelectedKeys={[]}
                aria-label="Analysis Summary"
            >
                <TableHeader>
                    <TableColumn>Description</TableColumn>
                    <TableColumn>Statistic</TableColumn>
                </TableHeader>
                <TableBody>
                    <TableRow key="1">
                        <TableCell>Most Time-Losing Slice</TableCell>
                        <TableCell>{mostTimeLosingSlice || 'None'}</TableCell>
                    </TableRow>
                    <TableRow key="2">
                        <TableCell>Most Time-Losing Rank</TableCell>
                        <TableCell>{`Rank ${mostTimeLosingRank} on Slice ${mostTimeLosingRankSlice}`}</TableCell>
                    </TableRow>
                    <TableRow key="3">
                        <TableCell>Longest Slice</TableCell>
                        <TableCell>{longestSlice}</TableCell>
                    </TableRow>
                    {/* <TableRow key="4">
                        <TableCell>{`% of Total Runtime Lost on Rank ${mostTimeLosingRank}`}</TableCell>
                        <TableCell>{formatPct(pctLostByMostTimeLosingRank)}%</TableCell>
                    </TableRow>
                    <TableRow key="5">
                        <TableCell>% of Total Runtime Lost Across All Ranks</TableCell>
                        <TableCell>{formatPct(pctLost)}%</TableCell>
                    </TableRow> */}
                </TableBody>
            </Table>
            {/* <h3>Time Lost Breakdown</h3>
            <Table
                hideHeader
                removeWrapper
                selectionMode="single"
                defaultSelectedKeys={[]}
                aria-label="Time Lost Breakdown"
            >
                <TableHeader>
                    <TableColumn>Description</TableColumn>
                    <TableColumn>Statistic</TableColumn>
                </TableHeader>
                <TableBody>
                    <TableRow key="4">
                        <TableCell>{`% of Total Runtime Lost on Rank ${mostTimeLosingRank}`}</TableCell>
                        <TableCell>{formatPct(pctLostByMostTimeLosingRank)}%</TableCell>
                    </TableRow>
                    <TableRow key="5">
                        <TableCell>% of Total Runtime Lost Across All Ranks</TableCell>
                        <TableCell>{formatPct(pctLost)}%</TableCell>
                    </TableRow>
                </TableBody>
            </Table> */}
        </div>
    );
};
