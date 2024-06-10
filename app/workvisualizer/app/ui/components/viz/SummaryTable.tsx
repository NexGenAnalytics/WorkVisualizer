'use client'
import React from "react";
import {Table, TableHeader, TableColumn, TableBody, TableRow, TableCell, RadioGroup, Radio} from "@nextui-org/react";
import {Accordion, AccordionItem} from "@nextui-org/accordion";

export const dataRequirements = {
    endpoint: '/api/metadata', // API endpoint for this component's data
    params: {} // Additional parameters if needed
};

export default function SummaryTable({ data }) {
  const [selectedColor, setSelectedColor] = React.useState("default");

  // Define a function to format the begin, end, and duration times
  function formatTime(time) {
      if (time < 0.0001) {
          return time.toExponential(2);
      } else {
          return time.toFixed(4);
      }
  }

  const calculateAverage = (rankInfo) => {
    const ranks = Object.values(rankInfo);
    const totalDuration = ranks.reduce((acc, rank) => acc + rank.dur, 0);
    const totalCount = ranks.reduce((acc, rank) => acc + rank.count, 0);
    const averageDuration = totalDuration / ranks.length;
    const averageCount = totalCount / ranks.length;
    return { averageDuration, averageCount };
  };

  const callTypes = ["other", "collective", "mpi", "kokkos"];
  const callTypeLabels = {
    "other": "Program",
    "collective": "MPI Collective",
    "mpi": "MPI Point-To-Point",
    "kokkos": "Kokkos"
  };

  return (
    <div className="flex flex-col gap-3">

      <Accordion selectionMode="multiple">

        <AccordionItem key="1" aria-label="Program Information" title="Program Information">
          <Table
            hideHeader
            color={selectedColor}
            selectionMode="single"
            defaultSelectedKeys={[]}
            aria-label="Example static collection table"
          >
            <TableHeader>
              <TableColumn>PROGRAM INFORMATION</TableColumn>
              <TableColumn> </TableColumn>
            </TableHeader>
            <TableBody>
              <TableRow key="1">
                <TableCell>Comm Size</TableCell>
                <TableCell>{data["mpi.world.size"]}</TableCell>
              </TableRow>
              <TableRow key="2">
                <TableCell>Received Ranks</TableCell>
                <TableCell>{data["known.ranks"].join(", ")}</TableCell>
              </TableRow>
              <TableRow key="3">
                <TableCell>Program Runtime</TableCell>
                <TableCell>{formatTime(data["program.runtime"])} s</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </AccordionItem>

        <AccordionItem key="2" aria-label="Call Distribution" title="Call Distribution (averaged across ranks)">
          <Table
            color={selectedColor}
            selectionMode="single"
            defaultSelectedKeys={[]}
            aria-label="Example static collection table"
          >
            <TableHeader>
              <TableColumn>Call Type</TableColumn>
              <TableColumn>Total Counts</TableColumn>
              <TableColumn>Unique Counts</TableColumn>
            </TableHeader>
            <TableBody>
              {callTypes.map((type, index) => (
                <TableRow key={index}>
                  <TableCell>{callTypeLabels[type]}</TableCell>
                  <TableCell>{data["total.counts"]["average"][type]}</TableCell>
                  <TableCell>{data["unique.counts"]["average"][type]}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </AccordionItem>
        <AccordionItem key="3" aria-label="Largest calls" title="Largest Calls (averaged across ranks)">
          <Table
            color={selectedColor}
            selectionMode="single"
            defaultSelectedKeys={[]}
            aria-label="Example static collection table"
          >
            <TableHeader>
              <TableColumn>Function</TableColumn>
              <TableColumn>Time Spent</TableColumn>
              <TableColumn>Number of Instances</TableColumn>
            </TableHeader>
            <TableBody>
              {data["biggest.calls"].map((call, index) => {
                const { averageDuration, averageCount } = calculateAverage(call.rank_info);
                return (
                  <TableRow key={index}>
                    <TableCell>{call.name}</TableCell>
                    <TableCell>{formatTime(averageDuration)} s</TableCell>
                    <TableCell>{averageCount.toFixed(2)}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </AccordionItem>
      </Accordion>

    </div>
  );
}
