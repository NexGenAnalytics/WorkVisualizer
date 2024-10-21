'use client'
// FileUploadButton.tsx
import { Button } from '@nextui-org/react';
import axios from 'axios';
import React, {useRef, useState} from 'react';
import { useRouter } from 'next/navigation';
import { CircularProgress } from '@nextui-org/react';

interface FileUploadButtonProps {
    redirectOnSuccess?: string;
}

const FileUploadButton: React.FC<FileUploadButtonProps> = ({ redirectOnSuccess }) => {
    const inputRef = useRef<HTMLInputElement>(null);
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);

    const handleButtonClick = () => {
        inputRef.current?.click();
    };

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        setIsLoading(true);
        const files = event.target.files;

        if (files && files.length > 0) {
            try {
                await axios.post('http://127.0.0.1:8000/api/clear');
                // Create an array of promises for parallel upload
                const uploadPromises = Array.from(files).map((file) => {
                    const formData = new FormData();
                    formData.append('files', file, file.name);

                    // Send each file via axios in parallel
                    return axios.post('http://127.0.0.1:8000/api/upload', formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data',
                        },
                    });
                });

                // Wait for all uploads to complete
                await Promise.all(uploadPromises);

                console.log('All files uploaded successfully');

                if (redirectOnSuccess) {
                    router.push(redirectOnSuccess);
                }
            } catch (error) {
                console.error('Error uploading files', error);
            }
        }
        setIsLoading(false);
    };

    return (
        <div className="flex flex-col items-center justify-center p-4">
            <input
                type="file"
                multiple
                ref={inputRef}
                onChange={handleFileChange}
                className="hidden"
                accept=".cali" // Specify the accepted file types
            />
            {isLoading ? (
                <CircularProgress size="lg" aria-label="Loading..." />
            ) : (
                <Button
                    color="primary"
                    onClick={handleButtonClick}
                >
                    Upload File(s)
                </Button>
            )}
        </div>
    );
};

export default FileUploadButton;