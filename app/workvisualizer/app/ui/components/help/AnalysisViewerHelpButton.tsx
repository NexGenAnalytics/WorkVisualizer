import React from 'react';
import {Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure} from "@nextui-org/react";

export default function AnalylsisViewerHelpButton() {
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
                    <ModalHeader className="flex flex-col gap-1">Analysis Viewer</ModalHeader>
                    <ModalBody>
                        <p>The Analysis Viewer visualizes the results of the analysis pipeline.</p>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>Slices</h3>
                        <p>The first plot shows the percentage of the total runtime that was lost in each slice.</p>
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
                        <i>Because "time lost" is relative to the representative rank, it is omitted from the Ranks plot.</i>
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
