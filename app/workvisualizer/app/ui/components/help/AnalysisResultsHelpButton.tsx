import React from 'react';
import {Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure} from "@nextui-org/react";

export default function AnalysisResultsHelpButton() {
    const {isOpen, onOpen, onOpenChange} = useDisclosure();

    return (
        <div>
            <div onClick={onOpen} style={{
                width: '25px',
                height: '25px',
                borderRadius: '50%',
                backgroundColor: '#495057',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                color: 'white',
                fontSize: '15px',
                border: 'none',
                transition: 'background-color 0.2s',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#343a40'; }}
            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#495057'; }}
            >
                ?
            </div>
            <Modal backdrop={"blur"} isOpen={isOpen} onOpenChange={onOpenChange}>
                <ModalContent>
                {(onClose) => (
                    <>
                    <ModalHeader className="flex flex-col gap-1">WorkVisualizer Analysis</ModalHeader>
                    <ModalBody>
                        <p>
                        Our analysis is based on "time lost."
                        </p>
                        <p>
                        First, we determine a "representative rank" that exhibits common behavior among all of the ranks.
                        </p>
                        <p>
                        Then, we compare all other ranks to this representative rank in order to determine where time is being lost.
                        </p>
                        <p>
                        Specifically, we look at the amount of time spent in MPI Collective calls (e.g. MPI_Allreduce).
                        </p>
                        <img src="/time_lost_explainer.png" alt="Analysis Visualization" style={{ maxWidth: '100%', height: 'auto' }} />
                        <p>As seen above, if the representative rank is waiting for another rank to enter a collective call, that is time being lost.</p>
                    </ModalBody>
                    <ModalFooter>
                        <Button color="danger" variant="light" onPress={onClose}>
                        Close
                        </Button>
                    </ModalFooter>
                    </>
                )}
                </ModalContent>
            </Modal>
        </div>
    );
};
