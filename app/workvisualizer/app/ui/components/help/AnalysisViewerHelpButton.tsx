import React from 'react';
import {Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure} from "@nextui-org/react";
import HelpIconButton from '@/app/ui/components/help/HelpButton';

export default function AnalylsisViewerHelpButton() {
    const {isOpen, onOpen, onOpenChange} = useDisclosure();

    return (
        <div>
            <HelpIconButton onClick={onOpen} />
            <Modal backdrop={"blur"} isOpen={isOpen} onOpenChange={onOpenChange} scrollBehavior={"inside"}>
                <ModalContent>
                {(onClose) => (
                    <>
                    <ModalHeader className="flex flex-col gap-1">Analysis Viewer</ModalHeader>
                    <ModalBody>
                        <p>The Analysis Viewer visualizes the results of the analysis pipeline.</p>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>Slices</h3>
                        <p>The first plot shows the time lost per slice averaged across all ranks.</p>
                        <img src="/time_lost_explainer.png" alt="Analysis Visualization" style={{ maxWidth: '100%', height: 'auto' }} />
                        <p>As seen above, if the representative rank is waiting for another rank to enter a collective call, that is time being lost. This is shown in blue on the plot.</p>
                        <p>If the inverse is true, and the rank in question is waiting on the representative rank, that is <b>negative</b> time lost, represented with green on the plot.</p>
                        <p><i>Note that the plot shows the absolute value of the average time lost per slice.</i></p>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>Ranks</h3>
                        <p>The second plot shows the percentage of the total runtime that was lost on the top ten time-losing ranks.</p>
                        <ul style={{ marginLeft: '1rem', listStyleType: 'disc' }}>
                            <li>By default, percentages are aggregated for each rank across all slices.</li>
                            <li>To view the percentage on a per-slice basis, click "Show Time Lost Per Slice"</li>
                            <ul style={{ marginLeft: '1rem', listStyleType: 'circle' }}>
                                <li>Click and drag the slider to select different slices.</li>
                                <li>The most time-losing slice is denoted on the slider with "!"</li>
                            </ul>
                        </ul>
                        <p><i>Note: In the event of many slices, these plots only show the 50 most time-losing slices.</i></p>
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
