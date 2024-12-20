'use client';
// FileUploadButton.tsx
import { Button } from '@nextui-org/react';
import { Progress } from "@nextui-org/progress";
import axios from 'axios';
import React, { useRef, useState, useEffect } from 'react';
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
        const totalFiles = files ? files.length : 0;
        let filesUploaded = 0;

        if (files && totalFiles > 0) {
            setIsUploading(true);
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
                        onUploadProgress: (progressEvent) => {
                            const { loaded, total } = progressEvent;
                            const fileProgress = Math.round((loaded / total!) * 100);
                            const overallProgress = Math.round(((filesUploaded + fileProgress / 100) / totalFiles) * 100);
                            setUploadProgress(overallProgress);
                        },
                    }).then(() => {
                        filesUploaded += 1;
                    });
                });

                // Wait for all uploads to complete
                await Promise.all(uploadPromises);
                setUploadProgress(100);
                console.log('All files uploaded successfully');

                await axios.post('http://127.0.0.1:8000/api/unpack')

                if (redirectOnSuccess) {
                    router.push(redirectOnSuccess);
                }

            } catch (error) {
                console.error('Error uploading files', error);
                setIsUploading(false);
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
                accept=".cali" // Specify the accepted file types
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