import React from 'react';
import {Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure} from "@nextui-org/react";

export default function VizSelectionHelpButton() {
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
                    <ModalHeader className="flex flex-col gap-1">Select Visualization</ModalHeader>
                    <ModalBody>
                        <p>
                        <b>Events Plot</b>: View all function calls over the execution of the program.
                        </p>
                        <p>
                        <b>Proportion Analyzer</b>: View an aggregated sunburst diagram to see where the program spends its time.
                        </p>
                        <p>
                        <b>Analysis Viewer</b>: Once Analysis has been run (see Analysis tab for more information), view the calculated time lost for all slices and ranks.
                        </p>
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
