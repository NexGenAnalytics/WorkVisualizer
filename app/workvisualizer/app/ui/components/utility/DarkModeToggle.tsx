import { useTheme } from "next-themes";
import { useState, useEffect } from "react";
import {Switch} from '@nextui-org/react'

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
        <Switch
            defaultSelected={theme === 'dark'}
            onValueChange={handleThemeChange}
        />
      </div>
    )
};

export default DarkModeToggle;
