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
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i], files[i].name);
            }

            try {
                const response = await axios.post('http://127.0.0.1:8000/api/upload', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                });
                console.log('File uploaded successfully');
                setIsLoading(false);
                if (redirectOnSuccess) {
                    router.push(redirectOnSuccess);
                }
            } catch (error) {
                console.error('Error uploading file', error);
                setIsLoading(false);
            }
        }
    };

    return (
        <div className="flex flex-col items-center justify-center p-4">
            <input
                type="file" multiple
                ref={inputRef}
                onChange={handleFileChange}
                className="hidden"
                accept=".cali" // Specify file types
            />
            {isLoading ?
                <CircularProgress size="lg" aria-label="Loading..."/>
                :
                <Button
                    color="primary"
                    onClick={handleButtonClick}
                >
                    Upload File(s)
                </Button>
            }
        </div>
    );
};

export default FileUploadButton;
