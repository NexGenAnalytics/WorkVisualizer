// FileUploadButton.tsx
import { Button } from '@nextui-org/react';
import axios from 'axios';
import { useRef } from 'react';
import { useRouter } from 'next/navigation';

interface FileUploadButtonProps {
    redirectOnSuccess?: string;
}

const FileUploadButton: React.FC<FileUploadButtonProps> = ({ redirectOnSuccess }) => {
    const inputRef = useRef<HTMLInputElement>(null);
    const router = useRouter();

    const handleButtonClick = () => {
        inputRef.current?.click();
    };

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files ? event.target.files[0] : null;
        if (file) {
            const formData = new FormData();
            formData.append('file', file, file.name);

            try {
                const response = await axios.post('http://127.0.0.1:8000/api/upload', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                });
                console.log('File uploaded successfully', response.data);
                if (redirectOnSuccess) {
                    router.push(redirectOnSuccess);
                }
            } catch (error) {
                console.error('Error uploading file', error);
            }
        }
    };

    return (
        <div className="flex flex-col items-center justify-center p-4">
            <input
                type="file"
                ref={inputRef}
                onChange={handleFileChange}
                className="hidden"
                accept=".json" // Specify file types
            />
            <Button
                color="primary"
                onClick={handleButtonClick}
            >
                Upload File
            </Button>
        </div>
    );
};

export default FileUploadButton;
