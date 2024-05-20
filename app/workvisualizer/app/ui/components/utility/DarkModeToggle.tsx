import { useTheme } from "next-themes";
import { useState, useEffect } from "react";
import {Switch} from '@nextui-org/react'

// const DarkModeToggle = () => {
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
    const [mounted, setMounted] = useState(false)
    const { theme, setTheme } = useTheme()

    // useEffect only runs on the client, so now we can safely show the UI
    useEffect(() => {
      setMounted(true)
    }, [])

    if (!mounted) {
      return null
    }

    const handleThemeChange = (checked: any) => {
      console.log("DarkModeToggle checked: ", checked)
      setTheme(checked ? "dark" : "light");
    }

    return (
      <div>
        {/*The current theme is: {theme}*/}
        <Switch
            defaultSelected={theme === 'dark'}
            onValueChange={handleThemeChange}
        />
      </div>
    )
};

export default DarkModeToggle;
