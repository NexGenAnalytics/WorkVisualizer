'use client'
import React, { useEffect, useState } from 'react';
import { Dropdown, DropdownTrigger, DropdownMenu, DropdownItem, Button } from "@nextui-org/react";

export function ToolBar({ onPlotSelectionChange }) {
    const [plotComponents, setPlotComponents] = useState([]);
    const [selectedKeys, setSelectedKeys] = useState(new Set());

    useEffect(() => {
        async function fetchComponents() {
            const res = await fetch('http://127.0.0.1:8000/api/util/vizcomponents');
            const data = await res.json();
            console.log(data);
            if (data.components) {
                setPlotComponents(data.components.map(file => file.replace('.tsx', '')));
            }
        }
        fetchComponents();
    }, []);

    useEffect(() => {
        onPlotSelectionChange(selectedKeys);
    }, [selectedKeys, onPlotSelectionChange]);

    return (
        <div className='flex-col pt-2 pl-4 pr-4'>
            <Dropdown placement='right-start'>
                <DropdownTrigger>
                    <Button variant="bordered">Plots</Button>
                </DropdownTrigger>
                <DropdownMenu
                    aria-label="Dynamic plot selection"
                    variant="flat"
                    closeOnSelect={false}
                    disallowEmptySelection={false}
                    selectionMode="multiple"
                    selectedKeys={selectedKeys}
                    onSelectionChange={setSelectedKeys}
                >
                    {plotComponents.map((component) => (
                        <DropdownItem key={component}>{component}</DropdownItem>
                    ))}
                </DropdownMenu>
            </Dropdown>
        </div>
    );
}
