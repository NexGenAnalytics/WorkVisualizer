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

  // Define a function to format the imbalance metric
  function formatImbalance(imbalance) {
    if (imbalance < 0.01) {
        return imbalance.toExponential(2);
    } else {
        return imbalance.toFixed(2);
    }
  }

  const sortedImbalance = data["imbalance"] && data["imbalance"].length > 0
    ? [...data["imbalance"]].sort((a, b) => b.imbalance - a.imbalance)
    : [];

  const calculateAverage = (rankInfo) => {
    const ranks = Object.values(rankInfo);
    const totalDuration = ranks.reduce((acc, rank) => acc + rank.dur, 0);
    const totalCount = ranks.reduce((acc, rank) => acc + rank.count, 0);
    const averageDuration = totalDuration / ranks.length;
    const averageCount = totalCount / ranks.length;
    return { averageDuration, averageCount };
  };

  const callTypes = ["other", "mpi_collective", "mpi_p2p", "kokkos"];
  const callTypeLabels = {
    "other": "Program",
    "mpi_collective": "MPI Collective",
    "mpi_p2p": "MPI Point-To-Point",
    "kokkos": "Kokkos"
  };

  return (
    <div className="flex flex-col gap-3">

      <Accordion selectionMode="multiple" defaultExpandedKeys={["1"]}>

        <AccordionItem key="1" aria-label="Program Information" title="Program Information">
          <Table
            hideHeader
            removeWrapper
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
                <TableCell>Program Runtime</TableCell>
                <TableCell>{formatTime(data["program.runtime"])} s</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </AccordionItem>

        <AccordionItem key="2" aria-label="Call Distribution" title="Call Distribution">
          <Table
            removeWrapper
            color={selectedColor}
            selectionMode="single"
            defaultSelectedKeys={[]}
            aria-label="Example static collection table"
          >
            <TableHeader>
              <TableColumn>Call Type</TableColumn>
              <TableColumn>Average Counts per Rank</TableColumn>
              <TableColumn>Unique Counts</TableColumn>
            </TableHeader>
            <TableBody>
              {callTypes.map((type, index) => (
                <TableRow key={index}>
                  <TableCell>{callTypeLabels[type]}</TableCell>
                  <TableCell>{data["average.counts"][type].toFixed(0)}</TableCell>
                  <TableCell>{data["unique.counts"][type]}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </AccordionItem>
        {/* <AccordionItem key="3" aria-label="Imbalanced calls" title="Imbalanced Calls">
          {data["imbalance"] && data["imbalance"].length > 0 ? (
            <Table
              removeWrapper
              color={selectedColor}
              selectionMode="single"
              defaultSelectedKeys={[]}
              aria-label="Example static collection table"
            >
              <TableHeader>
                <TableColumn>Function</TableColumn>
                <TableColumn>Imbalance</TableColumn>
              </TableHeader>
              <TableBody>
                {sortedImbalance.map((call, index) => {
                  return (
                    <TableRow key={index}>
                      <TableCell>{call.name}</TableCell>
                      <TableCell>{formatImbalance(call.imbalance * 100)}%</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <p>No imbalance was found.</p>
          )}
        </AccordionItem> */}
        <AccordionItem key="4" aria-label="Largest calls" title="Largest Calls">
          <Table
            removeWrapper
            color={selectedColor}
            selectionMode="single"
            defaultSelectedKeys={[]}
            aria-label="Example static collection table"
          >
            <TableHeader>
              <TableColumn>Function</TableColumn>
              <TableColumn>Average Time</TableColumn>
            </TableHeader>
            <TableBody>
              {Object.entries(data["biggest.calls"]).map(([callName, duration], index) => (
                <TableRow key={index}>
                  <TableCell>{callName}</TableCell>
                  <TableCell>{duration.toFixed(6)} s</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </AccordionItem>
      </Accordion>

    </div>
  );
}
