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

    // Determine the threshold for a "signficant" number of lossy ranks
    const signficantThreshold = numRanks * 0.1

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
    let numRanksWithSignificantTimeLost = 0;

    // Iterate through timeSlices to find the longest slice and most time-losing rank
    for (const slice_id in timeSlices) {
        const slice = timeSlices[slice_id];
        const sliceLength = slice.ts[1] - slice.ts[0];

        // Update longestSlice if the current slice is longer
        if (sliceLength > longestLength) {
            longestSlice = slice_id;
            longestLength = sliceLength;
        }

        // Determine the most time-losing slice
        const timeLostValue = parseFloat(slice.time_lost);
        if (Math.abs(timeLostValue) > maxTimeLost) {
            totalTimeLost += timeLostValue;
            maxTimeLost = Math.abs(timeLostValue);
            mostTimeLosingSlice = slice_id;
            timeLostByMostTimeLosingSlice = timeLostValue;
        }

        if (Number(slice.most_time_losing_rank) >= 0) {
            mostTimeLosingRank = slice.most_time_losing_rank;
            mostTimeLosingRankSlice = slice_id;
            if (slice.statistics.length > 0) {
                numRanksWithSignificantTimeLost += slice.statistics.length
                for (const rankTimeLost of slice.statistics) {
                    const rank = rankTimeLost["rank"];
                    if (rank == mostTimeLosingRank) {
                        timeLostByMostTimeLosingRank = rankTimeLost["time_lost"];
                    }
                }
            }
        }
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
                selectedKeys={["0"]}
                color={
                    numRanksWithSignificantTimeLost === 0
                    ? "success"
                    : numRanksWithSignificantTimeLost <= signficantThreshold
                    ? "warning"
                    : "danger"
                }
                aria-label="Analysis Summary"
            >
                <TableHeader>
                    <TableColumn>Description</TableColumn>
                    <TableColumn>Statistic</TableColumn>
                </TableHeader>
                <TableBody>
                    <TableRow key="0">
                        <TableCell># of Ranks with Signficant Time Lost</TableCell>
                        <TableCell>{numRanksWithSignificantTimeLost}</TableCell>
                    </TableRow>
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
                    <TableRow key="4">
                        <TableCell>{`% of Total Runtime Lost on Rank ${mostTimeLosingRank}`}</TableCell>
                        <TableCell>{formatPct(pctLostByMostTimeLosingRank)}%</TableCell>
                    </TableRow>
                    <TableRow key="5">
                        <TableCell>% of Total Runtime Lost Across All Ranks</TableCell>
                        <TableCell>{formatPct(pctLost)}%</TableCell>
                    </TableRow>
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
