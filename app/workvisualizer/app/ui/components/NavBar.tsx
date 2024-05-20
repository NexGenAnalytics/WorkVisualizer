'use client'
import React from "react";
import {Navbar, NavbarBrand, NavbarContent, NavbarItem, NavbarMenuToggle, NavbarMenu, NavbarMenuItem, Link, Button, Spacer} from "@nextui-org/react";
import Logo from './styling/Logo'
import DarkModeToggle from '@/app/ui/components/utility/DarkModeToggle'

export default function NavBar() {
    const [isMenuOpen, setIsMenuOpen] = React.useState(false);

    const menuItems = [
        "Dashboard",
        "Settings",
        "Help & Feedback",
        "Log Out",
    ];

    return (
        <Navbar
            isBordered
            isMenuOpen={isMenuOpen}
            onMenuOpenChange={setIsMenuOpen}
            // className="background"
        >
            <NavbarContent className="flex-grow justify-start">
                <NavbarMenuToggle
                    aria-label={isMenuOpen ? "Close menu" : "Open menu"}
                    // className="sm:hidden"
                />
                <NavbarBrand>
                    <Logo />
                    <Spacer x={4} />
                    <p className="font-bold text-3xl">WorkVisualizer</p>
                </NavbarBrand>
            </NavbarContent>
            <NavbarContent justify="end">
                <DarkModeToggle></DarkModeToggle>
            </NavbarContent>
            <NavbarMenu>
                {menuItems.map((item, index) => (
                    <NavbarMenuItem key={`${item}-${index}`}>
                        <Link
                            color={
                                index === 2 ? "primary" : index === menuItems.length - 1 ? "danger" : "foreground"
                            }
                            className="w-full"
                            href={index === 0 ? "/dashboard" : "#"}
                            size="lg"
                        >
                            {item}
                        </Link>
                    </NavbarMenuItem>
                ))}
            </NavbarMenu>
        </Navbar>
    );
}
