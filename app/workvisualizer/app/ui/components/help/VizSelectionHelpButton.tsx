import React from 'react';
import {Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure} from "@nextui-org/react";
import HelpIconButton from '@/app/ui/components/help/HelpButton';

export default function VizSelectionHelpButton() {
    const {isOpen, onOpen, onOpenChange} = useDisclosure();

    return (
        <div>
            <HelpIconButton onClick={onOpen} />
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
