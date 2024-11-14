import React from 'react';
import {Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure} from "@nextui-org/react";
import HelpIconButton from '@/app/ui/components/help/HelpButton';

export default function AnalysisResultsHelpButton() {
    const {isOpen, onOpen, onOpenChange} = useDisclosure();

    return (
        <div>
            <HelpIconButton onClick={onOpen} />
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
                        <p>Alternatively, if another rank is waiting for the representative rank to enter the collective call, that is reported as <b>negative</b> time lost, and still indicates imbalance in the application.</p>
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
