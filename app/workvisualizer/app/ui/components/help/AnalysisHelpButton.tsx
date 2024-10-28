import React from 'react';
import {Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, useDisclosure} from "@nextui-org/react";
import HelpIconButton from '@/app/ui/components/help/HelpButton';

// Rename the interface to avoid name conflict
interface AnalysisHelpButtonProps {
    fromAnalysisTab: boolean;
}

export default function AnalysisHelpButton({ fromAnalysisTab }: AnalysisHelpButtonProps) {
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
                        Our analysis is a two-step process.
                        </p>
                        <p>
                        First, we determine a "representative rank" that exhibits common behavior among all of the ranks.
                        After analysis has run, you can select this rank from the Settings tab.
                        </p>
                        <p>
                        Once we have determined the representative rank, we implement time slicing.
                        This divides the program's execution into segments based on repetitive function calls.
                        Slices can be viewed on the Events Plot with the "Show Time Slices" toggle.
                        </p>
                        <p>
                        Finding time slices allows us to identify ranks that execute the same slice slower or faster than the representative rank.
                        In doing so, we can identify where time is being lost in the application's runtime.
                        </p>
                        {fromAnalysisTab && (
                            <p>Analysis can be run from the Analysis tab.</p>
                        )}
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
