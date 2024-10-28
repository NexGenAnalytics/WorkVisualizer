import React from 'react';
import {Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure} from "@nextui-org/react";
import HelpIconButton from '@/app/ui/components/help/HelpButton';

export default function ProportionAnalyzerHelpButton() {
    const {isOpen, onOpen, onOpenChange} = useDisclosure();

    return (
        <div>
            <HelpIconButton onClick={onOpen} />
            <Modal backdrop={"blur"} isOpen={isOpen} onOpenChange={onOpenChange}>
                <ModalContent>
                {(onClose) => (
                    <>
                    <ModalHeader className="flex flex-col gap-1">Proportion Analyzer</ModalHeader>
                    <ModalBody>
                        <p>The Proportion Analyzer compares the total time spent in each function.</p>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>How to Use</h3>
                        <ul style={{ marginLeft: '1rem', listStyleType: 'disc' }}>
                            <li>Mouse over regions to see more information about the call</li>
                            <li>Click on a parent region to view all children of that call</li>
                            <li>Click in the center of the diagram to return to the previous level of the hierarchy</li>
                        </ul>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>Toggles</h3>
                        <ul style={{ marginLeft: '1rem', listStyleType: 'disc' }}>
                            <li><b>Call Type:</b> Check/Uncheck call types to show/hide them on the plot.</li>
                        </ul>
                        <p>Select the current rank or depth level from the Settings tab.</p>
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
