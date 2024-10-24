import React from 'react';
import {Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure} from "@nextui-org/react";

export default function EventsPlotHelpButton() {
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
                    <ModalHeader className="flex flex-col gap-1">Events Plot</ModalHeader>
                    <ModalBody>
                        <p>The Events Plot shows all of the functions called by the program, colored by type.</p>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>How to Use</h3>
                        <ul style={{ marginLeft: '1rem', listStyleType: 'disc' }}>
                            <li>Click and drag to zoom</li>
                            <li>Double click to return to the previous zoom</li>
                            <li>Triple click to return to the original view</li>
                            <li>Mouse over data points to reveal more information and highlight any parent calls</li>
                        </ul>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>Toggles</h3>
                        <ul style={{ marginLeft: '1rem', listStyleType: 'disc' }}>
                            <li><b>Call Type:</b> Check/Uncheck call types to show/hide them on the plot.</li>
                            <li><b>Show Duration:</b> Extend each event to reflect its duration.</li>
                            <li><b>Show Time Slices:</b> After running the analysis (see Analysis tab), delineates each time slice.</li>
                        </ul>
                        <p>Select the current rank, depth level, or slice from the Settings tab.</p>
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
