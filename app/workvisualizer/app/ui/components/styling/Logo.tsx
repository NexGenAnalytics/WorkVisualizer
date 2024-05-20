import Image from 'next/image';
import ngaDark from "../../../../public/nga-dark.svg";
import ngaLight from "../../../../public/nga-light.svg";
import {useTheme} from "next-themes";


const Logo = () => {
    const {theme, setTheme} = useTheme()

    return (
        <div>
            <Image
                priority
                src={theme === 'dark' ? ngaDark : ngaLight}
                alt="NGA"
                height={100}
                className="hidden md:block"
            />
        </div>
    )
};

export default Logo;
