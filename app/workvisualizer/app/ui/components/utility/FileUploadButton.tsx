'use client';
// FileUploadButton.tsx
import { Button } from '@nextui-org/react';
import { Progress } from "@nextui-org/progress";
import axios from 'axios';
import React, { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { CircularProgress } from '@nextui-org/react';

interface FileUploadButtonProps {
    redirectOnSuccess?: string;
}

const FileUploadButton: React.FC<FileUploadButtonProps> = ({ redirectOnSuccess }) => {
    const inputRef = useRef<HTMLInputElement>(null);
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);

    const handleButtonClick = () => {
        inputRef.current?.click();
    };

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        setIsLoading(true);
        const files = event.target.files;
        if (files && files.length > 0) {
            const formData = new FormData();

            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i], files[i].name);
            }

            setUploadProgress(0);
            setIsUploading(true); // Start upload

            try {
                const response = await axios.post('http://127.0.0.1:8000/api/upload', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                    onUploadProgress: (progressEvent) => {
                        const total = progressEvent.total || 0;
                        const current = progressEvent.loaded || 0;
                        const percentage = Math.floor((current / total) * 100);
                        setUploadProgress(percentage); // Update upload progress
                    },
                });
                console.log('Files uploaded successfully');
                setIsUploading(false);
                setIsLoading(false);
                if (redirectOnSuccess) {
                    router.push(redirectOnSuccess);
                }
            } catch (error) {
                console.error('Error uploading file', error);
                setIsUploading(false);
                setIsLoading(false);
            }
        }
    };

    return (
        <div className="flex flex-col items-center justify-center p-4">
            <input
                type="file"
                multiple
                ref={inputRef}
                onChange={handleFileChange}
                className="hidden"
                accept=".cali" // Specify file types
            />
            {(!isLoading && uploadProgress !== 100) && (
                <Button color="primary" onClick={handleButtonClick}>
                    Upload File(s)
                </Button>
            )}

            {(isUploading && uploadProgress !== 100) && (
                <Progress
                    label={"Uploading... (Step 1 of 2)"}
                    value={uploadProgress}
                    color={"primary"}
                    maxValue={100}
                    className="max-w-md mt-4"
                    style={{ width: '600px' }}
                />
            )}

            { (isLoading && uploadProgress == 100) ?
                (
                    <CircularProgress size="lg" label="Finishing up... (Step 2 of 2)" />
                )
                : null
            }
        </div>
    );
};

export default FileUploadButton;
