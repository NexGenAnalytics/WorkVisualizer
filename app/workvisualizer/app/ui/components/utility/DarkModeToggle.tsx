'use client';

import {useTheme} from "next-themes";
import {Switch} from '@nextui-org/react'
import { useEffect, useState } from "react";

// export function ThemeSwitcher() {
//     const [mounted, setMounted] = useState(false)
//     const { theme, setTheme } = useTheme()
//
//     useEffect(() => {
//         setMounted(true)
//     }, [])
//
//     if(!mounted) return null
//
//     return (
//         <div>
//             The current theme is: {theme}
//             <button onClick={() => setTheme('light')}>Light Mode</button>
//             <button onClick={() => setTheme('dark')}>Dark Mode</button>
//         </div>
//     )
// };

const DarkModeToggle = () => {
    const { setTheme } = useTheme();

    return (
        <Switch
            checked={false}
            onChange={(e) => setTheme(e.target.checked ? 'dark' : 'light')}
            color="primary"
        />
    );
};

export default DarkModeToggle;
