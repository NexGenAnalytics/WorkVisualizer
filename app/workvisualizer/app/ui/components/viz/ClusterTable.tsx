import React, { useState } from 'react';
import {
    Table,
    Dropdown,
    Button,
    Card,
    TableHeader,
    TableColumn,
    TableBody,
    TableCell,
    TableRow, DropdownMenu, DropdownItem
} from '@nextui-org/react';

interface ClusterTableProps {
    clusters: {
        [key: string]: string[];
    };
}

const ClusterTable: React.FC<ClusterTableProps> = ({ clusters }) => {
    const [selectedCluster, setSelectedCluster] = useState<string | null>(null);

    const handleClusterClick = (clusterId: string) => {
        setSelectedCluster(selectedCluster === clusterId ? null : clusterId); // Toggle dropdown
    };

    return (
        <Card css={{ padding: '20px' }}>
            <Table
                aria-label="Cluster Information"
                css={{
                    height: "auto",
                    minWidth: "100%",
                }}
            >
                <TableHeader>
                    <TableColumn>Cluster</TableColumn>
                    <TableColumn>Ranks</TableColumn>
                </TableHeader>
                <TableBody>
                    {Object.keys(clusters).map((clusterId) => (
                        <TableRow key={clusterId}>
                            <TableCell>{clusterId}</TableCell>
                            <TableCell>
                                {
                                    clusters[clusterId].length < 5 ?
                                    <p>{clusters[clusterId].join(', ')}</p> :
                                    <p>
                                        {clusters[clusterId].length} ranks
                                    </p>
                                }
                                {/* <Button
                                    auto
                                    light
                                    onClick={() => handleClusterClick(clusterId)}
                                >
                                    {clusters[clusterId].length}
                                </Button>
                                {selectedCluster === clusterId && (
                                    // <Dropdown>
                                    //     <DropdownMenu aria-label="Ranks in Cluster">
                                    //         {clusters[clusterId].map((rank, index) => (
                                    //             <DropdownItem key={index}>{rank}</DropdownItem>
                                    //         ))}
                                    //     </DropdownMenu>
                                    // </Dropdown>
                                )} */}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </Card>
    );
};

export default ClusterTable;
